#!/usr/bin/env python3
"""Build a per-commit code-diff digest for classification review.

Usage:
    python3 make_digest.py REPO BASE SOURCE_TIP SHADOW_REF OUT.md [--lines 25] [--files 8]

The shadow chain is read from BASE..SHADOW_REF. Each commit body is expected to
contain either "来源提交（N 个）：..." or "Source commits: ...".
"""

import argparse
import os
import re
import subprocess
import sys


def git(repo, *args):
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout


def parse_sources(body):
    match = re.search(r"来源提交（\d+ 个）：(.+)", body)
    if match:
        return [s.strip() for s in match.group(1).split(",") if s.strip()]
    match = re.search(r"Source commits:\s*(.+)", body)
    if match:
        return [s.strip() for s in match.group(1).split(",") if s.strip()]
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo")
    parser.add_argument("base")
    parser.add_argument("source_tip")
    parser.add_argument("shadow_ref")
    parser.add_argument("out")
    parser.add_argument("--lines", type=int, default=25)
    parser.add_argument("--files", type=int, default=8)
    args = parser.parse_args()

    repo = os.path.abspath(args.repo)
    chain = git(repo, "rev-list", "--reverse", f"{args.base}..{args.shadow_ref}").split()

    output = [
        "# 提交级代码 diff 摘要",
        "",
        "每条包含：来源提交、原标题、改动文件、最多 "
        f"{args.lines} 行真实增删代码。标题只是索引，分类以 diff 为准。",
        "",
    ]
    commit_count = 0

    for shadow_commit in chain:
        subject = git(repo, "log", "-1", "--format=%s", shadow_commit).strip()
        body = git(repo, "log", "-1", "--format=%b", shadow_commit)
        sources = parse_sources(body)
        if not sources:
            continue
        output += [f"## 影子提交 {shadow_commit[:10]}  {subject}", ""]

        for short in sources:
            full = git(repo, "rev-parse", short).strip()
            title = git(repo, "log", "-1", "--format=%s", full).strip()
            commit_count += 1

            numstat = git(
                repo, "show", "--numstat", "--format=", "--no-renames", full
            ).splitlines()
            rows = [line.split("\t") for line in numstat if line.strip()]
            files = [f"`{p}` (+{a}/-{d})" for a, d, p in rows[: args.files]]
            if len(rows) > args.files:
                files.append(f"… +{len(rows) - args.files} files")

            output += [f"### {full[:10]} | {title}", ""]
            output.append("files: " + " ; ".join(files))

            diff = git(repo, "show", "-U0", "--format=", "--no-color", full)
            lines = [
                line
                for line in diff.splitlines()
                if (line.startswith("+") or line.startswith("-"))
                and not line.startswith("+++")
                and not line.startswith("---")
                and line.strip() not in ("+", "-")
            ]
            if lines:
                output.append("```diff")
                output += lines[: args.lines]
                if len(lines) > args.lines:
                    output.append(f"… ({len(lines) - args.lines} more diff lines)")
                output.append("```")
            else:
                output.append("(binary or empty diff)")
            output.append("")

    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(output))

    print(
        f"wrote {args.out}: {len(chain)} shadow commits, "
        f"{commit_count} source commits, {os.path.getsize(args.out)} bytes"
    )


if __name__ == "__main__":
    sys.exit(main())
