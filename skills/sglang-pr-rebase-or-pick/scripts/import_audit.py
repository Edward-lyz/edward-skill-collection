#!/usr/bin/env python3
"""Audit intra-repository imports of a merged tree.

Three-way merge works on lines, so an import can survive a clean merge while the
module or symbol it names no longer exists in the merged tree, and two imports can
bind the same name from different modules. Neither shows up as a conflict, and
neither is caught by a lint run that only covers the files the merge touched.

Findings are labelled against the two parents:

    NEW        broken only in the merged tree -> merge defect, fix it
    INHERITED  already broken in a parent -> pre-existing debt, but still a blocker
               when the file sits on a critical path of the current delivery,
               because that path is about to be executed for the first time

Exit code is non-zero when a NEW finding exists, or when any finding lands on a
critical path.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import subprocess
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class Finding:
    """One unresolvable import or one shadowed import binding."""

    path: str
    line: int
    kind: str
    detail: str

    def key(self) -> tuple[str, str, str]:
        # Line numbers shift between trees, so parent comparison ignores them.
        return (self.path, self.kind, self.detail)


class Tree:
    """File list plus module index of one revision (or the working tree)."""

    def __init__(self, repo: Path, rev: Optional[str], package_root: str) -> None:
        self.repo = repo
        self.rev = rev
        self.package_root = package_root.strip("/")
        self.files = self._list_files()
        self.modules, self.packages = self._index_modules()
        self._source_cache: dict[str, Optional[str]] = {}
        self._symbol_cache: dict[str, Optional[frozenset[str]]] = {}

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def _list_files(self) -> frozenset[str]:
        if self.rev is None:
            out = self._git("ls-files", "--", self.package_root)
        else:
            out = self._git(
                "ls-tree", "-r", "--name-only", self.rev, "--", self.package_root
            )
        return frozenset(line for line in out.splitlines() if line.endswith(".py"))

    def _index_modules(self) -> tuple[frozenset[str], frozenset[str]]:
        modules: set[str] = set()
        packages: set[str] = set()
        prefix = f"{self.package_root}/" if self.package_root else ""
        for path in self.files:
            if not path.startswith(prefix):
                continue
            relative = path[len(prefix):]
            parts = relative[: -len(".py")].split("/")
            if parts[-1] == "__init__":
                parts = parts[:-1]
                if parts:
                    packages.add(".".join(parts))
            if parts:
                modules.add(".".join(parts))
            for depth in range(1, len(parts)):
                packages.add(".".join(parts[:depth]))
        return frozenset(modules), frozenset(packages)

    def top_level_names(self) -> frozenset[str]:
        return frozenset(name.split(".")[0] for name in self.modules | self.packages)

    def read(self, path: str) -> Optional[str]:
        if path in self._source_cache:
            return self._source_cache[path]
        text: Optional[str]
        try:
            if self.rev is None:
                text = (self.repo / path).read_text(encoding="utf-8", errors="replace")
            else:
                text = self._git("show", f"{self.rev}:{path}")
        except (OSError, subprocess.CalledProcessError):
            text = None
        self._source_cache[path] = text
        return text

    def module_path(self, module: str) -> Optional[str]:
        prefix = f"{self.package_root}/" if self.package_root else ""
        as_module = prefix + module.replace(".", "/") + ".py"
        if as_module in self.files:
            return as_module
        as_package = prefix + module.replace(".", "/") + "/__init__.py"
        if as_package in self.files:
            return as_package
        return None

    def has_module(self, module: str) -> bool:
        return module in self.modules or module in self.packages

    def exported_names(self, module: str) -> Optional[frozenset[str]]:
        """Top-level names of a module, or None when they cannot be trusted."""
        if module in self._symbol_cache:
            return self._symbol_cache[module]
        result: Optional[frozenset[str]] = None
        path = self.module_path(module)
        source = self.read(path) if path else None
        if source is not None:
            try:
                tree = ast.parse(source)
            except SyntaxError:
                tree = None
            if tree is not None:
                names: set[str] = set()
                trusted = True
                for node in tree.body:
                    definition = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                    if isinstance(node, definition):
                        names.add(node.name)
                        if node.name == "__getattr__":
                            # PEP 562 lazy re-export: the symbol table is built at
                            # runtime from a mapping, so static names prove nothing.
                            trusted = False
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                names.add(target.id)
                    elif isinstance(node, ast.AnnAssign) and isinstance(
                        node.target, ast.Name
                    ):
                        names.add(node.target.id)
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            names.add(alias.asname or alias.name.split(".")[0])
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            if alias.name == "*":
                                trusted = False
                            else:
                                names.add(alias.asname or alias.name)
                    elif isinstance(node, (ast.If, ast.Try, ast.With)):
                        # Conditional definitions are common for optional deps;
                        # symbol checking would produce noise, so stop trusting.
                        trusted = False
                if trusted:
                    result = frozenset(names)
        self._symbol_cache[module] = result
        return result


def _optional_import_lines(parsed: ast.Module) -> frozenset[int]:
    """Lines inside a try block that swallows ImportError.

    Optional-dependency fallbacks legitimately import modules that may be absent
    and legitimately rebind the same name, so they are not findings.
    """
    lines: set[int] = set()
    for node in ast.walk(parsed):
        if not isinstance(node, ast.Try):
            continue
        guarded = False
        for handler in node.handlers:
            names = []
            if isinstance(handler.type, ast.Name):
                names = [handler.type.id]
            elif isinstance(handler.type, ast.Tuple):
                names = [e.id for e in handler.type.elts if isinstance(e, ast.Name)]
            elif handler.type is None:
                names = ["BaseException"]
            if any(
                name
                in ("ImportError", "ModuleNotFoundError", "Exception", "BaseException")
                for name in names
            ):
                guarded = True
        if not guarded:
            continue
        for statement in node.body:
            for inner in ast.walk(statement):
                if hasattr(inner, "lineno"):
                    lines.add(inner.lineno)
    return frozenset(lines)


def scan_tree(tree: Tree, scope: Optional[Iterable[str]] = None) -> list[Finding]:
    """Collect unresolvable imports and shadowed bindings for one tree."""
    local_roots = tree.top_level_names()
    findings: list[Finding] = []
    paths = sorted(scope) if scope is not None else sorted(tree.files)
    for path in paths:
        source = tree.read(path)
        if source is None:
            continue
        try:
            with warnings.catch_warnings():
                # Repository files may contain invalid escapes; that is not this
                # gate's business.
                warnings.simplefilter("ignore")
                parsed = ast.parse(source)
        except SyntaxError as exc:
            findings.append(Finding(path, exc.lineno or 0, "syntax", str(exc.msg)))
            continue
        bindings: dict[str, str] = {}
        optional_lines = _optional_import_lines(parsed)
        # Shadowing only matters at module level: a function-local import rebinding
        # a module-level name is normal scoping, not a merge artefact.
        for node in parsed.body:
            if node.lineno in optional_lines:
                continue
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    bound = alias.asname or root
                    # `import a` and `import a.b` both bind `a`; that is not a shadow.
                    source = alias.name if alias.asname else root
                    _record_binding(
                        findings, bindings, path, node.lineno, bound, source
                    )
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    bound = alias.asname or alias.name
                    _record_binding(
                        findings, bindings, path, node.lineno, bound,
                        f"{node.module}.{alias.name}",
                    )
        for entry in ast.walk(parsed):
            if getattr(entry, "lineno", 0) in optional_lines:
                continue
            if isinstance(entry, ast.Import):
                for alias in entry.names:
                    root = alias.name.split(".")[0]
                    if root in local_roots and not tree.has_module(alias.name):
                        findings.append(
                            Finding(path, entry.lineno, "missing-module", alias.name)
                        )
            elif isinstance(entry, ast.ImportFrom):
                if entry.level or entry.module is None:
                    continue
                root = entry.module.split(".")[0]
                if root not in local_roots:
                    continue
                if not tree.has_module(entry.module):
                    findings.append(
                        Finding(path, entry.lineno, "missing-module", entry.module)
                    )
                    continue
                exported = tree.exported_names(entry.module)
                if exported is None:
                    continue
                for alias in entry.names:
                    if alias.name == "*":
                        continue
                    submodule = f"{entry.module}.{alias.name}"
                    if alias.name in exported or tree.has_module(submodule):
                        continue
                    findings.append(
                        Finding(path, entry.lineno, "missing-symbol", submodule)
                    )
    return findings


def _record_binding(
    findings: list[Finding],
    bindings: dict[str, str],
    path: str,
    line: int,
    bound: str,
    source: str,
) -> None:
    previous = bindings.get(bound)
    if previous is not None and previous != source:
        findings.append(
            Finding(path, line, "shadowed-import", f"{bound}: {previous} then {source}")
        )
    bindings[bound] = source


def is_critical(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument(
        "--final",
        default=None,
        help="revision of the merged tree; omit to audit the working tree",
    )
    parser.add_argument("--parent", action="append", default=[],
                        help="parent revision, repeat for both parents")
    parser.add_argument("--package-root", default="python",
                        help="directory holding the top-level packages")
    parser.add_argument("--critical-path", action="append", default=[],
                        help="glob of files the delivery target will execute")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    final = Tree(args.repo, args.final, args.package_root)
    findings = scan_tree(final)
    parent_keys: set[tuple[str, str, str]] = set()
    for parent in args.parent:
        parent_tree = Tree(args.repo, parent, args.package_root)
        shared = sorted(parent_tree.files & {f.path for f in findings})
        parent_keys.update(item.key() for item in scan_tree(parent_tree, shared))

    rows: list[tuple[str, Finding]] = []
    for finding in findings:
        label = "INHERITED" if finding.key() in parent_keys else "NEW"
        rows.append((label, finding))

    blockers = [
        (label, finding)
        for label, finding in rows
        if label == "NEW" or is_critical(finding.path, args.critical_path)
    ]

    report: list[str] = [
        "# Import audit",
        "",
        f"final: {args.final or 'working tree'}  "
        f"parents: {', '.join(args.parent) or 'none'}",
        f"files scanned: {len(final.files)}  findings: {len(rows)}  "
        f"blockers: {len(blockers)}",
        "",
        "| label | kind | file:line | detail |",
        "| --- | --- | --- | --- |",
    ]
    def sort_key(item: tuple[str, Finding]) -> tuple[str, str, int]:
        return (item[0], item[1].path, item[1].line)

    for label, finding in sorted(rows, key=sort_key):
        critical = (
            " (critical path)" if is_critical(finding.path, args.critical_path) else ""
        )
        report.append(
            f"| {label}{critical} | {finding.kind} | "
            f"{finding.path}:{finding.line} | {finding.detail} |"
        )
    text = "\n".join(report) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
