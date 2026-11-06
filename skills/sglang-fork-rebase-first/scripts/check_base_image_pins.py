#!/usr/bin/env python3
"""Compare the new baseline's pinned packages with what the BASE_IMAGE ships.

A user-confirmed BASE_IMAGE (hard rule 13) says nothing about whether it matches the new
baseline. DSv4.1 flash 2026-10: the confirmed `dev-dsv41` image had sglang-kernel 0.4.6.post1
while the baseline pins 0.4.9, so the service exited at start ("is less than the minimum
required version") after a full CR image build. Run this before submit_cr.sh.

  docker run --rm --entrypoint python3 "$BASE_IMAGE" -m pip list --format=json > pip.json
  python3 check_base_image_pins.py --pyproject python/pyproject.toml --pip-list pip.json

Exit 0: every enforced package satisfies its pin. Exit 1: one is wrong or missing.
Other pins are listed as WARN only: the runtime asserts a few packages (`assert_pkg_version`
in srt/utils/common.py), not all of them, and `pip list` of a base image misses packages that
the delivery Dockerfile installs later.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

DEFAULT_ENFORCED = ("torch", "sglang-kernel")  # torch pins the build; sglang-kernel is asserted at start
REQ_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*(?:\[[^\]]*\])?\s*((?:==|>=|<=|~=|>|<)[^;,#]+(?:,\s*(?:==|>=|<=|~=|>|<)[^;,#]+)*)?\s*(;.*)?$")
CLAUSE_RE = re.compile(r"(==|>=|<=|~=|>|<)\s*([^\s,]+)")


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def numeric(version: str) -> tuple[int, ...]:
    """Leading numeric release of a version; `0.4.6.post1` -> (0, 4, 6), `2.14.1+cu130` -> (2, 14, 1)."""
    match = re.match(r"\d+(?:\.\d+)*", version)
    if not match:
        raise ValueError(f"version without a numeric release: {version!r}")
    return tuple(int(p) for p in match.group(0).split("."))


def satisfies(installed: str, op: str, wanted: str) -> bool:
    have, want = numeric(installed), numeric(wanted)
    width = max(len(have), len(want))
    have, want = have + (0,) * (width - len(have)), want + (0,) * (width - len(want))
    if op == "==":
        return installed.split("+")[0] == wanted  # local tag +cu130 is not part of the pin; .post1 is
    return {">=": have >= want, ">": have > want, "<=": have <= want, "<": have < want, "~=": have >= want}[op]


def read_pins(pyproject: Path) -> dict[str, list[tuple[str, str]]]:
    """Unconditional clauses of [project].dependencies, plus torch from [build-system].requires."""
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    build = [r for r in data.get("build-system", {}).get("requires", []) if norm(r).startswith("torch")]
    lines = [*build, *data.get("project", {}).get("dependencies", [])]
    pins: dict[str, list[tuple[str, str]]] = {}
    for line in lines:
        match = REQ_RE.match(line)
        if not match or match.group(3) or not match.group(2):  # skip marker-bound and unpinned lines
            continue
        seen = pins.setdefault(norm(match.group(1)), [])
        seen.extend(c for c in CLAUSE_RE.findall(match.group(2)) if c not in seen)
    return pins


def check(pins: dict[str, list[tuple[str, str]]], installed: dict[str, str], enforced: set[str]) -> list[tuple[str, str, str, str]]:
    """Rows of (level, package, wanted, found) for every pin that is not met.

    A non-enforced package absent from the image is skipped: the delivery Dockerfile installs
    many of them after the base layer, so `pip list` of the base cannot judge them.
    """
    rows = []
    for pkg, clauses in sorted(pins.items()):
        wanted = ",".join(f"{op}{v}" for op, v in clauses)
        level = "FAIL" if pkg in enforced else "WARN"
        if pkg not in installed:
            if level == "FAIL":
                rows.append((level, pkg, wanted, "missing"))
        elif not all(satisfies(installed[pkg], op, v) for op, v in clauses):
            rows.append((level, pkg, wanted, installed[pkg]))
    for pkg in sorted(enforced - set(pins)):
        rows.append(("FAIL", pkg, "(no pin in pyproject)", installed.get(pkg, "missing")))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pyproject", type=Path, required=True)
    ap.add_argument("--pip-list", type=Path, required=True, help="`pip list --format=json` of the BASE_IMAGE")
    ap.add_argument("--enforce", default=",".join(DEFAULT_ENFORCED), help="comma list; mismatches here exit 1")
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args()
    installed = {norm(p["name"]): p["version"] for p in json.loads(args.pip_list.read_text(encoding="utf-8"))}
    rows = check(read_pins(args.pyproject), installed, {norm(p) for p in args.enforce.split(",") if p})
    lines = ["| level | package | pyproject wants | image has |", "|---|---|---|---|"]
    lines += [f"| {lvl} | {pkg} | {want} | {found} |" for lvl, pkg, want, found in rows] or ["| OK | - | - | - |"]
    report = "\n".join(lines) + "\n"
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    print(report, end="")
    failed = [r for r in rows if r[0] == "FAIL"]
    if failed:
        print(f"ERROR: BASE_IMAGE does not satisfy enforced pins: {[r[1] for r in failed]}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
