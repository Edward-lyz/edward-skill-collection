#!/usr/bin/env python3
"""Flag merged lines that exist in no parent and no ledger source.

A merge is not allowed to invent logic. Every line the final tree adds over
the fork parent must be traceable to the upstream parent, to the fork parent
itself (moved code), or to a declared ledger source branch (features replayed
from other fork lines). Lines with no provenance were written during the
merge; hunks of them on numeric paths are exactly how silent accuracy
regressions enter.

Matching is per normalized line, so single common lines ("return None")
match spuriously; the unit of review is the unmatched hunk, not the line.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_HIGH_RISK_PREFIXES = (
    "python/sglang/srt/layers/",
    "python/sglang/srt/mem_cache/",
    "sgl-kernel/",
)

# Structural noise: bare keywords and brackets carry no provenance signal.
TRIVIAL_LINES = {
    "else:", "try:", "finally:", "pass", "break", "continue", "return",
    "return None", "raise", ")", "):", "]", "}", "(", "[", "{", "},", "],",
    "),", '"""', "'''",
}

WHITESPACE_RUN = re.compile(r"\s+")


class GitError(RuntimeError):
    pass


@dataclass
class Hunk:
    path: str
    start: int
    lines: list[str]

    @property
    def end(self) -> int:
        return self.start + len(self.lines) - 1


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        errors="replace",
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "unknown Git error"
        raise GitError(f"git {' '.join(args[:3])}...: {detail}")
    return result.stdout


def verify_revision(repo: Path, revision: str) -> str:
    return run_git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}").strip()


def normalize(line: str) -> str | None:
    """Return the corpus key for a line, or None if it carries no signal."""
    text = WHITESPACE_RUN.sub(" ", line.strip())
    if len(text) < 8 or text in TRIVIAL_LINES:
        return None
    return text


def corpus_lines(repo: Path, revision: str, pathspec: str) -> set[str]:
    """Every normalized line of every matching file at revision."""
    result = subprocess.run(
        ["git", "-C", str(repo), "grep", "-h", "-I", "-e", "", revision, "--", pathspec],
        check=False,
        capture_output=True,
        text=True,
        errors="replace",
    )
    # git grep exits 1 when nothing matches; only >1 is an error.
    if result.returncode > 1:
        raise GitError(f"git grep at {revision}: {result.stderr.strip()}")
    lines = set()
    for raw in result.stdout.splitlines():
        key = normalize(raw)
        if key is not None:
            lines.add(key)
    return lines


def added_lines(
    repo: Path, target: str, final: str, pathspec: str
) -> list[tuple[str, int, str]]:
    """(path, final lineno, text) for every line final adds over target."""
    out = run_git(
        repo, "diff", "--no-color", "-U0", "--diff-filter=ACMR",
        target, final, "--", pathspec,
    )
    added: list[tuple[str, int, str]] = []
    path = ""
    lineno = 0
    for raw in out.splitlines():
        if raw.startswith("+++ b/"):
            path = raw[6:]
        elif raw.startswith("@@"):
            match = re.search(r"\+(\d+)", raw)
            lineno = int(match.group(1)) if match else 0
        elif raw.startswith("+") and not raw.startswith("+++"):
            added.append((path, lineno, raw[1:]))
            lineno += 1
    return added


def group_hunks(unmatched: list[tuple[str, int, str]]) -> list[Hunk]:
    hunks: list[Hunk] = []
    for path, lineno, text in unmatched:
        last = hunks[-1] if hunks else None
        if last is not None and last.path == path and lineno <= last.end + 2:
            last.lines.append(text)
        else:
            hunks.append(Hunk(path=path, start=lineno, lines=[text]))
    return hunks


