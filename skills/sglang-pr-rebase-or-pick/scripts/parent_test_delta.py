#!/usr/bin/env python3
"""Classify merged-tree test failures against both merge parents.

A structural merge can apply cleanly and still leave a caller paired with the
other parent's callee. Signature retrieval misses the cases where arity still
matches, where the call goes through a variable, or where only an exception type
or an accepted argument shape changed. Running the merged tree's own tests finds
them, but only if inherited failures are separated from merge-introduced ones.

This gate runs a caller-supplied test command in the final tree and in a detached
worktree of each parent, then reports which failures are new to the merge.
Exit code 1 means at least one merge-introduced failure.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_FAIL_PATTERN = r"^(?:FAILED|ERROR)\s+(\S+)"
TREE_PLACEHOLDER = "{tree}"


class GitError(RuntimeError):
    pass


@dataclass
class Run:
    role: str
    revision: str
    tree: Path
    exit_code: int = 0
    failures: set[str] = field(default_factory=set)
    collected: set[str] | None = None
    log: Path | None = None


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown Git error"
        raise GitError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def resolve(repo: Path, revision: str) -> str:
    return git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}").strip()


def run_command(template: str, tree: Path, log: Path) -> tuple[int, str]:
    """Run one shell command with TREE_PLACEHOLDER bound to the checkout path."""
    command = template.replace(TREE_PLACEHOLDER, str(tree))
    result = subprocess.run(
        command,
        shell=True,
        cwd=str(tree),
        check=False,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    log.write_text(f"$ {command}\n\n{output}")
    return result.returncode, output


def parse_ids(output: str, pattern: re.Pattern[str]) -> set[str]:
    found: set[str] = set()
    for line in output.splitlines():
        match = pattern.match(line.strip())
        if match:
            found.add(match.group(1))
    return found


def classify(final: Run, parents: list[Run]) -> dict[str, list[str]]:
    parent_failures = set().union(*(p.failures for p in parents)) if parents else set()
    parent_collected: set[str] = set()
    have_collected = all(p.collected is not None for p in parents)
    if have_collected:
        parent_collected = set().union(*(p.collected or set() for p in parents))

    introduced: list[str] = []
    unknown: list[str] = []
    for test in sorted(final.failures - parent_failures):
        # A test absent from both parents cannot prove the merge broke it.
        if have_collected and test not in parent_collected:
            unknown.append(test)
        else:
            introduced.append(test)

    return {
        "merge-introduced": introduced,
        "new-test-unknown-provenance": unknown,
        "inherited": sorted(final.failures & parent_failures),
        "fixed-by-merge": sorted(parent_failures - final.failures),
    }


def render(final: Run, parents: list[Run], buckets: dict[str, list[str]]) -> str:
    out: list[str] = ["# Parent-relative test delta", ""]
    out.append("| role | revision | exit | failures | collected |")
    out.append("|---|---|---|---|---|")
    for run in [final, *parents]:
        collected = "-" if run.collected is None else str(len(run.collected))
        out.append(
            f"| {run.role} | {run.revision[:12]} | {run.exit_code} | "
            f"{len(run.failures)} | {collected} |"
        )
    out.append("")
    for name in (
        "merge-introduced",
        "new-test-unknown-provenance",
        "inherited",
        "fixed-by-merge",
    ):
        tests = buckets[name]
        out.append(f"## {name} ({len(tests)})")
        out.append("")
        if tests:
            out.extend(f"- `{test}`" for test in tests)
        else:
            out.append("none")
        out.append("")
    out.append(
        "A `merge-introduced` entry is a blocker: the merged tree fails a test that "
        "at least one parent passes. `new-test-unknown-provenance` needs manual "
        "review because the test does not exist on either parent. `inherited` stays "
        "out of scope unless the user widens it."
    )
    out.append("")
    for run in [final, *parents]:
        if run.log is not None:
            out.append(f"- {run.role} log: `{run.log}`")
    out.append("")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--final", default="HEAD")
    parser.add_argument("--target", required=True, help="target-side merge parent")
    parser.add_argument("--source", required=True, help="source-side merge parent")
    parser.add_argument(
        "--test-command",
        required=True,
        help=f"shell command run in each tree; {TREE_PLACEHOLDER} expands to its path",
    )
    parser.add_argument(
        "--collect-command",
        help="optional listing command; enables new-test provenance separation",
    )
    parser.add_argument("--fail-pattern", default=DEFAULT_FAIL_PATTERN)
    parser.add_argument("--collect-pattern", default=r"^(\S+::\S+)")
    parser.add_argument("--log-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo.resolve()
    fail_pattern = re.compile(args.fail_pattern)
    collect_pattern = re.compile(args.collect_pattern)
    args.log_dir.mkdir(parents=True, exist_ok=True)

    roles = [
        ("final", args.final),
        ("target-parent", args.target),
        ("source-parent", args.source),
    ]
    revisions = {role: resolve(repo, rev) for role, rev in roles}

    runs: list[Run] = []
    worktrees: list[Path] = []
    try:
        with tempfile.TemporaryDirectory(prefix="parent-test-delta-") as scratch:
            for role, revision in revisions.items():
                if role == "final":
                    tree = repo
                else:
                    tree = Path(scratch) / role
                    git(repo, "worktree", "add", "--detach", str(tree), revision)
                    worktrees.append(tree)
                run = Run(role=role, revision=revision, tree=tree)
                run.log = args.log_dir / f"{role}-test.log"
                run.exit_code, output = run_command(args.test_command, tree, run.log)
                run.failures = parse_ids(output, fail_pattern)
                if args.collect_command:
                    collect_log = args.log_dir / f"{role}-collect.log"
                    _, collected_output = run_command(
                        args.collect_command, tree, collect_log
                    )
                    run.collected = parse_ids(collected_output, collect_pattern)
                runs.append(run)
    finally:
        for tree in worktrees:
            subprocess.run(
                ["git", "-C", str(repo), "worktree", "remove", "--force", str(tree)],
                check=False,
                capture_output=True,
            )

    final = next(run for run in runs if run.role == "final")
    parents = [run for run in runs if run.role != "final"]
    buckets = classify(final, parents)
    args.output.write_text(render(final, parents, buckets))

    print(f"wrote {args.output}")
    for name, tests in buckets.items():
        print(f"{name}: {len(tests)}")
    return 1 if buckets["merge-introduced"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GitError as error:
        print(f"parent_test_delta: {error}", file=sys.stderr)
        raise SystemExit(2) from error
