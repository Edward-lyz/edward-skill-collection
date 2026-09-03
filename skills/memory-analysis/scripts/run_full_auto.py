"""Full-auto orchestrator: capability A end-to-end + capability-B epilogue,
WITH self-healing -- on failure it diagnoses the cause, applies a known fix,
and re-runs the flow (bounded by --max-retries), instead of stopping at the
first error.

Pipeline (one command runs everything):
  preflight gate -> ensure sleep pod (auto apply + wait Running) -> assemble &
  push patch -> launch (all trace env on) -> wait capture complete -> collect
  -> report_memory -> auto_weight_diff (capability B).

Self-healing rules (each consumes one retry):
  * preflight MISS stage   -> fuzzy-match the fork's defined methods against
    the stage candidates (difflib >= 0.7) and PERSIST the new candidate into
    inject_hooks.STAGE_SPEC, then re-run preflight. Unfixable -> stop + reason.
  * wait_capture timeout   -> print the launch-log tail (root cause), kill the
    server, relaunch, wait again.
  * auto-B "no dump"       -> if dumps exist in the pod: re-collect and retry
    auto-B (collection raced the dump). If not: print the [memtrack]/error log
    tail; relaunch the flow from the launch step.
  * auto-B "no HF source"  -> auto-falls back to a header-only model mirror
    pulled from the pod (--pod is always passed), so this normally self-heals.

Usage:
  python3 run_full_auto.py --yaml deploy.yaml --sglang-src <local tree> \
      [--kubeconfig ...] [--ns default] [--sg-dir /sgl-workspace/sglang/python/sglang] \
      [--hf <repo|dir>] [--out ./mem_out] [--max-retries 2] [--health-port 8000]
"""

import argparse
import difflib
import os
import re
import shutil
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, _ROOT)

REMOTE_WORKDIR = "/tmp/memtrack_patch"
REMOTE_LOG = "/tmp/sglang_startup.log"
SNAPSHOT_DIR = "/tmp/capsnap"


def _log(msg):
    print(f"[full-auto] {msg}", flush=True)


# ---------------------------------------------------------------- self-heal
def try_fix_stage_spec(model_runner_path: str) -> bool:
    """Preflight healer: for each MISSing stage, fuzzy-match the fork's defined
    methods and persist the best candidate into inject_hooks.STAGE_SPEC."""
    import importlib
    import inject_hooks
    importlib.reload(inject_hooks)
    rep = inject_hooks.validate_hooks(model_runner_path)
    if not rep["missing"]:
        return False
    src_path = inject_hooks.__file__
    with open(src_path) as f:
        src = f.read()
    fixed = []
    for st in rep["missing"]:
        best, score = None, 0.0
        for meth in rep["defined"]:
            for cand in st["methods"]:
                r = difflib.SequenceMatcher(None, cand, meth).ratio()
                if r > score:
                    best, score = meth, r
        if not best or score < 0.7:
            _log(f"UNFIXABLE stage {st['before']}: no defined method close to "
                 f"{st['methods']} (best={best} score={score:.2f})")
            continue
        m = re.search(r'("before": "%s".*?"methods": \[)' %
                      re.escape(st["before"]), src, re.S)
        if not m:
            continue
        src = src[:m.end()] + f'"{best}", ' + src[m.end():]
        fixed.append((st["before"], best, round(score, 2)))
    if not fixed:
        return False
    with open(src_path, "w") as f:
        f.write(src)
    for stage, meth, score in fixed:
        _log(f"SELF-HEAL: STAGE_SPEC[{stage}] += candidate '{meth}' "
             f"(fuzzy score {score}) -- persisted to inject_hooks.py")
    return True


