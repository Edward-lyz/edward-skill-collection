"""Launch sglang inside the prepared pod, WAIT until startup memory capture is
actually finished, then collect logs. Requires a reachable cluster.

Why the explicit wait: CUDA-graph capture iterates over many batch sizes and can
take minutes, and with speculative decoding the DRAFT ModelRunner captures its
own graph AFTER the main one. If you copy the log too early you miss
`after_cuda_graph` (and the draft's whole cuda-graph pair). So before collecting
we gate on a completion signal:

  1. Prefer the health endpoint (fully ready => all capture done), but a decode
     node without its prefill peer may never report healthy.
  2. Fall back to log stability: the number of `after_cuda_graph` snapshots (one
     per ModelRunner per local GPU: main + draft) must be > 0 AND unchanged for
     `stable_secs` -- i.e. no capture has fired recently.

Only then do we `kubectl cp` the log and dumps back.

Fine-grained trace (aiak commit 491ed25b, native or skill-wrapped): launch_sglang
now enables ALL trace switches by default (SGLANG_TRACK_GPU_MEMORY=1,
SGLANG_CAPTURE_MEM_LEDGER=1, SGLANG_CAPTURE_MEM_SNAPSHOT_DIR=/tmp/capsnap) --
capability A constraint. Pass `snapshot_dir="/tmp/capsnap"` to collect_logs to
also pull back the per-runner `capture_mem_*.pickle` allocator snapshots.
"""

import time
from typing import List, Optional

from deploy_and_patch import exec_in_pod, _run


def launch_sglang(pod, launch_cmd, ns="default", kubeconfig=None,
                  log_path="/tmp/sglang_startup.log", extra_env="",
                  full_trace=True, snapshot_dir="/tmp/capsnap"):
    """Launch with ALL memory-trace switches ON by default (capability A
    constraint): SGLANG_TRACK_GPU_MEMORY + SGLANG_CAPTURE_MEM_LEDGER +
    SGLANG_CAPTURE_MEM_SNAPSHOT_DIR. Pass full_trace=False to fall back to the
    bare tracker only; extra_env is appended either way."""
    env = "SGLANG_TRACK_GPU_MEMORY=1"
    if full_trace:
        env += " SGLANG_CAPTURE_MEM_LEDGER=1"
        if snapshot_dir:
            env += f" SGLANG_CAPTURE_MEM_SNAPSHOT_DIR={snapshot_dir}"
            exec_in_pod(pod, f"mkdir -p {snapshot_dir}",
                        ns=ns, kubeconfig=kubeconfig, check=False)
    if extra_env:
        env += " " + extra_env
    # The launch blob is usually `<shell> -c <multi-line script>` flattened to
    # one string (extract_launch joins command+args). Re-nesting it UNQUOTED
    # after nohup would make the inner `-c` grab only the first word (`export`)
    # and exit silently with an empty log. So: unwrap the script body, ship it
    # base64 (quoting-proof) into a pod-side file, and nohup THAT file.
    import base64
    import re as _re
    script = launch_cmd.strip()
    m = _re.match(r"^(?:/bin/|/usr/bin/)?(?:ba|da)?sh\s+-c\s+(.*)$", script,
                  _re.S)
    if m:
        script = m.group(1)
    b64 = base64.b64encode(script.encode()).decode()
    launch_file = "/tmp/memtrack_launch.sh"
    exec_in_pod(pod, f"echo {b64} | base64 -d > {launch_file}",
                ns=ns, kubeconfig=kubeconfig)
    # Run with bash, NOT sh: deploy scripts routinely use bash-only syntax
    # (e.g. `ARGS=( ... )` arrays); dash would die with
    # `Syntax error: "(" unexpected` and leave an empty log.
    exec_in_pod(pod, f"{env} nohup /bin/bash {launch_file} > {log_path} 2>&1 &",
                ns=ns, kubeconfig=kubeconfig)


