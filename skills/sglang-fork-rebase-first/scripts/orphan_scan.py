#!/usr/bin/env python3
"""Find fork-only modules that the merge left without a caller.

When upstream rewrites a subsystem, the merge usually takes the upstream files
and the fork callers disappear with them. What is left behind are fork-only
modules that still compile, still import cleanly, and are never reached. They
are not defects, they are dead weight that the next merge has to resolve again,
so the honest move is to delete them together with the capability.

Verdicts:

    IN-USE         some other module imports it, or a deployment YAML passes a
                   flag this module reads
    DYNAMIC-MAYBE  no import, but its name appears in a string somewhere: a
                   registry or importlib call may reach it; needs a human
    ORPHAN         no import, no name mention, no deployed flag -> delete

Deployment YAMLs are the safety net: a module that reads a switch the release
configuration actually passes is never reported as an orphan.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

SKIP_DIRS = ("test/", "tests/", "benchmark/", "scripts/", "tools/", "examples/")


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], check=False, capture_output=True, text=True
    )
    return result.stdout


def list_files(repo: Path, rev: Optional[str], root: str) -> set[str]:
    if rev is None:
        out = git(repo, "ls-files", "--", root)
    else:
        out = git(repo, "ls-tree", "-r", "--name-only", rev, "--", root)
    return {line for line in out.splitlines() if line.endswith(".py")}


def module_of(path: str, package_root: str) -> str:
    relative = path[len(package_root) + 1 :] if package_root else path
    parts = relative[: -len(".py")].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def deployment_flags(paths: list[Path]) -> set[str]:
    """Dataclass-style field names for every --flag the deployment passes."""
    pattern = re.compile(r"--([a-z0-9][a-z0-9-]+)")
    fields: set[str] = set()
    for path in paths:
        for flag in pattern.findall(path.read_text(encoding="utf-8")):
            fields.add(flag.replace("-", "_"))
    return fields


def referencing_files(repo: Path, needle: str, own_path: str) -> set[str]:
    found = set()
    for line in git(repo, "grep", "-l", "-F", "-e", needle, "--", "*.py").splitlines():
        if line != own_path:
            found.add(line)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--target", required=True, help="target/fork parent revision")
    parser.add_argument(
        "--source", required=True, help="source/upstream parent revision"
    )
    parser.add_argument(
        "--final", default=None, help="merged revision; omit for working tree"
    )
    parser.add_argument("--package-root", default="python")
    parser.add_argument(
        "--deploy-yaml",
        action="append",
        default=[],
        type=Path,
        help="release YAML whose flags must keep their modules alive",
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    final_files = list_files(args.repo, args.final, args.package_root)
    target_files = list_files(args.repo, args.target, args.package_root)
    source_files = list_files(args.repo, args.source, args.package_root)
    fork_only = sorted(
        path
        for path in final_files & target_files
        if path not in source_files
        and not any(part in path for part in SKIP_DIRS)
        and not path.endswith("__init__.py")
    )
    flags = deployment_flags(args.deploy_yaml)

    rows: list[tuple[str, str, str]] = []
    for path in fork_only:
        module = module_of(path, args.package_root)
        leaf = module.rsplit(".", 1)[-1]
        importers = referencing_files(args.repo, module, path)
        if importers:
            rows.append(("IN-USE", path, f"imported by {len(importers)} module(s)"))
            continue
        text = (args.repo / path).read_text(encoding="utf-8", errors="replace")
        used_flags = sorted(flag for flag in flags if flag in text)
        if used_flags:
            shown = ", ".join(used_flags[:3])
            rows.append(("IN-USE", path, f"reads deployed flag(s): {shown}"))
            continue
        mentions = referencing_files(args.repo, leaf, path)
        if mentions:
            rows.append(
                ("DYNAMIC-MAYBE", path, f"name appears in {len(mentions)} file(s)")
            )
            continue
        rows.append(("ORPHAN", path, "no importer, no name mention, no deployed flag"))

    order = {"ORPHAN": 0, "DYNAMIC-MAYBE": 1, "IN-USE": 2}
    rows.sort(key=lambda row: (order[row[0]], row[1]))
    counts: dict[str, int] = {}
    for verdict, _path, _note in rows:
        counts[verdict] = counts.get(verdict, 0) + 1

    report = [
        "# Fork-only orphan scan",
        "",
        f"fork-only modules: {len(fork_only)}  "
        + "  ".join(f"{key}={value}" for key, value in sorted(counts.items())),
        f"deployment flags considered: {len(flags)}",
        "",
        "| verdict | path | evidence |",
        "| --- | --- | --- |",
    ]
    report += [f"| {verdict} | {path} | {note} |" for verdict, path, note in rows]
    text = "\n".join(report) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
