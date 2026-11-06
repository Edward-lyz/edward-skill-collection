#!/usr/bin/env python3
"""Build a fork PR inventory for the rebase-first workflow.

Enumerates commits reachable from the fork tip but not from the old
community base, groups them by work-item card, and emits per-commit
signals that drive category and difficulty decisions:

- fork_only: files the community base does not have (clean-pick signal)
- conflict_hist: overlap with a previous whole-branch merge conflict list
- cat_hint: path-based category suggestion, title keywords as fallback (a human must confirm)
- feature: delivery-feature binding, human fills (epd_mm/cache/dspark/vl_kernel/none)
- fw_pct: framework-face share of added lines (F1 in references/pr-taxonomy.md)

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
    "M": "merge 提交（按 remerge-diff 看解冲突残差）",
}

# Title rules that win over paths: community picks, reverts, branch-sync noise.
TITLE_FIRST: list[tuple[str, str]] = [
    (r"Cherry-pick to release|\(#\d{4,}\)$", "C1"),
    (r"^Revert ", "X"),
    (r"Pick .* code|merge .* into", "X"),
    (r"监控|指标|metric|log schema|pyspy|prometheus", "A2"),
]

# Path rules vote by added lines; most lines wins, earlier rule on ties. C2 only for pure test/CI commits.
PATH_HINTS: list[tuple[str, str]] = [
    (r"^(test|\.github|docker|scripts/ci)/|Dockerfile|run_ci|ci_tests", "C2"),
    (r"/models/|dsv4|deepseek_v4|kimi|glm|minimax|qwen", "B1"),
    (r"/observability/|/metrics/|metrics_collector|scheduler_metrics|tracing", "A2"),
    (r"/mem_cache/|asradix|attention_?store|hicache", "A3"),
    (
        r"/entrypoints/|serving_|tokenizer_manager|detokenizer|multi_tokenizer"
        r"|/disaggregation/|/multimodal/|encode_server",
        "A1",
    ),
]

# Fallback when no path rule matches. Hints only; a human confirms every card.
TITLE_HINTS: list[tuple[str, str]] = [
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

# Default migration scope: link (A1), monitoring (A2), multimodal, CI (C2). Everything else
# needs an explicit user request. C1/X/M never count (dropped / noise / merge residue).
MM_RE = re.compile(
    r"multimodal|多模态|\bEPD\b|encode[_ -]?(server|stage)|\bvit\b|\bvlm?\b"
    r"|video|视频|image|图片|mm_|processor|embedding",
    re.IGNORECASE,
)
NEVER_IN_SCOPE = {"C1", "X", "M"}

# F1 face split: model face = model files or paths named after a model.
MODEL_PATH_RE = re.compile(
    r"/models/|dsv4|deepseek_v4|kimi|glm|minimax|qwen", re.IGNORECASE
)
FRAMEWORK_ROOT_RE = re.compile(r"^python/sglang/(srt|kernels|jit_kernel)/")


def run_git(repo: str, *args: str) -> str:
    """Run a git command in repo and return stdout."""
    proc = subprocess.run(
        ["git", "-C", repo, *args], capture_output=True, text=True, check=True
    )
    return proc.stdout


def hint(patterns: list[tuple[str, str]], title: str, default: str) -> str:
    """Return the tag of the first pattern matching title, else default."""
    for pattern, tag in patterns:
        if re.search(pattern, title, re.IGNORECASE):
            return tag
    return default


def path_hint(file_adds: list[tuple[str, int]]) -> str:
    """Return the category whose path rule covers the most added lines, or ''."""
    votes: collections.Counter[str] = collections.Counter()
    unmatched = 0
    for path, n_add in file_adds:
        for pattern, tag in PATH_HINTS:
            if re.search(pattern, path, re.IGNORECASE):
                votes[tag] += max(n_add, 1)
                break
        else:
            unmatched += 1
    if len(votes) > 1 or unmatched:
        votes.pop("C2", None)  # tests shipped with a code change follow that change
    if not votes:
        return ""
    order = [tag for _, tag in PATH_HINTS]
    return max(votes, key=lambda tag: (votes[tag], -order.index(tag)))


def default_scope(cat: str, title: str, files: list[str]) -> str:
    """Pre-label the default migration scope: link / monitor / multimodal / ci / framework / out."""
    if cat in NEVER_IN_SCOPE:
        return "out"
    if cat == "A2":
        return "monitor"
    if cat == "C2":
        return "ci"
    if MM_RE.search(title + " " + " ".join(files)):
        return "multimodal"
    if cat == "A1":
        return "link"
    return "framework" if cat == "A4" else "out"


def difficulty(
    lines: int, fork_only: int, n_files: int, conflict: int, hot: bool
) -> str:
    """Grade replay difficulty from size, fork-only files and conflict history."""
    if conflict > 5 or hot:
        return "难"
    score = (1 if conflict > 0 else 0) + (1 if lines > 3000 else 0)
    score += 1 if (n_files - fork_only) > 10 else 0
    if score == 0:
        return "易"
    return "中" if score <= 2 else "难"


def main() -> None:
    """Write inventory.tsv and cards_summary.md for the fork commits."""
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
        "--reverse", "--topo-order",
        "--format=%H|%h|%an|%ad|%P|%s", "--date=short", "--abbrev=10",
    )
    card_re = re.compile(args.card_pattern)
    reverted = {
        m.group(1)
        for line in log.splitlines()
        if (m := re.search(r'Revert "(.{8,}?)"', line.split("|", 5)[5]))
    }

    rows: list[dict[str, object]] = []
    for line in log.splitlines():
        full, sha, author, date, parents, title = line.split("|", 5)
        title = title.replace("\t", " ")  # TAB 会把 TSV 串列
        is_merge = len(parents.split()) > 1
        m = card_re.search(title)
        card = m.group(0) if m else "NO-CARD"
        files: list[str] = []
        file_adds: list[tuple[str, int]] = []
        add = dele = fw_add = model_add = 0
        # merge 提交只看解冲突带进来的改动（git >= 2.36 的 remerge-diff）
        show_args = ["--remerge-diff"] if is_merge else []
        numstat = run_git(args.repo, "show", *show_args, "--numstat", "--format=", full)
        for stat in numstat.splitlines():
            parts = stat.split("\t")
            if len(parts) != 3:
                continue
            files.append(parts[2])
            n_add = 0 if parts[0] == "-" else int(parts[0])
            add += n_add
            file_adds.append((parts[2], n_add))
            dele += 0 if parts[1] == "-" else int(parts[1])
            if MODEL_PATH_RE.search(parts[2]):
                model_add += n_add
            elif FRAMEWORK_ROOT_RE.search(parts[2]):
                fw_add += n_add
        face_total = fw_add + model_add
        fork_only = sum(1 for f in files if f not in base_files)
        conflict = sum(1 for f in files if f in conflict_paths)
        cat = hint(TITLE_FIRST, title, "") or path_hint(file_adds) or hint(TITLE_HINTS, title, "A4")
        if any(prefix in title for prefix in reverted):
            cat = "X"  # revert 候选；净差为零才算成对互消，见 SKILL.md 第 3 步
        if is_merge:
            cat = "M"
        model = hint(MODEL_HINTS, title + " " + " ".join(files), "generic")
        if re.search(r"fix|修复|bug", title, re.IGNORECASE):
            cat = {"B1": "B2", "A4": "A5"}.get(cat, cat)
        hot = any(h in f for f in files for h in HOT_PATHS)
        lines = add + dele
        rows.append({
            "sha": sha, "date": date, "author": author, "card": card, "title": title,
            "merge": "Y" if is_merge else "",
            "cat_hint": cat, "cat": "", "feature": "", "model": model, "files": len(files),
            "scope_hint": default_scope(cat, title, files),
            "add": add, "del": dele, "fork_only": fork_only, "conflict_hist": conflict,
            "fw_pct": round(100 * fw_add / face_total) if face_total else "",
            "difficulty": difficulty(lines, fork_only, len(files), conflict, hot),
            "icode": args.icode_template.format(sha=full)
            if args.icode_template
            else "",
            "icafe": args.icafe_template.format(card=card)
            if args.icafe_template and card != "NO-CARD"
            else "",
            "decision": "",
            "evidence": "",
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
    in_scope = [r for r in rows if r["scope_hint"] != "out"]
    label = "默认迁链路+监控+多模态+CI，framework 待 F4 判受益面"
    print(f"scope_hint ({label}): {len(in_scope)}/{len(rows)} commits")
    print("cat/feature 列为空，人工确认 cat_hint 后填入；混合卡逐提交定类，特性绑定块打 feature 标签。")


if __name__ == "__main__":
    main()
