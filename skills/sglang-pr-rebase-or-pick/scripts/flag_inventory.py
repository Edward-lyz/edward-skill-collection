#!/usr/bin/env python3
"""Diff a config dataclass (feature switches) across a merge and its parents.

A merge can silently drop a flag that only one parent declared, or keep the flag
while taking the other parent default. Neither shows up as a conflict, and both
change what the delivered service does. This compares the fields of one dataclass
at three revisions.

Reported categories:

    DROPPED       declared by a parent, absent in the merged tree -> blocker,
                  a feature switch was lost
    DEFAULT-DRIFT kept, but the merged default differs from the owning parent
                  -> blocker unless the change is intentional
    NO-OP         kept and still declared, but every file that read it is gone
                  -> blocker, the switch silently does nothing now
    DEAD          no reader in either tree; pre-existing, reported once so a
                  deployment can stop passing it
    FORK-ONLY     declared only by the target/fork parent; these are the local
                  switches whose gated paths need explicit verification
    UPSTREAM-NEW  declared only by the source/upstream parent
"""
from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from pathlib import Path
from typing import Optional

MISSING = "<dropped>"


def read_waivers(path: Optional[Path]) -> dict[str, str]:
    """`name<TAB>reason` per line. A waiver without a reason is not accepted."""
    waivers: dict[str, str] = {}
    if path is None or not path.exists():
        return waivers
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, _, reason = line.partition("\t")
        if reason.strip():
            waivers[name.strip()] = reason.strip()
    return waivers


def find_readers(
    repo: Path,
    rev: Optional[str],
    names: list[str],
    declaring_file: str,
    spans: dict[str, tuple[int, int]],
) -> dict[str, set[str]]:
    """Flag name -> files mentioning it, ignoring its own declaration.

    One fixed-string `git grep -n` for every name at once, then attribute each
    matched line to the names it contains. Per-name greps, or re-reading every
    matched file, are both too slow to run as a routine gate.
    """
    command = ["git", "-C", str(repo), "grep", "-n", "-F"]
    for name in names:
        command += ["-e", name]
    if rev is not None:
        command.append(rev)
    command += ["--", "*.py"]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    readers: dict[str, set[str]] = {name: set() for name in names}
    prefix_fields = 3 if rev is not None else 2  # rev:path:line vs path:line
    for line in result.stdout.splitlines():
        parts = line.split(":", prefix_fields)
        if len(parts) < prefix_fields + 1:
            continue
        path = parts[1] if rev is not None else parts[0]
        content = parts[prefix_fields]
        try:
            line_no = int(parts[prefix_fields - 1])
        except ValueError:
            continue
        for name in names:
            if name not in content:
                continue
            if path == declaring_file:
                start, end = spans.get(name, (0, 0))
                if start <= line_no <= end:
                    continue
            readers[name].add(path)
    return readers


