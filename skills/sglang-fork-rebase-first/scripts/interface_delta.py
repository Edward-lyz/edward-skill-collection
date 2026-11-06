#!/usr/bin/env python3
"""Retrieve generic Python interface differences from both parents to a merge tree."""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROUTE_METHODS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "options",
    "head",
    "route",
    "api_route",
    "websocket",
}


class GitError(RuntimeError):
    pass


@dataclass(frozen=True)
class Candidate:
    priority: str
    origin: str
    path: str
    kind: str
    symbol: str
    detail: str


@dataclass
class Surface:
    symbols: dict[str, str]
    parameters: dict[str, dict[str, bool]]
    routes: set[tuple[str, str, str]]
    call_keywords: set[tuple[str, str, str]]


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


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        owner = dotted_name(node.value)
        return f"{owner}.{node.attr}" if owner else None
    return None


def argument_requirements(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, bool]:
    args = node.args
    positional = args.posonlyargs + args.args
    first_default = len(positional) - len(args.defaults)
    requirements = {
        argument.arg: index < first_default for index, argument in enumerate(positional)
    }
    requirements.update(
        {
            argument.arg: default is None
            # kwonlyargs and kw_defaults are the same length by construction.
            for argument, default in zip(args.kwonlyargs, args.kw_defaults, strict=True)
        }
    )
    if args.vararg is not None:
        requirements[f"*{args.vararg.arg}"] = False
    if args.kwarg is not None:
        requirements[f"**{args.kwarg.arg}"] = False
    return requirements


