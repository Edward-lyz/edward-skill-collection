#!/usr/bin/env python3
"""Trigger a fixed-recipe ipipe pipeline and collect its result (stdlib only).

Commands: list | plan | run | status | result.
Recipes live in ../references/scenarios.json; fixed params are baked in, the
`ask` params must come from the user via --set key=value.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

SCENARIOS_PATH = Path(__file__).resolve().parent.parent / "references" / "scenarios.json"
CLI_FALLBACK = Path.home() / ".ipipe-cli" / "bin" / "ipipe-cli"
ACTIVE = {"RUNNING", "WAITTING", "SKIPPING", "SUCCEEDING"}
BLOCKED = "PENDING_FOR_USER"
FAILED = {"FAIL", "CANCEL"}
POLL_SECONDS = 15
STAGE_WAIT_SECONDS = 1200
BUILD_URL = "https://console.cloud.baidu-int.com/devops/ipipe/workspaces/{ws}/pipeline-builds/{pbid}/view"
SECRET_RE = re.compile(r"(Bearer\s+\S+|(?:auth|token|api_key|secret)\S*\s*[=:]\s*\S+)", re.I)
LOG_KEEP_RE = re.compile(r"report table|│|mean_acc|Score|score|Traceback|ERROR|Error|FAIL|不达标")


class IpipeError(RuntimeError):
    """Raised for any CLI, API or recipe failure; message keeps the raw context."""


def load_config() -> dict[str, Any]:
    return json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))


def pick_scenario(cfg: dict[str, Any], name: str) -> tuple[str, dict[str, Any]]:
    key = cfg["aliases"].get(name.strip().lower(), name.strip().lower())
    if key not in cfg["scenarios"]:
        raise IpipeError(f"unknown scenario {name!r}; known: {sorted(cfg['scenarios'])}")
    return key, cfg["scenarios"][key]


def parse_sets(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        key, sep, value = item.partition("=")
        if not sep or not key:
            raise IpipeError(f"--set expects key=value, got {item!r}")
        out[key] = value
    return out


def resolve_stage_params(stage: dict[str, Any], overrides: dict[str, str]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Merge fixed + user values. Returns (params, missing ask entries). Unknown keys fail fast."""
    fixed: dict[str, str] = dict(stage.get("fixed", {}))
    ask: list[dict[str, Any]] = stage.get("ask", [])
    allowed = set(fixed) | {a["key"] for a in ask} | set(stage.get("optional", []))
    unknown = sorted(set(overrides) - allowed)
    if unknown:
        raise IpipeError(f"keys not in this recipe: {unknown}; allowed: {sorted(allowed)}")
    params = {**fixed, **overrides}
    for entry in ask:
        value = params.get(entry["key"])
        choices = entry.get("choices")
        if value is None or not choices:
            continue
        parts = value.split(",") if entry.get("multi") else [value]
        bad = [p for p in parts if p not in choices]
        if bad:
            raise IpipeError(f"{entry['key']}={bad} not in choices {choices}")
    missing = [a for a in ask if a["key"] not in params]
    return params, missing