def diagnose_launch_log(pod, ns, kubeconfig, n=40):
    from deploy_and_patch import exec_in_pod
    tail = exec_in_pod(pod, f"tail -n {n} {REMOTE_LOG} 2>/dev/null || true",
                       ns=ns, kubeconfig=kubeconfig, check=False)
    errs = exec_in_pod(
        pod, f"grep -aE 'Traceback|Error|MISS|memtrack' {REMOTE_LOG} "
             f"2>/dev/null | tail -n 20 || true",
        ns=ns, kubeconfig=kubeconfig, check=False)
    _log(f"--- launch log tail ---\n{tail}")
    if errs.strip():
        _log(f"--- error/memtrack lines ---\n{errs}")


def pod_has_dump(pod, ns, kubeconfig) -> bool:
    from deploy_and_patch import exec_in_pod
    out = exec_in_pod(pod, "ls /tmp/*param_memory_stats*log 2>/dev/null || true",
                      ns=ns, kubeconfig=kubeconfig, check=False)
    return bool(out.strip())


# ---------------------------------------------------------------- steps
def step_preflight(args) -> int:
    from preflight_capability_a import main as pf
    return pf(["--yaml", args.yaml, "--sglang-src", args.sglang_src,
               "--snapshot-dir", SNAPSHOT_DIR])


def step_patch(pod, args):
    from deploy_and_patch import cp_into_pod, exec_in_pod
    import inject_hooks
    wd = tempfile.mkdtemp(prefix="memtrack_")
    for fn in ("gpu_memory_tracker.py", "param_memory_dump.py",
               "apply_patch.py"):
        shutil.copyfile(os.path.join(_ROOT, "assets", fn),
                        os.path.join(wd, fn))
    block = subprocess.run(
        [sys.executable, os.path.join(_HERE, "inject_hooks.py"), "--render"],
        capture_output=True, text=True, check=True).stdout
    with open(os.path.join(wd, "inject_block.txt"), "w") as f:
        f.write(block)
    exec_in_pod(pod, f"rm -rf {REMOTE_WORKDIR}", ns=args.ns,
                kubeconfig=args.kubeconfig, check=False)
    cp_into_pod(pod, wd, REMOTE_WORKDIR, ns=args.ns,
                kubeconfig=args.kubeconfig)
    out = exec_in_pod(pod, f"SG_DIR={args.sg_dir} python3 "
                           f"{REMOTE_WORKDIR}/apply_patch.py",
                      ns=args.ns, kubeconfig=args.kubeconfig)
    _log(out.strip())
    shutil.rmtree(wd, ignore_errors=True)


