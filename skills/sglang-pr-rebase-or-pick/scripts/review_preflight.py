#!/usr/bin/env python3
"""Validate a merge candidate before publishing a review-only change.

Checks that the candidate is based on the frozen target, that a squash candidate
holds exactly one commit, and that every commit message carries a Change-Id footer
and a tracker id matching --card-pattern.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


CHANGE_ID_RE = re.compile(r"(?m)^Change-Id:\s+I[0-9a-fA-F]{40}\s*$")
DEFAULT_CARD_PATTERN = r"\b[a-z]+-\d+\b"


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True, stderr=subprocess.STDOUT
    ).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--target-sha", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--mode", choices=("pick", "squash"), required=True)
    parser.add_argument(
        "--card-pattern",
        default=DEFAULT_CARD_PATTERN,
        help="regex for the tracker id required in every commit message",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    card_re = re.compile(args.card_pattern, re.IGNORECASE)

    result = {
        "status": "pass",
        "mode": args.mode,
        "target_sha": args.target_sha,
        "head": git(args.repo, "rev-parse", args.head),
        "commit_count": None,
        "commits": [],
        "errors": [],
    }

    try:
        if (
            subprocess.call(
                [
                    "git",
                    "-C",
                    str(args.repo),
                    "merge-base",
                    "--is-ancestor",
                    args.target_sha,
                    args.head,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            != 0
        ):
            result["errors"].append("candidate is not based on the frozen target SHA")

        commit_shas = git(
            args.repo, "rev-list", "--reverse", f"{args.target_sha}..{args.head}"
        ).splitlines()
        result["commit_count"] = len(commit_shas)
        if args.mode == "squash" and len(commit_shas) != 1:
            result["errors"].append(
                "squash candidate must contain exactly one commit, "
                f"found {len(commit_shas)}"
            )

        for sha in commit_shas:
            message = git(args.repo, "show", "-s", "--format=%B", sha)
            cards = sorted(set(card_re.findall(message)))
            checks = {
                "sha": sha,
                "change_id": bool(CHANGE_ID_RE.search(message)),
                "cards": cards,
            }
            result["commits"].append(checks)
            if not checks["change_id"]:
                result["errors"].append(f"{sha}: missing valid Change-Id footer")
            if not cards:
                result["errors"].append(f"{sha}: missing tracker id in commit message")
    except (OSError, subprocess.CalledProcessError) as exc:
        result["status"] = "error"
        result["errors"].append(str(exc))

    if result["errors"]:
        result["status"] = "fail" if result["status"] == "pass" else result["status"]

    payload = json.dumps(result, ensure_ascii=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
