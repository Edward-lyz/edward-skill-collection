#!/usr/bin/env python3
"""Build a fork PR inventory for the rebase-first workflow.

Enumerates commits reachable from the fork tip but not from the old
community base, groups them by work-item card, and emits per-commit
signals that drive category and difficulty decisions:

- fork_only: files the community base does not have (clean-pick signal)
- conflict_hist: overlap with a previous whole-branch merge conflict list
- cat_hint: keyword-based category suggestion (a human must confirm)
- feature: delivery-feature binding, human fills (epd_mm/cache/dspark/vl_kernel/none)

Outputs inventory.tsv (one row per commit) and cards_summary.md.
"""

from __future__ import annotations

import argparse
import collections
import csv
import re
import subprocess
from pathlib import Path

CATEGORIES = {
    "A1": "链路适配",
    "A2": "监控适配",
    "A3": "Cache 适配",
    "A4": "通用模型优化",
    "A5": "通用 BUGFIX",
    "B1": "具体模型优化/适配",
    "B2": "具体模型 BUGFIX",
    "C1": "社区已收录(丢弃)",
    "C2": "工程/CI",
    "X": "成对消除/搬运残留",
}

# Ordered: first match wins. Hints only; a human confirms every card.
TITLE_HINTS: list[tuple[str, str]] = [
    (r"Cherry-pick to release|\(#\d{4,}\)$", "C1"),
    (r"^Revert ", "X"),
    (r"Pick .* code|merge .* into", "X"),
    (r"单测|run_ci|ci_tests|Dockerfile|镜像|mirror dep|base image", "C2"),
    (r"监控|指标|metric|日志|log schema|trace|pyspy|prometheus", "A2"),
    (r"asradix|attention ?store|radix|cache", "A3"),
    (
        (
            r"EPD|encode|embedding|tokenize|transfer|mooncake|zmq"
            r"|ibdevice|协议|接口|health"
        ),
        "A1",
    ),
    (r"kernel opt|显存|memory|量化|weight shard|mxfp4|fp8", "B1"),
    (r"fix|修复|bug", "A5"),
]

MODEL_HINTS: list[tuple[str, str]] = [
    (r"kimi[- _]?k?3|\bk3\b|kda|flashkda|dspark", "K3"),
    (r"k2\.?6|k26", "K2.6"),
    (r"k2\.?5|k25", "K2.5"),
    (r"\bv4\b|deepseek", "V4"),
    (r"glm", "GLM"),
]

HOT_PATHS = (
    "managers/scheduler",
    "model_executor/model_runner",
    "entrypoints/openai/serving",
)


def run_git(repo: str, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", repo, *args], capture_output=True, text=True, check=True
    )
    return proc.stdout


def hint(patterns: list[tuple[str, str]], title: str, default: str) -> str:
    for pattern, tag in patterns:
        if re.search(pattern, title, re.IGNORECASE):
            return tag
    return default


def difficulty(
    lines: int, fork_only: int, n_files: int, conflict: int, hot: bool
) -> str:
    if conflict > 5 or hot:
        return "难"
    score = (1 if conflict > 0 else 0) + (1 if lines > 3000 else 0)
    score += 1 if (n_files - fork_only) > 10 else 0
    if score == 0:
        return "易"
    return "中" if score <= 2 else "难"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--fork", required=True, help="frozen fork tip SHA")
    ap.add_argument("--old-base", required=True, help="frozen merge-base SHA")
    ap.add_argument(
        "--conflict-paths", help="file list from a previous whole-branch merge"
    )
    ap.add_argument("--card-pattern", default=r"luno-\d+|aihc-qa-\d+")
    ap.add_argument("--icafe-template", default="", help="e.g. http://.../{card}/show")
    ap.add_argument("--icode-template", default="", help="e.g. http://.../commits/{sha}")
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base_files = set(
        run_git(args.repo, "ls-tree", "-r", "--name-only", args.old_base).splitlines()
    )
    conflict_paths: set[str] = set()
    if args.conflict_paths:
        conflict_paths = set(Path(args.conflict_paths).read_text().split())

    log = run_git(
        args.repo, "log", args.fork, "^" + args.old_base,
        "--no-merges", "--reverse", "--topo-order",
        "--format=%H|%h|%an|%ad|%s", "--date=short",
    )
    card_re = re.compile(args.card_pattern)
    reverted = {
        m.group(1)
        for line in log.splitlines()
        if (m := re.search(r'Revert "(.{8,}?)"', line.split("|", 4)[4]))
    }

    rows: list[dict[str, object]] = []
    for line in log.splitlines():
        full, sha, author, date, title = line.split("|", 4)
        m = card_re.search(title)
        card = m.group(0) if m else "NO-CARD"
        files: list[str] = []
        add = dele = 0
        numstat = run_git(args.repo, "show", "--numstat", "--format=", full)
        for stat in numstat.splitlines():
            parts = stat.split("\t")
            if len(parts) != 3:
                continue
            files.append(parts[2])
            add += 0 if parts[0] == "-" else int(parts[0])
            dele += 0 if parts[1] == "-" else int(parts[1])
        fork_only = sum(1 for f in files if f not in base_files)
        conflict = sum(1 for f in files if f in conflict_paths)
        cat = hint(TITLE_HINTS, title, "A1")
        if any(prefix in title for prefix in reverted):
            cat = "X"  # one side of a revert pair
        model = hint(MODEL_HINTS, title + " " + " ".join(files), "generic")
        if cat == "B1" and re.search(r"fix|修复|bug", title, re.IGNORECASE):
            cat = "B2"
        hot = any(h in f for f in files for h in HOT_PATHS)
        lines = add + dele
        rows.append({
            "sha": sha, "date": date, "author": author, "card": card, "title": title,
            "cat_hint": cat, "cat": "", "feature": "", "model": model, "files": len(files),
            "add": add, "del": dele, "fork_only": fork_only, "conflict_hist": conflict,
            "difficulty": difficulty(lines, fork_only, len(files), conflict, hot),
            "icode": args.icode_template.format(sha=full)
            if args.icode_template
            else "",
            "icafe": args.icafe_template.format(card=card)
            if args.icafe_template and card != "NO-CARD"
            else "",
        })

    tsv = out_dir / "inventory.tsv"
    with tsv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    cards: dict[str, list[dict[str, object]]] = collections.defaultdict(list)
    for row in rows:
        cards[str(row["card"])].append(row)
    md = ["| card | commits | lines | fork_only/files | conflict_hist | hint mix |",
          "|---|---:|---:|---:|---:|---|"]
    for card, rs in sorted(cards.items(), key=lambda kv: -len(kv[1])):
        lines_sum = sum(int(r["add"]) + int(r["del"]) for r in rs)
        fo = sum(int(r["fork_only"]) for r in rs)
        nf = sum(int(r["files"]) for r in rs)
        cf = sum(int(r["conflict_hist"]) for r in rs)
        hints = collections.Counter(str(r["cat_hint"]) for r in rs)
        mix = "+".join(f"{k}x{v}" for k, v in hints.most_common())
        md.append(f"| {card} | {len(rs)} | {lines_sum:,} | {fo}/{nf} | {cf} | {mix} |")
    (out_dir / "cards_summary.md").write_text("\n".join(md) + "\n")
    print(f"{len(rows)} commits, {len(cards)} cards -> {tsv}")
    print("cat/feature 列为空，人工确认 cat_hint 后填入；混合卡逐提交定类，特性绑定块打 feature 标签。")


if __name__ == "__main__":
    main()

