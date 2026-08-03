"""Native report-file selection for recipe execution."""

from __future__ import annotations

from pathlib import Path

from ..path_utils import is_relative_to

_NATIVE_REPORT_SUFFIXES = {".nsys-rep", ".qdrep"}


def recipe_report_files(report_path: Path) -> tuple[Path, ...]:
    """Return native report files a recipe run should process.

    Directory inputs prefer ``.nsys-rep`` over ``.qdrep`` for the same report
    stem because ``.nsys-rep`` is the normal report-analysis input and shares
    the same cache identity as report facts. ``.qdrep`` remains supported for
    stems where no matching ``.nsys-rep`` exists.
    """

    if report_path.is_file():
        return (report_path.resolve(),)
    selected: dict[str, Path] = {}
    root = report_path.resolve()
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        if path.is_symlink() or not path.is_file():
            continue
        if path.suffix.lower() not in _NATIVE_REPORT_SUFFIXES:
            continue
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if not is_relative_to(resolved, root):
            continue
        stem_key = path.stem.lower()
        previous = selected.get(stem_key)
        if previous is None or _prefer_report(path, previous):
            selected[stem_key] = resolved
    return tuple(sorted(selected.values(), key=lambda path: path.name))


def _prefer_report(candidate: Path, previous: Path) -> bool:
    if candidate.suffix.lower() == ".nsys-rep" and previous.suffix.lower() != ".nsys-rep":
        return True
    if candidate.suffix.lower() != previous.suffix.lower():
        return False
    return candidate.name < previous.name
