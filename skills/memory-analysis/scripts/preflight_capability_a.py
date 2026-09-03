"""MANDATORY preflight gate for capability A (staged startup memory analysis).

Capability A MUST NOT proceed to injection/launch until this preflight passes.
It enforces three constraints, in order:

  1. Hook-point validation (打桩点校验): parse the target fork's
     model_runner.py and require every canonical startup stage to resolve to a
     present method (inject_hooks.validate_hooks). Any MISS fails the gate
     (exit 2) unless --allow-partial is given, because a missed stage silently
     drops from the report. Fine-grained extras (deepep / cuda-graph trace) are
     also checked (NATIVE vs WRAP) for information.

  2. Weight-adapter skeleton check (权重适配器骨架): resolve the running model
     from the deploy yaml's --model-path, match it against the registered
     model_adapters. If no adapter matches, AUTO-GENERATE a skeleton via
     derive_adapter (scans the fork's stacked_params_mapping) and write it to
     model_adapters/<name>.py. Generation failure is a WARN (capability A can
     run on the base adapter) but is always reported.

  3. Trace switches (trace 开关): emit the FULL set of memory-trace env vars
     that the launch must carry -- SGLANG_TRACK_GPU_MEMORY=1,
     SGLANG_CAPTURE_MEM_LEDGER=1, SGLANG_CAPTURE_MEM_SNAPSHOT_DIR=<dir>.
     run_and_collect.launch_sglang() now defaults these ON; this step prints
     the exact env string (and writes it to --env-out if given) so manual
     launches use the same set.

Usage:
  python3 preflight_capability_a.py --yaml deploy.yaml --sglang-src <tree> \
      [--model-runner <model_runner.py>] [--snapshot-dir /tmp/capsnap] \
      [--env-out <file>] [--allow-partial]

Exit codes: 0 = all gates passed; 2 = hook validation failed (do not proceed).
"""

import argparse
import glob as _glob
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, _ROOT)  # for `model_adapters` package

from inject_hooks import validate_hooks, print_validation, validate_extras


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def find_model_runner(sglang_src: str):
    hits = _glob.glob(os.path.join(sglang_src, "**", "model_runner.py"),
                      recursive=True)
    # prefer the model_executor one when several files match
    hits.sort(key=lambda p: ("model_executor" not in p, len(p)))
    return hits[0] if hits else None


def model_hint_from_yaml(yaml_path: str):
    """Model identity = basename of --model-path in the launch command."""
    from analyze_startup_stages import extract_launch, parse_arg
    raw = extract_launch(yaml_path)["raw"]
    if not raw:
        return None, None
    mp = parse_arg(raw, "model-path") or parse_arg(raw, "model")
    if not mp:
        return None, raw
    return os.path.basename(mp.rstrip("/")), raw


def gate1_hooks(model_runner_path: str, sglang_src: str, allow_partial: bool):
    print("== Gate 1/3: hook-point validation (打桩点 + 权重 dump 校验) ==")
    rep = validate_hooks(model_runner_path)
    print(print_validation(rep))
    try:
        print(validate_extras(sglang_src))
    except Exception as e:
        print(f"[warn] extras validation skipped: {e}")
    if rep["missing"] and not allow_partial:
        print("[FAIL] stage(s) unresolved -- extend STAGE_SPEC candidates in "
              "inject_hooks.py (or rerun with --allow-partial to accept the "
              "coverage loss). Capability A must not proceed.")
        return False
    # dump_param_memory_stats constraint: the load stage (dump_after=True) must
    # resolve AND the asset staged into the pod must define the function --
    # otherwise capability A produces no weight dump and the auto capability-B
    # chain (auto_weight_diff.py) has nothing to diff.
    dump_stage_ok = any(st.get("dump_after") for st, _hit in rep["resolved"])
    asset = os.path.join(_ROOT, "assets", "param_memory_dump.py")
    try:
        with open(asset) as f:
            asset_ok = "def dump_param_memory_stats" in f.read()
    except OSError:
        asset_ok = False
    print(f"  [{'OK' if dump_stage_ok else 'MISS'}]{'  ' if dump_stage_ok else ''} "
          f"dump_param_memory_stats fires after the load stage "
          f"(inject block calls it when the dump_after stage resolves)")
    print(f"  [{'OK' if asset_ok else 'MISS'}]{'  ' if asset_ok else ''} "
          f"asset assets/param_memory_dump.py defines dump_param_memory_stats")
    if not (dump_stage_ok and asset_ok):
        print("[FAIL] weight-dump hook incomplete -- capability A would produce "
              "no *param_memory_stats* file, breaking the mandatory "
              "capability-B auto chain. Fix before proceeding.")
        return False
    print("[PASS] hook points + weight-dump hook validated.")
    return True


