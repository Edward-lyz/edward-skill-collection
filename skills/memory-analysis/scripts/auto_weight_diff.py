"""Capability-A epilogue: auto-run capability B from the collected weight dump.

Capability A (staged startup memory analysis) MUST end with this step: after
`run_and_collect.collect_logs()` has pulled the `*param_memory_stats*` dump(s)
back into <out_dir>, this script chains straight into capability B
(`analyze-weights`) -- HF theoretical weight sizes diffed against the runtime
dump -- with everything resolved automatically:

  - dump file : newest/largest `*param_memory_stats*` in <out_dir>, preferring
    gpu0 and the LARGEST file (the target model; the draft model's dump is
    reported but skipped -- its theory belongs to a different checkpoint).
  - HF source : the yaml's --model-path is a POD-INTERNAL path. Resolution
    order: (1) explicit --hf; (2) the same path exists locally (shared mount);
    (3) with --pod given, a header-only local mirror is pulled from the pod
    (index/config json + the first 8+header_len bytes of each shard -- a few
    MB total, never the weight bodies); else fail with exit 2.
  - parallel  : tp/ep/dcp/dp parsed from the yaml (same anti-circularity rule
    as capability B: degrees never come from the dump).
  - adapter   : --model if given, else fuzzy-matched from the model name
    against model_adapters/ (the preflight gate auto-generates a skeleton, so
    by this point a match normally exists).

Usage:
  python3 auto_weight_diff.py <out_dir> --yaml deploy.yaml \
      [--hf <repo|local_dir>] [--pod <pod> [--ns default] [--kubeconfig ...]] \
      [--model <adapter>] [--sglang-src <tree>] \
      [--out <report_dir, default <out_dir>/weight_diff>]

Exit codes: 0 ok; 2 no dump found / no HF source resolvable (capability A is
considered INCOMPLETE in that case -- check the dump hook or pass --hf).
"""

import argparse
import glob
import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, _ROOT)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def pick_dump(out_dir: str):
    """Prefer gpu0; among those take the largest file = the target model
    (draft/speculative dumps are much smaller). Returns (chosen, skipped)."""
    cands = glob.glob(os.path.join(out_dir, "*param_memory_stats*"))
    if not cands:
        return None, []
    gpu0 = [c for c in cands if "gpu0" in os.path.basename(c)] or cands
    chosen = max(gpu0, key=os.path.getsize)
    return chosen, [c for c in cands if c != chosen]


