#!/usr/bin/env python3
"""Verify that a shadow branch reproduces its source tree safely.

Usage:
    python3 verify_shadow.py REPO SOURCE_REF SHADOW_REF [--base BASE] [--skip-python]

Checks:
1. The parent of SHADOW_REF (the docs commit) has the same tree as SOURCE_REF.
2. Files changed since BASE contain no conflict markers.
3. Every Python file at the shadow tree parses; failures already present at
   BASE are reported separately as pre-existing.

Exit code is nonzero when a check fails.
"""

import argparse
import ast
import os
import re
import subprocess
import sys
import warnings

MARKER = re.compile(r"^(<<<<<<< |=======$|>>>>>>> |\|\|\|\|\|\|\| )")


def git(repo, *args, check=True):
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=check
    )


def tree_of(repo, ref):
    return git(repo, "rev-parse", f"{ref}^{{tree}}").stdout.strip()


def changed_files(repo, base, tip):
    out = git(repo, "diff", "--name-only", "--no-renames", base, tip).stdout
    return [line for line in out.splitlines() if line.strip()]


def read_blob(repo, ref, path):
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=repo, capture_output=True, check=False
    )
    return result.stdout if result.returncode == 0 else None


def parse_python(data):
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return "non-utf8", None
    if text.startswith("\ufeff"):
        text = text[1:]
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ast.parse(text)
        except SyntaxError as exc:
            return "syntax", f"line {exc.lineno}: {exc.msg}"
        return "bom", None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ast.parse(text)
    except SyntaxError as exc:
        return "syntax", f"line {exc.lineno}: {exc.msg}"
    return "ok", None


def python_failures(repo, ref):
    listing = git(repo, "ls-tree", "-r", "--name-only", ref).stdout.splitlines()
    failures = {}
    total = 0
    for path in listing:
        if not path.endswith(".py"):
            continue
        data = read_blob(repo, ref, path)
        if data is None:
            continue
        total += 1
        status, detail = parse_python(data)
        if status in ("syntax", "non-utf8"):
            failures[path] = f"{status}: {detail}" if detail else status
    return total, failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo")
    parser.add_argument("source_ref")
    parser.add_argument("shadow_ref")
    parser.add_argument("--base", default=None)
    parser.add_argument("--skip-python", action="store_true")
    args = parser.parse_args()

    repo = os.path.abspath(args.repo)
    ok = True

    shadow_tip = git(repo, "rev-parse", args.shadow_ref).stdout.strip()
    parent = git(repo, "rev-parse", f"{shadow_tip}^").stdout.strip()
    source_tree = tree_of(repo, args.source_ref)
    parent_tree = tree_of(repo, parent)
    tree_equal = source_tree == parent_tree
    print(
        f"tree_equal: {'PASS' if tree_equal else 'FAIL'} "
        f"({parent[:10]} tree {parent_tree[:10]} vs {args.source_ref} {source_tree[:10]})"
    )
    ok = ok and tree_equal

    marker_hits = []
    if args.base:
        for path in changed_files(repo, args.base, parent):
            data = read_blob(repo, parent, path)
            if not data or len(data) > 2_000_000 or b"\0" in data[:8192]:
                continue
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                if MARKER.match(line):
                    marker_hits.append(f"{path}:{lineno}")
                    break
    markers_ok = not marker_hits
    print(
        f"conflict_markers: {'PASS' if markers_ok else 'FAIL'} "
        f"({len(marker_hits)} file(s))"
    )
    if marker_hits:
        for hit in marker_hits[:20]:
            print(f"  {hit}")
        ok = False

    if not args.skip_python:
        total, failures = python_failures(repo, parent)
        baseline = {}
        if args.base:
            _, baseline = python_failures(repo, args.base)
        new_failures = {p: d for p, d in failures.items() if p not in baseline}
        syntax_ok = not new_failures
        print(
            f"python_syntax: {'PASS' if syntax_ok else 'FAIL'} "
            f"({total} files, {len(new_failures)} new, {len(baseline)} pre-existing)"
        )
        for path, detail in list(new_failures.items())[:10]:
            print(f"  NEW {path}: {detail}")
        for path, detail in list(baseline.items())[:5]:
            print(f"  pre-existing {path}: {detail}")
        ok = ok and syntax_ok

    files = git(repo, "ls-tree", "-r", "--long", shadow_tip).stdout.splitlines()
    for line in files:
        match = re.match(r"^\d+ \w+ [0-9a-f]+ +(\d+)\t(.+)$", line)
        if match and "SHADOW_DIFFMAP.html" in match.group(2):
            print(f"diffmap: {match.group(2)} {int(match.group(1)):,} bytes")

    print(f"RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