def resolve_plan(scn: dict[str, Any], overrides: dict[str, str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Per-stage params for the whole recipe plus the union of missing ask entries."""
    stages: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    prev: dict[str, str] = {}
    for stage in scn["stages"]:
        if stage.get("same_params_as_previous"):
            stages.append({"match": stage["match"], "params": dict(prev)})
            continue
        params, miss = resolve_stage_params(stage, overrides)
        missing += [m for m in miss if m not in missing]
        stages.append({"match": stage["match"], "params": params})
        prev = params
    return stages, missing


def cli_path() -> str:
    found = shutil.which("ipipe-cli")
    if found:
        return found
    if CLI_FALLBACK.exists():
        return str(CLI_FALLBACK)
    raise IpipeError("ipipe-cli not found; install it per the ipipe-official skill")


def cli(*args: str) -> Any:
    proc = subprocess.run([cli_path(), *args], capture_output=True, text=True, timeout=120)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise IpipeError(f"ipipe-cli {' '.join(args[:3])} exit={proc.returncode}: {(proc.stdout + proc.stderr)[:400]}") from None
    if proc.returncode != 0 or (isinstance(data, dict) and data.get("code", 200) != 200) or (isinstance(data, dict) and data.get("error")):
        raise IpipeError(f"ipipe-cli {' '.join(args[:3])} failed: {json.dumps(data, ensure_ascii=False)[:400]}")
    return data


def stages_of(pbid: int) -> list[dict[str, Any]]:
    return list(cli("build", "status", "--pipeline-build-id", str(pbid))["entities"])


def find_stage(stages: list[dict[str, Any]], match: str) -> dict[str, Any] | None:
    return next((s for s in stages if match in s["stageName"]), None)


def wait_stage(pbid: int, match: str, want: set[str], timeout: int) -> dict[str, Any]:
    """Poll until the matching stage reaches a status in `want`; fail fast if any stage failed."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        stages = stages_of(pbid)
        failed = [s["stageName"] for s in stages if s["status"] in FAILED]
        stage = find_stage(stages, match)
        if stage and stage["status"] in want:
            return stage
        if failed:
            raise IpipeError(f"stage failed before {match!r} was ready: {failed}")
        time.sleep(POLL_SECONDS)
    raise IpipeError(f"timeout waiting for stage {match!r} to reach {sorted(want)}")


def start_pipeline(scn: dict[str, Any], cfg: dict[str, Any], stages: list[dict[str, Any]], branch: str) -> dict[str, Any]:
    res = cli("trigger", "start", "--pipeline-id", str(scn["pipeline_id"]), "--branch", branch)["entities"]
    pbid = int(res["pipelineBuildId"])
    started = []
    for idx, stage in enumerate(stages):
        ready = wait_stage(pbid, stage["match"], {BLOCKED}, STAGE_WAIT_SECONDS)
        args = ["build", "retry", "--stage-build-id", str(ready["id"])]
        for key, value in stage["params"].items():
            args += ["--param", f"{key}={value}"]
        cli(*args)
        started.append(stage["match"])
        if idx < len(stages) - 1:  # next manual stage only unlocks after this one finishes
            wait_stage(pbid, stage["match"], {"SUCC", "SKIPPED"}, STAGE_WAIT_SECONDS)
    return {"pipelineBuildId": pbid, "buildNumber": res.get("buildNumber"),
            "url": BUILD_URL.format(ws=cfg["workspace_id"], pbid=pbid), "started_stages": started}


def wait_done(pbid: int, timeout: int) -> str:
    """Return 'done' or 'blocked' (a manual stage still waits for a human); raise on timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        statuses = [s["status"] for s in stages_of(pbid)]
        if not ACTIVE & set(statuses):
            return "done"
        if BLOCKED in statuses and "RUNNING" not in statuses:
            return "blocked"
        time.sleep(POLL_SECONDS)
    raise IpipeError(f"pipeline build {pbid} still running after {timeout}s")


def mask(text: str) -> str:
    return SECRET_RE.sub("<secret>", text)


def job_result(job_id: int) -> dict[str, Any]:
    job = cli("build", "job", "--job-build-id", str(job_id))
    plugin = job.get("pluginJobBuild") or {}
    out: dict[str, Any] = {
        "status": job.get("status") or job.get("originalStatus"),
        "duration": job.get("duration"),
        "outParams": {k: mask(str(v)) for k, v in (plugin.get("outParams") or {}).items()},
        "reports": [r.get("reportUrl") for r in plugin.get("reports") or [] if r.get("reportUrl")],
    }
    logs = [lg["url"] for lg in job.get("logs") or [] if lg.get("url")]
    out["log_url"] = logs[0] if logs else None
    if out["log_url"]:
        with urllib.request.urlopen(out["log_url"], timeout=30) as resp:  # noqa: S310 - internal log service
            text = resp.read().decode("utf-8", errors="replace")
        out["log_key_lines"] = [mask(ln)[:240] for ln in text.splitlines() if LOG_KEEP_RE.search(ln)][-40:]
    return out


def collect_result(pbid: int, cfg: dict[str, Any]) -> dict[str, Any]:
    stages = stages_of(pbid)
    summary = [{"stage": s["stageName"].strip(), "status": s["status"],
                "jobs": [{"name": j["jobName"].strip(), "status": j["status"], "id": j["id"]} for j in s["jobBuildBeans"]]}
               for s in stages]
    jobs = {j["id"]: job_result(j["id"]) for s in stages for j in s["jobBuildBeans"] if j["status"] in {"SUCC", "FAIL"}}
    return {"pipelineBuildId": pbid, "url": BUILD_URL.format(ws=cfg["workspace_id"], pbid=pbid),
            "stages": summary, "jobs": jobs}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    for name in ("plan", "run"):
        p = sub.add_parser(name)
        p.add_argument("scenario")
        p.add_argument("--set", action="append", default=[], dest="sets")
        p.add_argument("--branch")
    sub.choices["run"].add_argument("--yes", action="store_true", help="really trigger; without it run == plan")
    sub.choices["run"].add_argument("--wait", type=int, default=0, metavar="SECONDS", help="wait for completion then print result")
    for name in ("status", "result"):
        sub.add_parser(name).add_argument("pipeline_build_id", type=int)
    args = ap.parse_args()
    cfg = load_config()
    try:
        if args.cmd == "list":
            for key, scn in cfg["scenarios"].items():
                print(f"{key:11} pipeline={scn['pipeline_id']:<8} {scn['title']}  [verified: {scn['verified']}]")
            return 0
        if args.cmd in {"status", "result"}:
            out = collect_result(args.pipeline_build_id, cfg) if args.cmd == "result" else stages_of(args.pipeline_build_id)
            print(json.dumps(out, ensure_ascii=False, indent=1))
            return 0
        key, scn = pick_scenario(cfg, args.scenario)
        if scn.get("kind") == "aiqa":
            raise IpipeError("aiqa scenario is not scripted; follow references/api.md section 'AI 智能测试'")
        stages, missing = resolve_plan(scn, parse_sets(args.sets))
        plan = {"scenario": key, "pipeline_id": scn["pipeline_id"], "heavy": bool(scn.get("heavy")),
                "branch": args.branch or cfg["branch"], "stages": stages, "missing_ask": missing}
        if missing:
            print(json.dumps(plan, ensure_ascii=False, indent=1))
            return 2  # caller must ask the user for these keys
        if args.cmd == "plan" or not args.yes:
            print(json.dumps(plan, ensure_ascii=False, indent=1))
            return 0
        started = start_pipeline(scn, cfg, stages, plan["branch"])
        print(json.dumps(started, ensure_ascii=False, indent=1))
        if args.wait:
            state = wait_done(started["pipelineBuildId"], args.wait)
            print(json.dumps({"state": state, **collect_result(started["pipelineBuildId"], cfg)}, ensure_ascii=False, indent=1))
        return 0
    except IpipeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
