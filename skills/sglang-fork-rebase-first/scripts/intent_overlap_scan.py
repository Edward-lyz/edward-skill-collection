#!/usr/bin/env python3
"""Find commit pairs where the fork and upstream pursued the same intent.

A long-lived fork and its upstream often build the same capability twice. Those
pairs are what a whole-branch merge resolves badly: line-level merging keeps both
implementations, or keeps the fork's caller against upstream's callee. They need
deliberate per-pair decisions, which means isolating them as their own commits so
a reviewer can trace each one.

Reported categories:

    LOCAL-ADAPT    rival pair whose fork side carries environment-adaptation
                   markers (cache, memory, monitoring, transport) -> keep the
                   fork behavior and re-attach it on the upstream structure
    RIVAL          both sides changed the same files AND their subjects share a
                   topic word -> pick in isolation, decide which wins
    FILE-ONLY      same files, no topic overlap -> usually an incidental
                   collision in a file both sides happen to touch
    TOPIC-ONLY     topic overlap, no shared file -> parallel work in different
                   layers; confirm, do not assume

Shared files are weighted by how many commits touch them. A file that only two
commits touch is strong evidence of rival work; a file touched by a hundred
commits carries almost none, which is what keeps hot files like serving_chat.py
from pairing everything with everything.

Anything not reported had no counterpart on the other side and can ride along in
the bulk merge.

A dispositioned pair goes into the waiver file as `fork_short<TAB>reason`. Both
parents are frozen SHAs, so a waiver stays valid across patchsets and the reason
column doubles as the disposition record for the review description.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# Words marking work done for the local deployment rather than for the model.
# These capabilities rarely exist upstream and must survive the merge.
LOCAL_ADAPT_WORDS = {
    "cache", "hicache", "asradix", "radix", "mem", "memory", "oom", "vram",
    "monitor", "metric", "metrics", "prometheus", "trace", "tracing", "log",
    "logging", "deploy", "yaml", "quota", "zmq", "mooncake", "rdma", "ib",
    "bootstrap", "watchdog", "health",
}

# Tokens carrying no topic signal; dropping them keeps the overlap score honest.
STOP_WORDS = {
    "a", "add", "and", "bug", "change", "clean", "cleanup", "code", "fix",
    "for", "from", "in", "into", "make", "minor", "more", "of", "on",
    "refactor", "remove", "revert", "support", "the", "to", "update", "use",
    "with",
}

TOKEN_RE = re.compile(r"[a-z0-9_]+")
UNIT_SEP = chr(31)


def run(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def topic_tokens(subject: str) -> set[str]:
    """Subject words that carry topic meaning."""
    words = {word for word in TOKEN_RE.findall(subject.lower()) if len(word) > 2}
    return words - STOP_WORDS


def read_waivers(path: Path | None) -> dict[str, str]:
    """`fork_short<TAB>reason` per line. A waiver without a reason is not accepted."""
    waivers: dict[str, str] = {}
    if path is None or not path.exists():
        return waivers
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, _, reason = line.partition("	")
        if reason.strip():
            waivers[name.strip()] = reason.strip()
    return waivers


def collect_commits(repo: Path, base: str, tip: str, limit: int) -> list[dict]:
    """Commits reachable from tip but not base, newest first, with their files."""
    raw = run(
        repo, "log", "--no-merges", f"--max-count={limit}",
        f"--format=%H{UNIT_SEP}%s", f"{base}..{tip}",
    )
    commits = []
    for line in raw.splitlines():
        parts = line.split(UNIT_SEP, 1)
        if len(parts) != 2:
            continue
        sha, subject = parts
        files = set(run(repo, "show", "--pretty=", "--name-only", sha).split())
        commits.append(
            {
                "sha": sha,
                "short": sha[:12],
                "subject": subject,
                "files": files,
                "topics": topic_tokens(subject),
            }
        )
    return commits


def score_pair(
    fork: dict, upstream: dict, file_weight: dict[str, float]
) -> tuple[float, set[str], set[str]]:
    """Overlap strength plus the shared files and shared topic words.

    Shared files are weighted by rarity: a file touched by two commits is real
    evidence, a file touched by a hundred is noise. Without this a hot file pairs
    every commit with every other commit.
    """
    shared_files = fork["files"] & upstream["files"]
    shared_topics = fork["topics"] & upstream["topics"]
    file_score = sum(file_weight.get(path, 0.0) for path in shared_files)
    score = file_score * 10 + len(shared_topics)
    return score, shared_files, shared_topics


def classify(fork: dict, shared_files: set[str], shared_topics: set[str]) -> str:
    if not shared_files:
        return "TOPIC-ONLY"
    if not shared_topics:
        return "FILE-ONLY"
    if fork["topics"] & LOCAL_ADAPT_WORDS:
        return "LOCAL-ADAPT"
    return "RIVAL"


def build_report(base: str, fork_commits: list[dict], upstream_commits: list[dict],
                 pairs: list[dict], counts: dict[str, int],
                 waived: list[dict]) -> str:
    lines = ["# Intent overlap scan", ""]
    lines.append(f"merge base: {base[:12]}")
    lines.append(
        f"fork commits scanned: {len(fork_commits)}   "
        f"upstream commits scanned: {len(upstream_commits)}"
    )
    summary = ", ".join(f"{kind} {counts[kind]}" for kind in sorted(counts))
    lines.append("pending pairs: " + (summary if pairs else "none"))
    if waived:
        lines.append(f"waived pairs: {len(waived)}")
    lines.append("")

    for kind in ("LOCAL-ADAPT", "RIVAL", "FILE-ONLY", "TOPIC-ONLY"):
        selected = [pair for pair in pairs if pair["kind"] == kind]
        if not selected:
            continue
        lines.append(f"## {kind} ({len(selected)})")
        lines.append("")
        for pair in selected:
            lines.append(
                f"- score {pair['score']:.1f}  fork {pair['fork']['short']} "
                f"vs upstream {pair['upstream']['short']}"
            )
            lines.append(f"  - fork: {pair['fork']['subject']}")
            lines.append(f"  - upstream: {pair['upstream']['subject']}")
            if pair["files"]:
                shown = sorted(pair["files"])[:6]
                more = len(pair["files"]) - len(shown)
                suffix = f" (+{more} more)" if more > 0 else ""
                lines.append(f"  - shared files: {', '.join(shown)}{suffix}")
            if pair["topics"]:
                lines.append(f"  - shared topics: {', '.join(sorted(pair['topics']))}")
            lines.append("")

    if waived:
        lines.append(f"## WAIVED ({len(waived)})")
        lines.append("")
        for pair in waived:
            lines.append(
                f"- {pair['kind']}  fork {pair['fork']['short']} "
                f"vs upstream {pair['upstream']['short']}"
            )
            lines.append(f"  - fork: {pair['fork']['subject']}")
            lines.append(f"  - disposition: {pair['waiver']}")
            lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--target", required=True, help="fork parent SHA")
    parser.add_argument("--source", required=True, help="upstream parent SHA")
    parser.add_argument("--max-commits", type=int, default=400,
                        help="per side scan cap, newest first")
    parser.add_argument("--min-score", type=float, default=5.0,
                        help="report pairs at or above this overlap score")
    parser.add_argument(
        "--kinds",
        default="LOCAL-ADAPT,RIVAL",
        help="comma-separated kinds to keep; default hides incidental collisions",
    )
    parser.add_argument(
        "--waiver-file",
        type=Path,
        default=None,
        help="dispositioned pairs: fork_short<TAB>reason per line",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    base = run(args.repo, "merge-base", args.target, args.source).strip()
    if not base:
        raise SystemExit("no merge base between target and source")

    fork_commits = collect_commits(args.repo, base, args.target, args.max_commits)
    upstream_commits = collect_commits(args.repo, base, args.source, args.max_commits)

    # Index upstream commits by file so pairing stays linear in practice.
    by_file: dict[str, list[int]] = defaultdict(list)
    for idx, commit in enumerate(upstream_commits):
        for path in commit["files"]:
            by_file[path].append(idx)

    # Rarity weight per file: a path both sides touch once is real evidence, a
    # path touched by most commits carries none.
    touch_count: dict[str, int] = defaultdict(int)
    for commit in (*fork_commits, *upstream_commits):
        for path in commit["files"]:
            touch_count[path] += 1
    file_weight = {path: 1.0 / count for path, count in touch_count.items()}

    wanted_kinds = {kind for kind in args.kinds.split(",") if kind}
    pairs = []
    for fork in fork_commits:
        candidates: set[int] = set()
        for path in fork["files"]:
            candidates.update(by_file.get(path, ()))
        for idx in candidates:
            upstream = upstream_commits[idx]
            score, shared_files, shared_topics = score_pair(
                fork, upstream, file_weight
            )
            if score < args.min_score:
                continue
            kind = classify(fork, shared_files, shared_topics)
            if wanted_kinds and kind not in wanted_kinds:
                continue
            pairs.append(
                {
                    "score": score,
                    "kind": kind,
                    "fork": fork,
                    "upstream": upstream,
                    "files": shared_files,
                    "topics": shared_topics,
                }
            )

    pairs.sort(key=lambda item: -item["score"])
    waivers = read_waivers(args.waiver_file)
    for pair in pairs:
        pair["waiver"] = waivers.get(pair["fork"]["short"], "")
    waived = [pair for pair in pairs if pair["waiver"]]
    pairs = [pair for pair in pairs if not pair["waiver"]]
    counts: dict[str, int] = defaultdict(int)
    for pair in pairs:
        counts[pair["kind"]] += 1

    report = build_report(base, fork_commits, upstream_commits, pairs, counts, waived)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(report)

    # Rival and local-adapt pairs need a human decision before the merge is
    # trusted. A waived pair already has one, recorded in the waiver reason.
    return 1 if counts["RIVAL"] or counts["LOCAL-ADAPT"] else 0


if __name__ == "__main__":
    sys.exit(main())
