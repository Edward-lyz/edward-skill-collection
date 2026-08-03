"""Small filesystem path predicates shared by runtime modules."""

from __future__ import annotations

from pathlib import Path


def is_relative_to(path: Path, root: Path) -> bool:
    """Return whether ``path`` is under ``root`` after both are resolved by caller."""

    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