def mirror_headers_from_pod(pod, remote_dir, local_dir, ns="default",
                            kubeconfig=None):
    """Build a header-only local mirror of a pod-internal model dir: copies
    *.json (index/config) and, for every *.safetensors shard, only the first
    8+header_len bytes (the theory loader reads just the header). Never touches
    weight bodies, so the copy stays a few MB even for TB checkpoints."""
    import tempfile
    from deploy_and_patch import cp_into_pod, exec_in_pod, _run
    os.makedirs(local_dir, exist_ok=True)
    stage = f"/tmp/model_hdr_mirror_{os.getpid()}"
    helper = (
        "import os, shutil, struct, sys\n"
        "src, dst = sys.argv[1], sys.argv[2]\n"
        "os.makedirs(dst, exist_ok=True)\n"
        "for n in os.listdir(src):\n"
        "    sp = os.path.join(src, n)\n"
        "    if n.endswith('.json'):\n"
        "        shutil.copyfile(sp, os.path.join(dst, n))\n"
        "    elif n.endswith('.safetensors'):\n"
        "        with open(sp, 'rb') as f:\n"
        "            hl = struct.unpack('<Q', f.read(8))[0]\n"
        "            f.seek(0)\n"
        "            data = f.read(8 + hl)\n"
        "        with open(os.path.join(dst, n), 'wb') as g:\n"
        "            g.write(data)\n"
        "print(len(os.listdir(dst)), 'files mirrored')\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
        tf.write(helper)
        local_helper = tf.name
    remote_helper = f"{stage}_helper.py"
    cp_into_pod(pod, local_helper, remote_helper, ns=ns, kubeconfig=kubeconfig)
    os.unlink(local_helper)
    exec_in_pod(pod, f"python3 {remote_helper} {remote_dir} {stage}",
                ns=ns, kubeconfig=kubeconfig)
    listing = exec_in_pod(pod, f"ls {stage}", ns=ns, kubeconfig=kubeconfig)
    for name in listing.split():
        _run(["cp", f"{ns}/{pod}:{stage}/{name}",
              os.path.join(local_dir, name)], kubeconfig)
    exec_in_pod(pod, f"rm -rf {stage} {remote_helper}", ns=ns,
                kubeconfig=kubeconfig, check=False)
    print(f"[auto-B] header-only mirror: {local_dir} "
          f"({len(listing.split())} files)")
    return local_dir


def resolve_adapter(model_hint):
    if not model_hint:
        return None
    import model_adapters  # noqa: F401  (registers bundled + generated)
    from model_adapters.base import _REGISTRY
    hint = _norm(model_hint)
    for name in _REGISTRY:
        n = _norm(name)
        if n == hint or n in hint or hint in n:
            return name
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("out_dir", help="capability-A collect_logs output dir")
    ap.add_argument("--yaml", required=True, help="deploy yaml (parallel degrees"
                    " + model path)")
    ap.add_argument("--hf", default=None, help="HF repo/dir override; the "
                    "yaml --model-path is a POD path and is only used when the "
                    "same dir exists locally (shared mount)")
    ap.add_argument("--pod", default=None, help="pod name: pull a header-only "
                    "model mirror from the pod when no local HF source resolves")
    ap.add_argument("--ns", default="default")
    ap.add_argument("--kubeconfig", default=None)
    ap.add_argument("--model", default=None, help="adapter override")
    ap.add_argument("--sglang-src", default=None)
    ap.add_argument("--out", default=None, help="report dir "
                    "(default <out_dir>/weight_diff)")
    args = ap.parse_args(argv)

    dump, skipped = pick_dump(args.out_dir)
    if not dump:
        print(f"[FAIL] no *param_memory_stats* dump under {args.out_dir} -- "
              f"capability A is incomplete (dump hook did not fire or "
              f"collect_logs missed it).")
        return 2
    print(f"[auto-B] dump: {dump}")
    for s in skipped:
        print(f"[auto-B] skipped dump (draft/other rank): {s}")

    from analyze_startup_stages import extract_launch, parse_arg
    raw = extract_launch(args.yaml)["raw"]
    # NOTE: --model-path in the yaml is the POD-INTERNAL path.
    mp = parse_arg(raw, "model-path") or parse_arg(raw, "model")
    hf = args.hf
    if not hf and mp and os.path.isdir(mp):
        hf = mp
        print(f"[auto-B] pod model path {mp} also exists locally "
              f"(shared mount) -> using it as the HF source")
    if not hf and mp and args.pod:
        try:
            hf = mirror_headers_from_pod(
                args.pod, mp, os.path.join(args.out_dir, "model_hdr_mirror"),
                ns=args.ns, kubeconfig=args.kubeconfig)
        except Exception as e:
            print(f"[warn] header mirror from pod failed: {e}")
    if not hf:
        print(f"[FAIL] cannot resolve an HF source: yaml --model-path "
              f"({mp!r}) is a POD path and no local copy/mirror is available; "
              f"rerun with --hf <repo|dir> or --pod <pod> to pull a "
              f"header-only mirror.")
        return 2
    model_hint = os.path.basename(mp.rstrip("/")) if mp else None
    adapter = args.model or resolve_adapter(model_hint)
    print(f"[auto-B] hf={hf} adapter={adapter or '(base heuristic)'} "
          f"model={model_hint}")

    out = args.out or os.path.join(args.out_dir, "weight_diff")
    cmd = [sys.executable, os.path.join(_ROOT, "bin", "mem-analysis"),
           "analyze-weights", "--hf", hf, "--stats-file", dump,
           "--yaml", args.yaml, "--out", out]
    if adapter:
        cmd += ["--model", adapter]
    if args.sglang_src:
        cmd += ["--sglang-src", args.sglang_src]
    print(f"[auto-B] exec: {' '.join(cmd)}")
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
