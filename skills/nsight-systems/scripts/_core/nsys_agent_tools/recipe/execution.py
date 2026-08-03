"""Top-level recipe execution orchestration."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from ..defaults import DEFAULT_AGENT_CACHE_DIR
from ..process_utils import run_bounded_process
from ..reporting.file_utils import file_lock
from ..reporting.parquet_cache import full_parquet_exports_ready
from .health import recipe_failure_payload
from .payload import assemble_recipe_payload
from .redaction import redact_error
from .run_plan import RecipeRunContext, prepare_recipe_run


def run_recipe(
    *,
    nsys_path: str,
    recipe: str,
    report: str | Path,
    output_dir: str | Path,
    report_cache_dir: str | Path = DEFAULT_AGENT_CACHE_DIR,
    extra_args: list[str] | None = None,
    timeout_s: int = 300,
) -> dict[str, Any]:
    """Run a validated Nsys recipe against runtime-owned paths."""

    prepared = prepare_recipe_run(
        nsys_path=nsys_path,
        recipe=recipe,
        report=report,
        output_dir=output_dir,
        extra_args=extra_args or [],
        report_cache_dir=report_cache_dir,
    )
    if isinstance(prepared, dict):
        return prepared
    try:
        completed = _execute_recipe(prepared, timeout_s=timeout_s)
        if isinstance(completed, dict):
            return completed
        return assemble_recipe_payload(prepared, completed)
    finally:
        prepared.cleanup()


def _execute_recipe(
    prepared: RecipeRunContext,
    *,
    timeout_s: int,
) -> subprocess.CompletedProcess[str] | dict[str, Any]:
    try:
        prepared.preflight["ok"] = True
        # Intentional local `nsys recipe` execution: argv is a list (no shell),
        # recipe names and user extra args are validated by prepare_recipe_run,
        # and runtime-owned --input/--output values prevent path override.
        #
        # The export directory is shared with report-fact DuckDB caches so
        # recipes and report tools do not duplicate raw report Parquet exports.
        # If the raw export cache is complete, run without holding the shared
        # export lock. Otherwise let the recipe framework create/update only
        # the tables it needs under the report-set lock. Pre-exporting the
        # whole report can be slower than the recipe itself on large traces.
        if full_parquet_exports_ready(prepared.export_reports, prepared.export_path):
            return run_bounded_process(prepared.command, timeout_s=timeout_s)
        with file_lock(prepared.export_lock_path, timeout_s=max(float(timeout_s), 30.0)):
            return run_bounded_process(prepared.command, timeout_s=timeout_s)
    except subprocess.TimeoutExpired as exc:
        return recipe_failure_payload(
            recipe=prepared.recipe,
            error=redact_error(
                exc,
                report_path=prepared.report_path,
                recipe_input=prepared.recipe_input_path,
                recipe_out=prepared.output_path,
                recipe_export=prepared.export_path,
            ),
            preflight=prepared.preflight,
            category="recipe_timeout",
        )
    except Exception as exc:
        return recipe_failure_payload(
            recipe=prepared.recipe,
            error=redact_error(
                exc,
                report_path=prepared.report_path,
                recipe_input=prepared.recipe_input_path,
                recipe_out=prepared.output_path,
                recipe_export=prepared.export_path,
            ),
            preflight=prepared.preflight,
            category="recipe_process_error",
        )