def read_revision(repo: Path, rev: Optional[str], path: str) -> Optional[str]:
    if rev is None:
        try:
            return (repo / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"{rev}:{path}"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout if result.returncode == 0 else None


def collect_fields(
    source: str, class_name: str
) -> tuple[dict[str, str], dict[str, tuple[int, int]]]:
    """Field name -> default expression, and field name -> declaration line span.

    The span covers the whole annotated assignment, help text included, so a
    reader search can ignore the declaration without ignoring the rest of the
    declaring file: a config class often folds its own legacy fields into a
    newer structure a few thousand lines further down.
    """
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return {}, {}
    fields: dict[str, str] = {}
    spans: dict[str, tuple[int, int]] = {}
    for node in ast.walk(parsed):
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for statement in node.body:
            if not isinstance(statement, ast.AnnAssign):
                continue
            if not isinstance(statement.target, ast.Name):
                continue
            default = "<required>"
            if statement.value is not None:
                default = " ".join(ast.unparse(statement.value).split())
            fields[statement.target.id] = default
            spans[statement.target.id] = (
                statement.lineno,
                statement.end_lineno or statement.lineno,
            )
    return fields, spans


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--file", default="python/sglang/srt/server_args.py")
    parser.add_argument("--class-name", default="ServerArgs")
    parser.add_argument("--target", required=True, help="target/fork parent revision")
    parser.add_argument(
        "--source", required=True, help="source/upstream parent revision"
    )
    parser.add_argument(
        "--final", default=None, help="merged revision; omit to read the working tree"
    )
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--waiver-file",
        type=Path,
        default=None,
        help="dispositioned DROPPED/NO-OP flags: name<TAB>reason per line",
    )
    parser.add_argument(
        "--consumer-parity",
        action="store_true",
        help="also check whether each kept flag still has a reader",
    )
    parser.add_argument(
        "--parity-scope",
        choices=["fork-only", "all"],
        default="fork-only",
        help="which kept flags to check readers for; all is slow on a big tree",
    )
    args = parser.parse_args()

    revisions = (
        ("target", args.target),
        ("source", args.source),
        ("final", args.final),
    )
    trees: dict[str, dict[str, str]] = {}
    spans: dict[str, dict[str, tuple[int, int]]] = {}
    for label, rev in revisions:
        text = read_revision(args.repo, rev, args.file)
        if text is None:
            print(f"cannot read {args.file} at {label} ({rev})", file=sys.stderr)
            return 2
        trees[label], spans[label] = collect_fields(text, args.class_name)
        if not trees[label]:
            print(f"no fields found for {args.class_name} at {label}", file=sys.stderr)
            return 2

    target, source, final = trees["target"], trees["source"], trees["final"]
    dropped = sorted((set(target) | set(source)) - set(final))
    fork_only = sorted(set(target) - set(source))
    upstream_new = sorted(set(source) - set(target))
    drift: list[tuple[str, str, str, str]] = []
    for name in sorted(set(final)):
        owners = [label for label in ("target", "source") if name in trees[label]]
        if not owners:
            continue
        parent_defaults = {trees[label][name] for label in owners}
        if len(parent_defaults) > 1:
            # Parents disagree: the merged choice is a decision, not a drift.
            continue
        parent_default = parent_defaults.pop()
        if final[name] != parent_default:
            drift.append((name, parent_default, final[name], "/".join(owners)))

    final_label = args.final or "working tree"
    waivers = read_waivers(args.waiver_file)
    waived = [(name, waivers[name]) for name in dropped + [] if name in waivers]
    noop: list[str] = []
    dead: list[str] = []
    if args.consumer_parity:
        kept = set(final) & (set(target) | set(source))
        if args.parity_scope == "fork-only":
            kept &= set(fork_only)
        shared = sorted(kept)
        parent_rev = args.target
        parent_readers = find_readers(
            args.repo, parent_rev, shared, args.file, spans["target"]
        )
        source_readers = find_readers(
            args.repo, args.source, shared, args.file, spans["source"]
        )
        final_readers = find_readers(
            args.repo, args.final, shared, args.file, spans["final"]
        )
        for name in shared:
            before = parent_readers[name] | source_readers[name]
            after = final_readers[name]
            if not before and not after:
                dead.append(name)
            elif before and not after:
                noop.append(name)
    report: list[str] = [
        f"# Flag inventory: {args.class_name} in {args.file}",
        "",
        f"target={args.target}  source={args.source}  final={final_label}",
        f"fields: target={len(target)} source={len(source)} final={len(final)}",
        "",
        f"## DROPPED ({len(dropped)})",
    ]
    report += [f"- {name}" for name in dropped] or ["- none"]
    report += ["", f"## DEFAULT-DRIFT ({len(drift)})"]
    report += [
        f"- {name}: {parent} -> {merged} (declared by {owners})"
        for name, parent, merged, owners in drift
    ] or ["- none"]
    report += ["", f"## FORK-ONLY ({len(fork_only)})"]
    report += [f"- {name} = {final.get(name, MISSING)}" for name in fork_only]
    report += ["", f"## UPSTREAM-NEW ({len(upstream_new)})"]
    report += [f"- {name} = {final.get(name, MISSING)}" for name in upstream_new]
    if args.consumer_parity:
        report += ["", f"## NO-OP ({len(noop)})"]
        report += [f"- {name}" for name in noop] or ["- none"]
        report += ["", f"## DEAD ({len(dead)})"]
        report += [f"- {name}" for name in dead] or ["- none"]
    unwaived_dropped = [name for name in dropped if name not in waivers]
    unwaived_noop = [name for name in noop if name not in waivers]
    waived += [(name, waivers[name]) for name in noop if name in waivers]
    report += ["", f"## WAIVED ({len(waived)})"]
    report += [f"- {name}: {reason}" for name, reason in waived] or ["- none"]
    text = "\n".join(report) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 1 if unwaived_dropped or drift or unwaived_noop else 0


if __name__ == "__main__":
    sys.exit(main())
