#!/usr/bin/env python3
"""Print the comma-separated report dependencies missing from the running interpreter."""

from __future__ import annotations

import re
from importlib import metadata
from pathlib import Path


def main() -> int:
    requirements = Path(__file__).resolve().parent.parent / "requirements.txt"
    if not requirements.is_file():
        return 0
    missing = []
    for line in requirements.read_text(encoding="utf-8").splitlines():
        spec = line.strip()
        if not spec or spec.startswith("#"):
            continue
        name = re.split(r"[<>=!~;\[ ]", spec, maxsplit=1)[0]
        try:
            metadata.distribution(name)
        except metadata.PackageNotFoundError:
            missing.append(name)
    if missing:
        print(", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
