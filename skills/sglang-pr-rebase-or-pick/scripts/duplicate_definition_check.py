#!/usr/bin/env python3
"""Find duplicate Python definitions that silently override earlier bodies."""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


class GitError(RuntimeError):
    pass


@dataclass(frozen=True)
class Duplicate:
    path: str
    scope: str
    symbol: str
    lines: tuple[int, ...]
    blocking: bool

    @property
    def key(self) -> tuple[str, str, str]:
        return self.path, self.scope, self.symbol


def verify_revision(repo: Path, revision: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", f"{revision}^{{commit}}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown Git error"
        raise GitError(f"cannot resolve revision {revision!r}: {detail}")


def git_blob(repo: Path, revision: str, path: str) -> str | None:
    listing = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-z", revision, "--", path],
        check=False,
        capture_output=True,
    )
    if listing.returncode != 0:
        detail = listing.stderr.decode(errors="replace").strip() or "unknown Git error"
        raise GitError(f"cannot inspect {revision}:{path}: {detail}")
    if not listing.stdout:
        return None
    result = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-p", f"{revision}:{path}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "unknown Git error"
        raise GitError(f"cannot read {revision}:{path}: {detail}")
    return result.stdout


def changed_python_paths(repo: Path, base: str, final: str) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            f"{base}..{final}",
            "--",
            "*.py",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(set(result.stdout.splitlines()))


def decorator_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        owner = decorator_name(node.value)
        return f"{owner}.{node.attr}" if owner else ""
    if isinstance(node, ast.Call):
        return decorator_name(node.func)
    return ""


