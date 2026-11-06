#!/usr/bin/env python3
"""Mode of the last N executed runs of the 压测自动化 "DeepSeek压测" stage.

The stage's manual params cannot be read through ipipe-cli, so each run's params are
recovered from its job logs: the `aiak_perf.py` command line (set -x echo) and the
`dataset: '<label>##<file>'` line of the alert job. Only parsed flags are printed;
log lines are never echoed because the job script carries a credential.

  python3 stress_history.py [--last 10] [--pipeline-id 2353017] [--module baidu/bcc-test/ds_test]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from collections import Counter
from typing import Any

import ipipe_run as run

STAGE = "DeepSeek压测"
EXECUTED = {"SUCC", "FAIL", "CANCEL"}  # WAITTING / PENDING_FOR_USER mean the stage never ran
LOG_HEAD_LINES = 1500  # the command echo is within the first ~100 lines of a 12 h log
# aiak_perf.py flag -> stage param key
FLAG_TO_KEY = {
    "run_time_second": "run_time_second", "n": "num_requests", "qps": "qps", "of": "fixed_output_length",
    "k8s_mode": "k8s_mode", "dataset_type": "dataset_type", "runner_type": "runner_type",
    "qps_strategy": "qps_strategy", "enable_thinking": "enable_thinking",
    "aiak_perf_version": "aiak_perf_version", "host": "as_address", "ports": "port",
    "thinking_budget": "thinking_budget",
}
ABSENT_FLAG_DEFAULT = {"port": "1", "thinking_budget": "NA"}  # script omits the flag at these values
FLAG_RE = re.compile(r'--(\w+) (?:"([^"]*)"|(\S+))')
DATASET_RE = re.compile(r"dataset: '\\''(.+?)'\\'")


def parse_perf_command(line: str) -> dict[str, str]:
    """Stage params from one `+ command='python3 .../aiak_perf.py --x ...'` trace line."""
    start = line.find("aiak_perf.py")
    if start < 0:
        return {}
    flags = {m.group(1): m.group(2) if m.group(2) is not None else m.group(3) for m in FLAG_RE.finditer(line[start:])}
    params = {FLAG_TO_KEY[f]: v for f, v in flags.items() if f in FLAG_TO_KEY}
    for key, default in ABSENT_FLAG_DEFAULT.items():
        params.setdefault(key, default)
    if "k8s_pod" in flags:
        params["pod_role"] = "prefill" if "-prefill" in flags["k8s_pod"] else "other"
    return params


def pick_mode(values: list[str]) -> tuple[str, int]:
    """Most common value; ties go to the newest (values are ordered newest first)."""
    counts = Counter(values)
    best = max(counts.values())
    return next(v for v in values if counts[v] == best), best


def read_log_head(job_id: int) -> list[str]:
    """Return the first lines of a job log."""
    job = run.cli("build", "job", "--job-build-id", str(job_id))
    logs = [lg["url"] for lg in job.get("logs") or [] if lg.get("url")]
    if not logs:
        return []
    lines: list[str] = []
    with urllib.request.urlopen(logs[0], timeout=60) as resp:  # noqa: S310 - internal log service
        for raw in resp:
            lines.append(raw.decode("utf-8", errors="replace").rstrip())
            if len(lines) >= LOG_HEAD_LINES:
                break
    return lines


def run_params(stage: dict[str, Any]) -> dict[str, str]:
    """Return the parameters a stage ran with."""
    params: dict[str, str] = {}
    for job in stage["jobBuildBeans"]:
        name = job["jobName"]
        if "告警" not in name and "压测" not in name:
            continue
        for line in read_log_head(job["id"]):
            if "告警" in name and "dataset_name" not in params:
                match = DATASET_RE.search(line)
                if match:
                    params["dataset_name"] = match.group(1)
            if "压测" in name and "+ command=" in line and "aiak_perf.py" in line:
                params.update(parse_perf_command(line))
                break
    return params


def executed_runs(module: str, pipeline_id: int, last: int) -> list[dict[str, Any]]:
    """Return the last executed stress runs of a pipeline."""
    rows = run.cli("build", "history", "--module", module, "--limit", "1500")
    mine = [r for r in rows if r.get("pipelineConfId") == pipeline_id]  # already newest first
    runs: list[dict[str, Any]] = []
    for row in mine:
        stage = run.find_stage(run.stages_of(row["id"]), STAGE)
        if not stage or stage["status"] not in EXECUTED:
            continue
        runs.append({"pipelineBuildId": row["id"], "buildNumber": row["buildNumber"], "status": stage["status"],
                     "user": stage.get("triggerUser"), **run_params(stage)})
        if len(runs) == last:
            break
    return runs


def summarize(runs: list[dict[str, Any]]) -> dict[str, list[Any]]:
    """Group run values by parameter."""
    keys = sorted({k for r in runs for k in r} - {"pipelineBuildId", "buildNumber", "status", "user"})
    return {k: list(pick_mode([r[k] for r in runs if k in r])) + [sum(1 for r in runs if k in r)] for k in keys}


def main() -> int:
    """Parse arguments and print stress run history."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--last", type=int, default=10)
    ap.add_argument("--pipeline-id", type=int, default=2353017)
    ap.add_argument("--module", default="baidu/bcc-test/ds_test")
    args = ap.parse_args()
    try:
        runs = executed_runs(args.module, args.pipeline_id, args.last)
    except run.IpipeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    # mode entry = [value, count among runs that carry the key, runs that carry the key]
    print(json.dumps({"runs": runs, "mode": summarize(runs)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
