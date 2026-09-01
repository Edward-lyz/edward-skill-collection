#!/usr/bin/env python3
"""Classify interface_delta HIGH rows that say a public symbol is absent.

"Absent from the final tree" is a name lookup, not a capability check. On a big
merge most rows are benign, and re-deciding them by hand every run does not
scale. This applies the documented disposition order mechanically:

    MOVED           the same name still exists somewhere in the merged tree
    DEAD-IN-PARENT  the owning parent had no caller either, so it was dead code
    RENAMED-TWIN    a merged definition carries the same distinctive comment or
                    docstring line, i.e. upstream renamed it
    REAL-LOSS       none of the above; needs a human and probably M7 handling

Exit code is non-zero only when a REAL-LOSS row remains.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

ROW = re.compile(
    r"^\|\s*`(?P<prio>[A-Z]+)`\s*\|\s*`(?P<origin>[a-z]+)`\s*"
    r"\|\s*`(?P<path>[^`]+)`\s*\|\s*`(?P<kind>[a-z]+)`\s*"
    r"\|\s*`(?P<symbol>[^`]+)`\s*\|\s*(?P<detail>[^|]+)\|"
)
ABSENT = "absent from final"


@dataclass
class Row:
    origin: str
    path: str
    kind: str
    symbol: str

    @property
    def leaf(self) -> str:
        return self.symbol.rsplit(".", 1)[-1]


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], check=False, capture_output=True, text=True
    )
    return result.stdout


def grep_names(
    repo: Path, rev: Optional[str], names: list[str]
) -> dict[str, set[str]]:
    """Name -> files containing it as a word. One grep for the whole batch."""
    hits: dict[str, set[str]] = {name: set() for name in names}
    if not names:
        return hits
    args = ["grep", "-n", "-w"]
    for name in names:
        args += ["-e", name]
    if rev is not None:
        args.append(rev)
    args += ["--", "*.py"]
    prefix_fields = 3 if rev is not None else 2
    for line in git(repo, *args).splitlines():
        parts = line.split(":", prefix_fields)
        if len(parts) < prefix_fields + 1:
            continue
        path = parts[1] if rev is not None else parts[0]
        content = parts[prefix_fields]
        for name in names:
            if re.search(rf"\b{re.escape(name)}\b", content):
                hits[name].add(path)
    return hits


def definition_marker(repo: Path, rev: str, path: str, leaf: str) -> Optional[str]:
    """A distinctive comment/docstring line from the parent definition.

    Upstream renames usually copy the explanation verbatim, so the comment is a
    better fingerprint than the name.
    """
    source = git(repo, "show", f"{rev}:{path}")
    if not source:
        return None
    lines = source.splitlines()
    for index, line in enumerate(lines):
        if not re.search(rf"(def|class)\s+{re.escape(leaf)}\b", line):
            continue
        for candidate in lines[index + 1 : index + 12]:
            text = candidate.strip().lstrip("#").strip().strip('"').strip()
            if len(text) >= 30 and not text.startswith(("return", "self.", "if ")):
                return text
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument(
        "--report", required=True, type=Path, help="interface_delta output"
    )
    parser.add_argument(
        "--target", required=True, help="target/fork parent revision"
    )
    parser.add_argument(
        "--source", required=True, help="source/upstream parent revision"
    )
    parser.add_argument(
        "--final", default=None, help="merged revision; omit for working tree"
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    rows: list[Row] = []
    for line in args.report.read_text(encoding="utf-8").splitlines():
        match = ROW.match(line.strip())
        if not match or match.group("prio") != "HIGH":
            continue
        if ABSENT not in match.group("detail"):
            continue
        rows.append(
            Row(
                origin=match.group("origin"),
                path=match.group("path"),
                kind=match.group("kind"),
                symbol=match.group("symbol"),
            )
        )

    parent_of = {"target": args.target, "source": args.source}
    leaves = sorted({row.leaf for row in rows if row.kind != "file"})
    final_hits = grep_names(args.repo, args.final, leaves)
    parent_hits = {
        label: grep_names(args.repo, rev, leaves) for label, rev in parent_of.items()
    }

    verdicts: list[tuple[str, Row, str]] = []
    for row in rows:
        if row.kind == "file":
            basename = Path(row.path).name
            same_name = grep_names(args.repo, args.final, [Path(basename).stem])
            note = ", ".join(sorted(same_name[Path(basename).stem])[:2]) or "-"
            verdict = "MOVED" if same_name[Path(basename).stem] else "REAL-LOSS"
            verdicts.append((verdict, row, note))
            continue
        found = final_hits[row.leaf]
        if found:
            verdicts.append(("MOVED", row, ", ".join(sorted(found)[:2])))
            continue
        owner_rev = parent_of.get(row.origin, args.target)
        owner_files = parent_hits.get(row.origin, {}).get(row.leaf, set())
        if owner_files <= {row.path}:
            verdicts.append(
                ("DEAD-IN-PARENT", row, "no caller in the owning parent")
            )
            continue
        marker = definition_marker(args.repo, owner_rev, row.path, row.leaf)
        twin = ""
        if marker:
            args_grep = ["grep", "-n", "-F", marker]
            if args.final is not None:
                args_grep.append(args.final)
            args_grep += ["--", "*.py"]
            hits = git(args.repo, *args_grep).splitlines()
            twin = hits[0].split(":", 2)[0] if hits else ""
        if twin:
            verdicts.append(("RENAMED-TWIN", row, f"same comment in {twin}"))
        else:
            verdicts.append(
                ("REAL-LOSS", row, f"callers in parent: {len(owner_files)}")
            )

    order = {"REAL-LOSS": 0, "RENAMED-TWIN": 1, "DEAD-IN-PARENT": 2, "MOVED": 3}
    verdicts.sort(key=lambda item: (order[item[0]], item[1].path, item[1].symbol))
    counts: dict[str, int] = {}
    for verdict, _row, _note in verdicts:
        counts[verdict] = counts.get(verdict, 0) + 1

    report = [
        "# Absent-symbol triage",
        "",
        f"rows: {len(rows)}  "
        + "  ".join(f"{key}={value}" for key, value in sorted(counts.items())),
        "",
        "| verdict | origin | path | symbol | evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    report += [
        f"| {verdict} | {row.origin} | {row.path} | {row.symbol} | {note} |"
        for verdict, row, note in verdicts
    ]
    text = "\n".join(report) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 1 if counts.get("REAL-LOSS") else 0


if __name__ == "__main__":
    sys.exit(main())
