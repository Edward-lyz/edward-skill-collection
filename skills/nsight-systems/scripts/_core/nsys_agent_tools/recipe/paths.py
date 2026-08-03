from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from ..path_utils import is_relative_to
from ..prompt_safety import sanitize_text


def iter_regular_output_files(root: Path) -> Iterator[Path]:
    """Yield regular files under a recipe output without following symlinks."""

    for current, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            name for name in dirnames if not (Path(current) / name).is_symlink()
        )
        for filename in sorted(filenames):
            path = Path(current) / filename
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if path.is_file() and not path.is_symlink() and is_relative_to(resolved, root):
                yield path


def resolve_recipe_output_label(output_root: str | Path, output_label: str) -> Path:
    """Resolve a recipe output label under ``output_root`` without accepting paths."""

    if not output_label or "/" in output_label or "\\" in output_label:
        raise ValueError("Use an output label returned by recipe execution, not a path.")
    if output_label in {".", ".."} or output_label.startswith("."):
        raise ValueError("Invalid recipe output label.")
    root = Path(output_root).expanduser().resolve()
    target = (root / output_label).resolve()
    if not is_relative_to(target, root):
        raise ValueError("Recipe output is outside the configured output root.")
    if not target.is_dir():
        raise FileNotFoundError(output_label)
    return target


def safe_recipe_output_label_for_error(output_label: str) -> str:
    if "/" in output_label or "\\" in output_label:
        return "<invalid-output-label>"
    return sanitize_text(output_label, max_chars=200)