def intentional_definition_group(
    symbol: str,
    nodes: list[ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef],
) -> bool:
    if not all(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in nodes
    ):
        return False
    decorators = [
        {decorator_name(decorator) for decorator in node.decorator_list}
        for node in nodes
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    overload_group = all(
        any(name.rsplit(".", 1)[-1] == "overload" for name in names)
        for names in decorators[:-1]
    ) and not any(name.rsplit(".", 1)[-1] == "overload" for name in decorators[-1])
    accessors = {f"{symbol}.setter", f"{symbol}.getter", f"{symbol}.deleter"}
    property_group = "property" in decorators[0] and all(
        bool(names & accessors) for names in decorators[1:]
    )
    registration_group = all(
        any(name.endswith(".register") for name in names) for names in decorators
    )
    return overload_group or property_group or registration_group


def is_test_path(path: str) -> bool:
    parsed = PurePosixPath(path)
    filename = parsed.name
    return (
        any(part in {"test", "tests"} for part in parsed.parts[:-1])
        or filename.startswith("test_")
        or filename.endswith("_test.py")
        or filename == "conftest.py"
    )


def collect_duplicates(text: str, path: str) -> list[Duplicate]:
    tree = ast.parse(text)
    duplicates: list[Duplicate] = []

    def visit_scope(statements: list[ast.stmt], scope: str) -> None:
        definitions: dict[
            str, list[ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef]
        ] = {}
        for statement in statements:
            if isinstance(
                statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                definitions.setdefault(statement.name, []).append(statement)
        for symbol, nodes in definitions.items():
            if len(nodes) < 2 or intentional_definition_group(symbol, nodes):
                continue
            duplicates.append(
                Duplicate(
                    path=path,
                    scope=scope,
                    symbol=symbol,
                    lines=tuple(node.lineno for node in nodes),
                    blocking=not is_test_path(path),
                )
            )
        for statement in statements:
            if isinstance(statement, ast.ClassDef):
                child_scope = (
                    statement.name
                    if scope == "<module>"
                    else f"{scope}.{statement.name}"
                )
                visit_scope(statement.body, child_scope)

    visit_scope(tree.body, "<module>")
    return duplicates


def resolve_nodes(tree: ast.Module, symbol: str) -> list[ast.AST]:
    parts = [part for part in symbol.split(".") if part]
    statements = tree.body
    nodes: list[ast.AST] = []
    for index, part in enumerate(parts):
        nodes = [
            statement
            for statement in statements
            if isinstance(
                statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            )
            and statement.name == part
        ]
        if not nodes:
            return []
        if index == len(parts) - 1:
            return nodes
        owner = nodes[-1]
        if not isinstance(owner, ast.ClassDef):
            return []
        statements = owner.body
    return nodes


def anchor_exists(repo: Path, final: str, anchor: str) -> bool:
    path, separator, symbol = anchor.partition(":")
    if not separator or not path or not symbol:
        return False
    text = git_blob(repo, final, path)
    if text is None:
        return False
    try:
        tree = ast.parse(text, filename=f"{final}:{path}")
    except SyntaxError:
        return False
    return bool(resolve_nodes(tree, symbol))


def read_waivers(
    repo: Path, final: str, path: Path | None
) -> set[tuple[str, str, str]]:
    waivers: set[tuple[str, str, str]] = set()
    if path is None or not path.exists():
        return waivers
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        columns = line.split("\t")
        if len(columns) < 6:
            raise ValueError(
                f"invalid waiver at {path}:{line_number}; expected path, scope, "
                "symbol, disposition, final-anchor, reason"
            )
        issue_path, scope, symbol, disposition, anchor, reason = columns[:6]
        if disposition != "intentional-override":
            raise ValueError(
                f"invalid waiver at {path}:{line_number}; "
                "disposition must be intentional-override"
            )
        if not anchor_exists(repo, final, anchor):
            raise ValueError(
                f"invalid waiver at {path}:{line_number}; final anchor does not resolve"
            )
        if not reason.strip():
            raise ValueError(f"invalid waiver at {path}:{line_number}; reason is empty")
        waivers.add((issue_path, scope, symbol))
    return waivers


def render_report(
    duplicates: list[Duplicate],
    introduced: set[tuple[str, str, str]],
    waivers: set[tuple[str, str, str]],
    paths: list[str],
    ignored: list[str],
) -> str:
    unwaived = [
        duplicate
        for duplicate in duplicates
        if duplicate.key in introduced
        and duplicate.blocking
        and duplicate.key not in waivers
    ]
    lines = [
        "# Duplicate Definition Check",
        "",
        f"- Paths scanned: {len(paths)}",
        f"- Unsupported paths ignored: {len(ignored)}",
        f"- Final duplicate groups: {len(duplicates)}",
        f"- New or increased groups: {len(introduced)}",
        f"- Unwaived blockers: {len(unwaived)}",
        "",
        "| Status | Path | Scope | Symbol | Lines |",
        "|---|---|---|---|---|",
    ]
    for duplicate in duplicates:
        if duplicate.key not in introduced:
            status = "PREEXISTING"
        elif duplicate.key in waivers:
            status = "WAIVED"
        else:
            status = "BLOCKER" if duplicate.blocking else "REVIEW"
        line_list = ", ".join(str(line) for line in duplicate.lines)
        lines.append(
            f"| {status} | `{duplicate.path}` | `{duplicate.scope}` | "
            f"`{duplicate.symbol}` | {line_list} |"
        )
    if not duplicates:
        lines.append("| PASS | - | - | - | No duplicate definitions found. |")
    if ignored:
        lines.extend(
            [
                "",
                "Ignored non-Python paths require a language-native duplicate "
                "or symbol gate:",
                "",
                *[f"- `{path}`" for path in ignored],
            ]
        )
    return "\n".join(lines) + "\n"


def read_paths(path: Path) -> tuple[list[str], list[str]]:
    requested = sorted(
        {line.strip() for line in path.read_text().splitlines() if line.strip()}
    )
    python_paths = [item for item in requested if item.endswith(".py")]
    ignored = [item for item in requested if not item.endswith(".py")]
    return python_paths, ignored


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", required=True)
    parser.add_argument("--final", required=True)
    parser.add_argument("--paths-file", type=Path)
    parser.add_argument("--waiver-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    verify_revision(args.repo, args.base)
    verify_revision(args.repo, args.final)

    if args.paths_file is not None:
        paths, ignored = read_paths(args.paths_file)
    else:
        paths = changed_python_paths(args.repo, args.base, args.final)
        ignored = []
    if not paths and ignored:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_report([], set(), set(), paths, ignored))
        raise ValueError(
            "no Python paths to inspect; use a language-native gate for the "
            "requested paths"
        )

    base_duplicates: list[Duplicate] = []
    final_duplicates: list[Duplicate] = []
    for path in paths:
        for revision, destination in (
            (args.base, base_duplicates),
            (args.final, final_duplicates),
        ):
            text = git_blob(args.repo, revision, path)
            if text is None:
                continue
            try:
                destination.extend(collect_duplicates(text, path))
            except SyntaxError as error:
                raise ValueError(f"cannot parse {revision}:{path}: {error}") from error

    base_counts = {duplicate.key: len(duplicate.lines) for duplicate in base_duplicates}
    introduced = {
        duplicate.key
        for duplicate in final_duplicates
        if len(duplicate.lines) > base_counts.get(duplicate.key, 1)
    }

    waivers = read_waivers(args.repo, args.final, args.waiver_file)
    unused_waivers = waivers - introduced
    if unused_waivers:
        formatted = ", ".join(":".join(key) for key in sorted(unused_waivers))
        raise ValueError(
            f"waivers do not match a new or increased duplicate: {formatted}"
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        render_report(final_duplicates, introduced, waivers, paths, ignored)
    )
    unwaived = [
        duplicate
        for duplicate in final_duplicates
        if duplicate.key in introduced
        and duplicate.blocking
        and duplicate.key not in waivers
    ]
    print(
        f"scanned={len(paths)} duplicates={len(final_duplicates)} "
        f"introduced={len(introduced)} "
        f"unwaived={len(unwaived)} output={args.output}"
    )
    return 1 if unwaived else 0


if __name__ == "__main__":
    try:
        exit_code = main()
    except (GitError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        exit_code = 2
    raise SystemExit(exit_code)