def load_waivers(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    waivers = {}
    for raw in path.read_text().splitlines():
        if "\t" not in raw:
            continue
        name, reason = raw.split("\t", 1)
        if name.strip() and reason.strip():
            waivers[name.strip()] = reason.strip()
    return waivers


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--target", required=True, help="frozen fork parent")
    parser.add_argument("--source", required=True, help="frozen upstream parent")
    parser.add_argument("--final", default="HEAD", help="merged revision")
    parser.add_argument(
        "--extra-source", action="append", default=[],
        help="ledger branch replayed features come from; repeatable",
    )
    parser.add_argument("--pathspec", default="*.py")
    parser.add_argument(
        "--high-risk-prefix", action="append", default=[],
        help="path prefixes that block on unmatched hunks "
             "(default: layers/, mem_cache/, sgl-kernel/)",
    )
    parser.add_argument("--min-hunk-lines", type=int, default=3,
                        help="hunks shorter than this are listed but never block")
    parser.add_argument("--waiver-file", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        target = verify_revision(args.repo, args.target)
        final = verify_revision(args.repo, args.final)
        corpus_refs = [target, verify_revision(args.repo, args.source)]
        corpus_refs += [verify_revision(args.repo, ref) for ref in args.extra_source]

        corpus: set[str] = set()
        for ref in corpus_refs:
            corpus |= corpus_lines(args.repo, ref, args.pathspec)
        additions = added_lines(args.repo, target, final, args.pathspec)
    except GitError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    unmatched = []
    signal_total = 0
    for path, lineno, text in additions:
        key = normalize(text)
        if key is None:
            continue
        signal_total += 1
        if key not in corpus:
            unmatched.append((path, lineno, text))

    hunks = group_hunks(unmatched)
    high_prefixes = tuple(args.high_risk_prefix) or DEFAULT_HIGH_RISK_PREFIXES
    waivers = load_waivers(args.waiver_file)

    blockers: list[Hunk] = []
    waived: list[tuple[Hunk, str]] = []
    advisory: list[Hunk] = []
    for hunk in hunks:
        is_high = hunk.path.startswith(high_prefixes)
        if is_high and len(hunk.lines) >= args.min_hunk_lines:
            reason = waivers.get(hunk.path)
            if reason is None:
                blockers.append(hunk)
            else:
                waived.append((hunk, reason))
        else:
            advisory.append(hunk)

    lines = ["# Provenance audit", ""]
    lines.append(f"- final `{final[:12]}` vs fork parent `{target[:12]}`")
    lines.append(f"- corpus: {len(corpus_refs)} refs, {len(corpus)} distinct lines")
    lines.append(
        f"- added lines with signal: {signal_total}; "
        f"unmatched: {len(unmatched)} in {len(hunks)} hunks / "
        f"{len({h.path for h in hunks})} files"
    )
    lines.append("")

    def render(title: str, group: list[Hunk], preview: int) -> None:
        lines.append(f"## {title} ({len(group)} hunks)")
        lines.append("")
        by_file: dict[str, list[Hunk]] = {}
        for hunk in group:
            by_file.setdefault(hunk.path, []).append(hunk)
        for path, file_hunks in sorted(
            by_file.items(), key=lambda kv: -sum(len(h.lines) for h in kv[1])
        ):
            total = sum(len(h.lines) for h in file_hunks)
            lines.append(f"### {path} - {total} lines / {len(file_hunks)} hunks")
            for hunk in file_hunks[:preview]:
                first = hunk.lines[0].strip()
                lines.append(
                    f"- L{hunk.start}-L{hunk.end} ({len(hunk.lines)}): `{first[:96]}`"
                )
            if len(file_hunks) > preview:
                lines.append(f"- ... {len(file_hunks) - preview} more hunks")
            lines.append("")

    if blockers:
        render("BLOCKER: unmatched hunks on high-risk paths", blockers, preview=8)
    if waived:
        lines.append(f"## Waived ({len(waived)} hunks)")
        lines.append("")
        for hunk, reason in waived:
            lines.append(f"- {hunk.path} L{hunk.start}-L{hunk.end}: {reason}")
        lines.append("")
    if advisory:
        render("Advisory: unmatched hunks elsewhere", advisory, preview=3)

    lines.append(
        "Unmatched means the hunk exists in no parent and no ledger source: it "
        "was written during the merge. Glue must be dispositioned per hunk "
        "(waiver file, path<TAB>reason); behavioral additions do not belong "
        "in a merge and go to their own change with numeric validation."
    )
    report = "\n".join(lines) + "\n"
    if args.output:
        args.output.write_text(report)
        print(f"wrote {args.output}")
    else:
        print(report)
    print(f"blockers={len(blockers)} waived={len(waived)} advisory={len(advisory)}")
    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())

