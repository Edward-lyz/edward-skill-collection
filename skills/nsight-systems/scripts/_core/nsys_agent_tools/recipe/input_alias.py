"""Runtime-owned input aliases for Nsys recipe execution."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from .health import recipe_failure_payload
from .redaction import redact_error
from .report_inputs import recipe_report_files


def prepare_recipe_input_alias(
    *,
    recipe: str,
    report_path: Path,
    output_root: Path,
    recipe_out: Path,
    preflight: dict[str, Any],
) -> tuple[Path, tempfile.TemporaryDirectory[str]] | dict[str, Any]:
    """Stage report inputs in a runtime-owned directory before recipes run.

    The installed recipe framework may materialize per-report export sidecars
    next to its `--input` path even when `--export-dir` is provided. Passing a
    symlink/hardlink alias under the runtime output root keeps those sidecars
    out of the user's report directory without copying large reports.
    """

    scratch = tempfile.TemporaryDirectory(
        prefix=f"{recipe_out.name}-input-",
        dir=output_root,
    )
    scratch_path = Path(scratch.name)
    try:
        if report_path.is_file():
            alias = scratch_path / report_path.name
            _link_report_file(report_path, alias)
            preflight["input_alias"] = "runtime-owned-file"
            return alias, scratch
        alias_dir = scratch_path / report_path.name
        alias_dir.mkdir()
        reports = recipe_report_files(report_path)
        for child in reports:
            _link_report_file(child, alias_dir / child.name)
        linked = len(reports)
        if linked == 0:
            raise FileNotFoundError("report directory contains no native report files")
        preflight["input_alias"] = "runtime-owned-directory"
        preflight["input_alias_report_count"] = linked
        return alias_dir, scratch
    except Exception as exc:  # noqa: BLE001 - JSON tool boundary
        scratch.cleanup()
        return recipe_failure_payload(
            recipe=recipe,
            error=redact_error(
                exc,
                report_path=report_path,
                recipe_out=recipe_out,
            ),
            preflight=preflight,
            category="input_alias_unavailable",
        )


def _link_report_file(source: Path, alias: Path) -> None:
    try:
        alias.symlink_to(source)
    except OSError:
        # Hardlinks keep recipe sidecars beside the alias without copying large
        # reports. They may still fail across devices, in which case the caller
        # returns a structured setup failure instead of writing beside the
        # user's original report.
        alias.hardlink_to(source)