def _count(pod, pattern, log, ns, kubeconfig):
    out = exec_in_pod(pod, f"grep -aEc '{pattern}' {log} 2>/dev/null || true",
                      ns=ns, kubeconfig=kubeconfig, check=False)
    try:
        return int(out.strip() or 0)
    except ValueError:
        return 0


def wait_health(pod, port=8000, path="/health", ns="default", kubeconfig=None):
    try:
        exec_in_pod(pod, f"curl -sf http://127.0.0.1:{port}{path}",
                    ns=ns, kubeconfig=kubeconfig, check=True)
        return True
    except Exception:
        return False


def wait_capture_complete(pod, log="/tmp/sglang_startup.log", ns="default",
                          kubeconfig=None, stable_secs=90, poll=20,
                          timeout_s=2400, health_port=8000) -> str:
    """Block until startup memory capture is done. Returns why it stopped.

    Completion = health-ready OR the `after_*cuda_graph` snapshot count is >0 and
    has not changed for `stable_secs` (no capture fired recently). Guards against
    collecting mid-capture.
    """
    deadline = time.time() + timeout_s
    last_count, last_change = -1, time.time()
    while time.time() < deadline:
        if wait_health(pod, port=health_port, ns=ns, kubeconfig=kubeconfig):
            return "health-ready"
        # matches legacy `after_cuda_graph` AND canonical
        # `after_target_cuda_graph` / `after_draft_cuda_graph`
        c = _count(pod, r"Tracker\] \[after_[a-z_]*cuda_graph", log, ns, kubeconfig)
        if c != last_count:
            last_count, last_change = c, time.time()
        elif c > 0 and (time.time() - last_change) >= stable_secs:
            return f"stable ({c} after_cuda_graph snapshots, no change {stable_secs}s)"
        time.sleep(poll)
    return "timeout"


def collect_logs(pod, out_dir, ns="default", kubeconfig=None,
                 startup_log="/tmp/sglang_startup.log", rank_tag="TP0 EP0",
                 snapshot_dir: Optional[str] = None):
    """Copy startup log + per-GPU weight dumps; build a single-rank staged log
    (every stage, time order, no dedup) ready for report_memory. The staged log
    also keeps the fine-grained trace lines (capture-mem-ledger + DeepEP buffer
    allocs) so report_memory can render its extra sections. With snapshot_dir,
    also pull back the capture allocator pickles."""
    import os
    os.makedirs(out_dir, exist_ok=True)
    local_log = os.path.join(out_dir, "sglang_startup.log")
    _run(["cp", f"{ns}/{pod}:{startup_log}", local_log], kubeconfig, check=False)
    collected = [local_log]
    listing = exec_in_pod(pod, "ls /tmp/*param_memory_stats*log 2>/dev/null || true",
                          ns=ns, kubeconfig=kubeconfig, check=False)
    for remote in listing.split():
        local = os.path.join(out_dir, os.path.basename(remote))
        _run(["cp", f"{ns}/{pod}:{remote}", local], kubeconfig, check=False)
        collected.append(local)
    if snapshot_dir:
        listing = exec_in_pod(
            pod, f"ls {snapshot_dir}/capture_mem_*.pickle 2>/dev/null || true",
            ns=ns, kubeconfig=kubeconfig, check=False)
        for remote in listing.split():
            local = os.path.join(out_dir, os.path.basename(remote))
            _run(["cp", f"{ns}/{pod}:{remote}", local], kubeconfig, check=False)
            collected.append(local)
    # single-rank full timeline (no dedup), for report_memory --xlsx
    import re
    staged = os.path.join(out_dir, "staged_rank0_gpu0_full.log")
    with open(local_log, "r", errors="ignore") as f, open(staged, "w") as g:
        for line in f:
            if rank_tag not in line:
                continue
            if (re.search(r"GPU Memory Tracker\] \[[a-z]", line)
                    or "[capture-mem-ledger]" in line
                    or "[cg-breakdown]" in line
                    or "Allocating DeepEP buffer" in line):
                g.write(line)
    collected.append(staged)
    return collected