def decorator_routes(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        name = dotted_name(decorator.func)
        if name is None or name.rsplit(".", 1)[-1] not in ROUTE_METHODS:
            continue
        for argument in decorator.args:
            if (
                isinstance(argument, ast.Constant)
                and isinstance(argument.value, str)
                and argument.value.startswith("/")
            ):
                routes.add((name, argument.value))
    return routes


def public_symbol(symbol: str) -> bool:
    leaf = symbol.rsplit(".", 1)[-1]
    return leaf == "__init__" or not leaf.startswith("_")


def parse_surface(text: str, label: str) -> Surface:
    tree = ast.parse(text, filename=label)
    symbols: dict[str, str] = {}
    parameters: dict[str, dict[str, bool]] = {}
    routes: set[tuple[str, str, str]] = set()
    call_keywords: set[tuple[str, str, str]] = set()

    class DirectCallVisitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            callee = dotted_name(node.func)
            if callee is not None:
                for keyword in node.keywords:
                    if keyword.arg is not None:
                        call_keywords.add((current_symbol, callee, keyword.arg))
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            return

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            return

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            return

        def visit_Lambda(self, node: ast.Lambda) -> None:
            return

    def visit(statements: list[ast.stmt], prefix: str = "") -> None:
        nonlocal current_symbol
        for statement in statements:
            if isinstance(statement, ast.ClassDef):
                symbol = f"{prefix}.{statement.name}" if prefix else statement.name
                symbols[symbol] = "class"
                visit(statement.body, symbol)
            elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbol = f"{prefix}.{statement.name}" if prefix else statement.name
                symbols[symbol] = "function"
                parameters[symbol] = argument_requirements(statement)
                routes.update(
                    (symbol, decorator, route)
                    for decorator, route in decorator_routes(statement)
                )
                current_symbol = symbol
                visitor = DirectCallVisitor()
                for body_statement in statement.body:
                    visitor.visit(body_statement)

    current_symbol = ""
    visit(tree.body)
    return Surface(symbols, parameters, routes, call_keywords)


def compare(
    repo: Path, origin: str, reference: str, final: str, path: str
) -> list[Candidate]:
    reference_text = git_blob(repo, reference, path)
    if reference_text is None:
        return []
    final_text = git_blob(repo, final, path)
    if final_text is None:
        return [
            Candidate(
                "HIGH",
                origin,
                path,
                "file",
                path,
                "reference file is absent from final tree",
            )
        ]

    reference_surface = parse_surface(reference_text, f"{reference}:{path}")
    final_surface = parse_surface(final_text, f"{final}:{path}")
    candidates: list[Candidate] = []

    for symbol, kind in reference_surface.symbols.items():
        if public_symbol(symbol) and symbol not in final_surface.symbols:
            candidates.append(
                Candidate(
                    "HIGH",
                    origin,
                    path,
                    kind,
                    symbol,
                    "public symbol is absent from final tree",
                )
            )
        elif (
            public_symbol(symbol)
            and symbol in final_surface.symbols
            and final_surface.symbols[symbol] != kind
        ):
            candidates.append(
                Candidate(
                    "HIGH",
                    origin,
                    path,
                    "symbol-kind",
                    symbol,
                    f"reference {kind} became {final_surface.symbols[symbol]}",
                )
            )

    for symbol, reference_parameters in reference_surface.parameters.items():
        if not public_symbol(symbol) or symbol not in final_surface.parameters:
            continue
        final_parameters = final_surface.parameters[symbol]
        for parameter in sorted(reference_parameters.keys() - final_parameters.keys()):
            candidates.append(
                Candidate(
                    "MEDIUM",
                    origin,
                    path,
                    "parameter",
                    f"{symbol}.{parameter}",
                    "reference parameter is absent from final signature",
                )
            )
        for parameter in sorted(reference_parameters.keys() & final_parameters.keys()):
            if not reference_parameters[parameter] and final_parameters[parameter]:
                candidates.append(
                    Candidate(
                        "MEDIUM",
                        origin,
                        path,
                        "parameter-requiredness",
                        f"{symbol}.{parameter}",
                        "reference optional parameter is required in final signature",
                    )
                )

    for symbol, decorator, route in sorted(
        reference_surface.routes - final_surface.routes
    ):
        candidates.append(
            Candidate(
                "HIGH",
                origin,
                path,
                "route",
                f"{symbol}@{decorator}:{route}",
                "route is absent from final tree",
            )
        )

    final_callers = set(final_surface.parameters)
    for caller, callee, keyword in sorted(
        reference_surface.call_keywords - final_surface.call_keywords
    ):
        if caller not in final_callers or not public_symbol(caller):
            continue
        candidates.append(
            Candidate(
                "LOW",
                origin,
                path,
                "call-keyword",
                f"{caller}->{callee}:{keyword}",
                "reference call keyword is absent from final caller",
            )
        )
    return candidates


def read_paths(path: Path) -> tuple[list[str], list[str]]:
    requested = sorted(
        {line.strip() for line in path.read_text().splitlines() if line.strip()}
    )
    python_paths = [item for item in requested if item.endswith(".py")]
    ignored = [item for item in requested if not item.endswith(".py")]
    return python_paths, ignored


def render(candidates: list[Candidate], paths: list[str], ignored: list[str]) -> str:
    priority_counts = {
        priority: sum(candidate.priority == priority for candidate in candidates)
        for priority in ("HIGH", "MEDIUM", "LOW")
    }
    lines = [
        "# Generic Interface Delta",
        "",
        f"- Python paths scanned: {len(paths)}",
        f"- Unsupported paths ignored: {len(ignored)}",
        f"- Review candidates: {len(candidates)}",
        f"- High priority: {priority_counts['HIGH']}",
        f"- Medium priority: {priority_counts['MEDIUM']}",
        f"- Low priority: {priority_counts['LOW']}",
        "- Automatic blockers: 0",
    ]
    if ignored:
        lines.extend(
            [
                "",
                "Ignored non-Python paths require a language-native gate:",
                "",
                *[f"- `{path}`" for path in ignored],
            ]
        )
    lines.extend(
        [
            "",
            "High rows need feature-thread disposition. Inspect medium rows for "
            "active boundaries. Inspect low rows only when an inferred contract "
            "or conflict decision makes the caller relevant.",
            "",
            "| Priority | Origin | Path | Kind | Symbol | Detail |",
            "|---|---|---|---|---|---|",
        ]
    )
    rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    for candidate in sorted(
        candidates,
        key=lambda item: (
            rank[item.priority],
            item.origin,
            item.path,
            item.kind,
            item.symbol,
        ),
    ):
        lines.append(
            f"| `{candidate.priority}` | `{candidate.origin}` | "
            f"`{candidate.path}` | `{candidate.kind}` | "
            f"`{candidate.symbol}` | {candidate.detail} |"
        )
    if not candidates:
        lines.append("| - | - | - | - | - | No interface deltas found. |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--final", default="HEAD")
    parser.add_argument("--paths-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    verify_revision(args.repo, args.source)
    verify_revision(args.repo, args.target)
    verify_revision(args.repo, args.final)
    paths, ignored = read_paths(args.paths_file)
    if not paths:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render([], paths, ignored))
        raise ValueError(
            "no Python paths to inspect; use a language-native gate for the "
            "requested paths"
        )
    candidates: list[Candidate] = []
    for path in paths:
        try:
            candidates.extend(
                compare(args.repo, "source", args.source, args.final, path)
            )
            candidates.extend(
                compare(args.repo, "target", args.target, args.final, path)
            )
        except SyntaxError as error:
            raise ValueError(f"cannot parse {path}: {error}") from error

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(candidates, paths, ignored))
    print(
        f"paths={len(paths)} ignored={len(ignored)} candidates={len(candidates)} "
        f"output={args.output}"
    )
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
    except (GitError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        exit_code = 2
    raise SystemExit(exit_code)