def step_launch(pod, launch_cmd, args, relaunch=False):
    from deploy_and_patch import exec_in_pod
    from run_and_collect import launch_sglang
    if relaunch:
        exec_in_pod(pod, f"pkill -f launch_server || true; "
                         f"pkill -f memtrack_launch.sh || true; "
                         f"pkill -f 'sglang' || true; sleep 5; "
                         f"rm -f {REMOTE_LOG}",
                    ns=args.ns, kubeconfig=args.kubeconfig, check=False)
    launch_sglang(pod, launch_cmd, ns=args.ns, kubeconfig=args.kubeconfig,
                  log_path=REMOTE_LOG, snapshot_dir=SNAPSHOT_DIR)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--yaml", required=True)
    ap.add_argument("--sglang-src", required=True,
                    help="LOCAL copy of the pod's sglang tree (for validation)")
    ap.add_argument("--kubeconfig", default=None)
    ap.add_argument("--ns", default="default")
    ap.add_argument("--sg-dir", default="/sgl-workspace/sglang/python/sglang",
                    help="sglang package dir INSIDE the pod")
    ap.add_argument("--hf", default=None,
                    help="HF source override for capability B (yaml "
                         "--model-path is a POD path)")
    ap.add_argument("--out", default="./mem_out")
    ap.add_argument("--launch-cmd", default=None,
                    help="override the launch command (default: from yaml)")
    ap.add_argument("--max-retries", type=int, default=2)
    ap.add_argument("--health-port", type=int, default=8000)
    args = ap.parse_args(argv)

    from preflight_capability_a import find_model_runner
    from analyze_startup_stages import extract_launch

    # -- gate: preflight with self-heal ------------------------------------
    for i in range(args.max_retries + 1):
        if step_preflight(args) == 0:
            break
        mr = find_model_runner(args.sglang_src)
        if not (mr and i < args.max_retries and try_fix_stage_spec(mr)):
            _log("STOP: preflight failed and no automatic fix applies -- see "
                 "the gate output above for the exact reason.")
            return 2
        _log(f"preflight retry {i + 1}/{args.max_retries} after self-heal")
    else:
        return 2

    # -- pod up (auto) ------------------------------------------------------
    from deploy_and_patch import ensure_sleep_pod
    sleep_yaml = os.path.join(tempfile.gettempdir(),
                              "memtrack_sleep_" + os.path.basename(args.yaml))
    pods = ensure_sleep_pod(args.yaml, sleep_yaml, ns=args.ns,
                            kubeconfig=args.kubeconfig)
    pod = pods[0]
    _log(f"sleep pod ready: {pod}")

    step_patch(pod, args)
    launch_cmd = args.launch_cmd or extract_launch(args.yaml)["raw"]

    # -- launch -> collect -> report -> auto-B, with flow-level retries -----
    from run_and_collect import wait_capture_complete, collect_logs
    from auto_weight_diff import main as auto_b
    os.makedirs(args.out, exist_ok=True)
    relaunch = False
    for attempt in range(args.max_retries + 1):
        step_launch(pod, launch_cmd, args, relaunch=relaunch)
        relaunch = True
        why = wait_capture_complete(pod, log=REMOTE_LOG, ns=args.ns,
                                    kubeconfig=args.kubeconfig,
                                    health_port=args.health_port)
        _log(f"capture wait: {why}")
        if why == "timeout":
            _log("DIAGNOSIS: capture never completed --")
            diagnose_launch_log(pod, args.ns, args.kubeconfig)
            if attempt < args.max_retries:
                _log(f"relaunching (retry {attempt + 1}/{args.max_retries})")
                continue
            _log("STOP: retries exhausted at capture wait.")
            return 3

        collect_logs(pod, args.out, ns=args.ns, kubeconfig=args.kubeconfig,
                     startup_log=REMOTE_LOG, snapshot_dir=SNAPSHOT_DIR)
        staged = os.path.join(args.out, "staged_rank0_gpu0_full.log")
        subprocess.run(
            [sys.executable, os.path.join(_HERE, "report_memory.py"), staged,
             "--xlsx", os.path.join(args.out, "staged_memory_gpu0.xlsx")],
            check=False)

        b_argv = [args.out, "--yaml", args.yaml, "--pod", pod,
                  "--ns", args.ns, "--sglang-src", args.sglang_src]
        if args.kubeconfig:
            b_argv += ["--kubeconfig", args.kubeconfig]
        if args.hf:
            b_argv += ["--hf", args.hf]
        rc = auto_b(b_argv)
        if rc == 0:
            _log(f"DONE: full flow complete, artifacts in {args.out}/ "
                 f"(staged report + weight_diff/).")
            return 0
        # no dump: dump still in pod (collection race) vs never produced
        if pod_has_dump(pod, args.ns, args.kubeconfig):
            _log("DIAGNOSIS: dump exists in pod but was not collected -- "
                 "re-collecting and retrying capability B.")
            collect_logs(pod, args.out, ns=args.ns, kubeconfig=args.kubeconfig,
                         startup_log=REMOTE_LOG, snapshot_dir=SNAPSHOT_DIR)
            rc = auto_b(b_argv)
            if rc == 0:
                _log(f"DONE after re-collect; artifacts in {args.out}/.")
                return 0
        _log("DIAGNOSIS: no weight dump was produced (dump hook did not "
             "fire) --")
        diagnose_launch_log(pod, args.ns, args.kubeconfig)
        if attempt < args.max_retries:
            _log(f"relaunching flow (retry {attempt + 1}/{args.max_retries})")
            continue
        _log("STOP: retries exhausted; capability B incomplete.")
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
