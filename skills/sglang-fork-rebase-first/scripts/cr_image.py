#!/usr/bin/env python3
"""Wait for the CR pipeline of a pushed change and print the built image address.

The ChangePipeline of the module builds one image per change in the job
"构建镜像"; the address is in that job's outParams NORMAL_IMAGE_VERSION.
Pass the TIP commit of the replay stack: every change checks out its own ref,
so the tip image contains the whole stack.

Exit codes: 0 image found (printed on stdout), 1 build failed or image missing,
2 timeout. Needs ipipe-cli logged in (`ipipe-cli login status`).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

IMAGE_JOB = "构建镜像"
IMAGE_KEY = "NORMAL_IMAGE_VERSION"
PENDING = {"RUNNING", "WAITING", "INIT", "PENDING", "QUEUED", "CREATED", "SKIPPED"}
FAILED_BUILD = {"FAIL", "CANCEL", "CANCELED", "ABORT"}


def find_cli() -> str:
    cli = shutil.which("ipipe-cli") or os.path.expanduser("~/.ipipe-cli/bin/ipipe-cli")
    if os.access(cli, os.X_OK):
        return cli
    # Not installed: fetch the official ipipe-official package and install the CLI.
    ensure = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ensure_ipipe.sh")
    proc = subprocess.run(["bash", ensure], capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"ipipe-cli missing and auto-install failed:\n{proc.stderr}")
    return proc.stdout.strip()


def ipipe(cli: str, *args: str) -> object:
    proc = subprocess.run([cli, *args], capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"ipipe-cli {' '.join(args)} failed: {proc.stderr or proc.stdout}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        sys.exit(f"ipipe-cli returned non-JSON: {proc.stdout[:300]}")


def latest_build(cli: str, module: str, revision: str, conf_id: int) -> dict | None:
    builds = ipipe(cli, "build", "commit", "--module", module, "--revision", revision)
    if not isinstance(builds, list):
        sys.exit(f"unexpected build commit payload: {str(builds)[:300]}")
    mine = [b for b in builds if b.get("pipelineConfId") == conf_id]
    return max(mine, key=lambda b: b["buildTime"]) if mine else None


def image_task(cli: str, build_id: int) -> dict | None:
    tasks = ipipe(cli, "build", "tasks", "--pipeline-build-id", str(build_id))
    if not isinstance(tasks, dict):
        sys.exit(f"unexpected build tasks payload: {str(tasks)[:300]}")
    for task in tasks["entities"]:
        if task["jobName"].strip() == IMAGE_JOB:
            return task
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--module", default="baidu/hac-aiacc/aiak_sglang")
    ap.add_argument("--revision", required=True, help="tip commit SHA or Change-Id")
    ap.add_argument("--conf-id", type=int, default=2205943,
                    help="ChangePipeline-dev/dp 集成流水线【GPU】")
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--interval", type=int, default=45)
    ap.add_argument("--base-image", default="", help="user-confirmed base image, echoed to output")
    ap.add_argument("-o", "--output", help="write JSON {image, base_image, build_url} here")
    args = ap.parse_args()

    cli = find_cli()
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        build = latest_build(cli, args.module, args.revision, args.conf_id)
        task = image_task(cli, build["id"]) if build else None
        state = task["status"] if task else "NO-BUILD-YET"
        print(f"[cr_image] build={build and build['id']} {IMAGE_JOB}={state}", file=sys.stderr)
        if task and state == "SUCC":
            image = (task.get("outParams") or {}).get(IMAGE_KEY)
            if not image:
                print(f"{IMAGE_JOB} succeeded but {IMAGE_KEY} is empty", file=sys.stderr)
                return 1
            print(image)
            if args.output:
                with open(args.output, "w") as fh:
                    json.dump({"image": image, "base_image": args.base_image,
                               "build_url": build["buildUrl"]}, fh)
            return 0
        if build and task and state not in PENDING:
            print(f"image build ended {state}: {build['buildUrl']}", file=sys.stderr)
            return 1
        if build and build["status"] in FAILED_BUILD:
            # An earlier stage failed, so the image job will never run.
            print(f"pipeline {build['status']} before image: {build['buildUrl']}", file=sys.stderr)
            return 1
        time.sleep(args.interval)
    print("timeout waiting for image build", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