def gate2_adapter(model_hint, sglang_src: str):
    print("\n== Gate 2/3: weight-adapter skeleton (权重适配器骨架) ==")
    if not model_hint:
        print("[warn] could not resolve --model-path from yaml; adapter check "
              "skipped -- pass the model name manually via derive_adapter.py.")
        return None
    import model_adapters  # registers bundled adapters
    from model_adapters.base import _REGISTRY
    hint = _norm(model_hint)
    for name in _REGISTRY:
        n = _norm(name)
        if n == hint or n in hint or hint in n:
            print(f"[PASS] model '{model_hint}' -> existing adapter '{name}'.")
            return name
    # auto-generate a skeleton
    name = hint or "auto"
    out = os.path.join(_ROOT, "model_adapters", f"{name}.py")
    print(f"[info] no adapter matches '{model_hint}' -> auto-generating "
          f"skeleton '{name}' from stacked_params_mapping...")
    try:
        from derive_adapter import derive
        text = derive(sglang_src, model_hint, name)
        with open(out, "w") as f:
            f.write(text)
        with open(os.path.join(_ROOT, "model_adapters", "__init__.py"), "a") as f:
            f.write(f"from . import {name}  # noqa: F401,E402  (auto-registered)\n")
        print(f"[PASS] skeleton written: {out} (refine `tp` per category "
              f"against config/source before trusting the diff).")
        return name
    except SystemExit as e:
        print(f"[warn] skeleton generation failed: {e}. Capability A continues "
              f"on the base heuristic adapter; generate manually later with "
              f"derive_adapter.py.")
        return None


def gate3_env(snapshot_dir: str, env_out):
    print("\n== Gate 3/3: memory-trace switches (全量 trace 开关) ==")
    env = ("SGLANG_TRACK_GPU_MEMORY=1 SGLANG_CAPTURE_MEM_LEDGER=1 "
           f"SGLANG_CAPTURE_MEM_SNAPSHOT_DIR={snapshot_dir}")
    print(f"[PASS] launch MUST carry: {env}")
    print(f"       (launch_sglang() defaults these ON; remember to "
          f"`mkdir -p {snapshot_dir}` in the pod -- launch_sglang does it.)")
    if env_out:
        with open(env_out, "w") as f:
            f.write(env + "\n")
        print(f"[written] {env_out}")
    return env


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--yaml", required=True, help="deploy yaml")
    ap.add_argument("--sglang-src", required=True, help="sglang source tree "
                    "(local copy of the pod's tree)")
    ap.add_argument("--model-runner", default=None,
                    help="model_runner.py path (default: auto-locate in src)")
    ap.add_argument("--snapshot-dir", default="/tmp/capsnap")
    ap.add_argument("--env-out", default=None,
                    help="write the required env string to this file")
    ap.add_argument("--allow-partial", action="store_true",
                    help="accept MISSing stages (coverage loss) -- discouraged")
    args = ap.parse_args(argv)

    mr = args.model_runner or find_model_runner(args.sglang_src)
    if not mr:
        print(f"[FAIL] no model_runner.py under {args.sglang_src}")
        return 2
    print(f"[preflight] model_runner: {mr}")
    model_hint, raw = model_hint_from_yaml(args.yaml)
    if raw:
        print(f"[preflight] launch: {raw[:160]}{'...' if len(raw) > 160 else ''}")
    print(f"[preflight] model: {model_hint or '(unresolved)'}\n")

    if not gate1_hooks(mr, args.sglang_src, args.allow_partial):
        return 2
    gate2_adapter(model_hint, args.sglang_src)
    gate3_env(args.snapshot_dir, args.env_out)
    print("\n[preflight] ALL GATES DONE -- capability A may proceed "
          "(inject -> deploy -> launch -> collect -> report), and MUST finish "
          "with the capability-B auto chain: "
          "`python3 scripts/auto_weight_diff.py <out_dir> --yaml <deploy.yaml>` "
          "(diffs the collected *param_memory_stats* dump against HF theory).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
