"""Assemble structured recipe execution payloads from process results."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .capabilities import recipe_run_contract
from .health import classify_recipe_failure, recipe_failure_guidance, recipe_outcome
from .paths import iter_regular_output_files
from .preview import MAX_RECIPE_OUTPUT_FILES, inspect_recipe_output, preview_outputs
from .redaction import redact_command, redact_process_text
from .result_contract import (
    expected_recipe_outputs_from_files,
    primary_result_files,
    recipe_file_role,
    recipe_output_profile,
)
from .run_plan import RecipeRunContext


@dataclass(frozen=True)
class RecipeOutputInspection:
    files: list[dict[str, Any]]
    files_truncated: bool
    schemas: list[dict[str, Any]]
    previews: list[dict[str, Any]]
    primary_files: list[dict[str, Any]]
    output_profile: str


def assemble_recipe_payload(
    prepared: RecipeRunContext,
    completed: subprocess.CompletedProcess[str],
) -> dict[str, Any]:
    inspected = inspect_recipe_outputs(prepared.output_path, recipe=prepared.recipe)
    failure_category = (
        ""
        if completed.returncode == 0
        else classify_recipe_failure(completed.stderr, completed.stdout)
    )
    outcome = recipe_outcome(
        returncode=completed.returncode,
        primary_files=inspected.primary_files,
        stderr=completed.stderr,
        stdout=completed.stdout,
    )
    payload = {
        "ok": completed.returncode == 0,
        "recipe": prepared.recipe,
        "display_name": prepared.recipes.get(prepared.recipe),
        "preflight": prepared.preflight,
        "recipe_outcome": outcome,
        "analysis_contract": recipe_run_contract(prepared.recipe),
        "output_available": prepared.output_path.is_dir(),
        "data_available": bool(inspected.primary_files),
        "failure_category": failure_category or None,
        "failure_guidance": recipe_failure_guidance(failure_category) if failure_category else [],
        "command": redact_command(
            prepared.command,
            report_path=prepared.report_path,
            recipe_input=prepared.recipe_input_path,
            recipe_out=prepared.output_path,
            recipe_export=prepared.export_path,
        ),
        "evidence_summary": recipe_evidence_summary(
            recipe=prepared.recipe,
            files=inspected.files,
            schemas=inspected.schemas,
            previews=inspected.previews,
            primary_files=inspected.primary_files,
            output_profile=inspected.output_profile,
            allowed_flags=prepared.allowed_flags if prepared.recipe_help.get("ok") else None,
        ),
        "_local_output_path": str(prepared.output_path),
        "output_label": prepared.output_path.name,
        "stdout": redact_process_text(
            completed.stdout,
            report_path=prepared.report_path,
            recipe_input=prepared.recipe_input_path,
            recipe_out=prepared.output_path,
            recipe_export=prepared.export_path,
        ),
        "stderr": redact_process_text(
            completed.stderr,
            report_path=prepared.report_path,
            recipe_input=prepared.recipe_input_path,
            recipe_out=prepared.output_path,
            recipe_export=prepared.export_path,
        ),
        "files": inspected.files[:100],
        "result_files": [item for item in inspected.files if item.get("role") == "data"][:100],
        "primary_result_files": inspected.primary_files,
        "output_profile": inspected.output_profile,
        "helper_files": [item for item in inspected.files if item.get("role") == "helper"][:50],
        "auxiliary_files": [
            item
            for item in inspected.files
            if item.get("role") in {"metadata", "notebook", "analysis_metadata", "other"}
        ][:100],
        "output_schemas": inspected.schemas,
        "output_previews": inspected.previews,
    }
    if inspected.files_truncated:
        payload["files_truncated"] = True
        payload["files_truncated_note"] = (
            f"Only the first {MAX_RECIPE_OUTPUT_FILES} regular output files were inspected."
        )
    if prepared.recipe_help.get("ok"):
        payload["live_flags"] = sorted(prepared.allowed_flags)
        payload["supports_csv"] = "--csv" in prepared.allowed_flags
    expected = expected_recipe_outputs_from_files(
        inspected.files,
        supports_csv=bool(payload.get("supports_csv")),
    )
    if expected:
        payload["expected_output_notes"] = expected
    return payload


def inspect_recipe_outputs(recipe_out: Path, *, recipe: str) -> RecipeOutputInspection:
    files: list[dict[str, Any]] = []
    files_truncated = False
    if recipe_out.is_dir():
        for path in iter_regular_output_files(recipe_out):
            rel = path.relative_to(recipe_out).as_posix()
            files.append({"path": rel, "bytes": path.stat().st_size, "role": recipe_file_role(rel)})
            if len(files) >= MAX_RECIPE_OUTPUT_FILES:
                files_truncated = True
                break
    previews = preview_outputs(recipe_out, files) if recipe_out.is_dir() else []
    schemas = inspect_recipe_output(recipe_out, files=files) if recipe_out.is_dir() else []
    primary_files = primary_result_files(files, schemas=schemas, previews=previews)
    return RecipeOutputInspection(
        files=files,
        files_truncated=files_truncated,
        schemas=schemas,
        previews=previews,
        primary_files=primary_files,
        output_profile=recipe_output_profile(recipe=recipe, files=files),
    )


def recipe_evidence_summary(
    *,
    recipe: str,
    files: list[dict[str, Any]],
    schemas: list[dict[str, Any]],
    previews: list[dict[str, Any]],
    primary_files: list[dict[str, Any]],
    output_profile: str,
    allowed_flags: set[str] | None,
) -> dict[str, Any]:
    """Return compact execution evidence near the top of recipe payloads."""

    schema_by_file = {str(item.get("file")): item for item in schemas if item.get("file")}
    preview_by_file = {str(item.get("file")): item for item in previews if item.get("file")}
    primary_paths = {str(item.get("path")) for item in primary_files}
    data_files: list[dict[str, Any]] = []
    ordered_files = [item for item in files if str(item.get("path")) in primary_paths]
    ordered_files.extend(item for item in files if str(item.get("path")) not in primary_paths)
    for item in ordered_files:
        if item.get("role") != "data":
            continue
        rel = str(item.get("path") or "")
        schema = schema_by_file.get(rel, {})
        preview = preview_by_file.get(rel, {})
        row: dict[str, Any] = {
            "path": rel,
            "query_table": schema.get("query_table"),
            "bytes": item.get("bytes"),
            "columns": [
                column.get("name")
                for column in schema.get("columns", [])[:20]
                if isinstance(column, dict)
            ],
        }
        if schema.get("row_count") is not None:
            row["row_count"] = schema.get("row_count")
        if preview.get("preview_sort"):
            row["preview_sort"] = preview.get("preview_sort")
        if preview.get("text"):
            row["preview_text"] = str(preview.get("text"))[:1200]
        data_files.append(row)
        if len(data_files) >= 8:
            break
    return {
        "recipe": recipe,
        "output_profile": output_profile,
        "live_flags": sorted(allowed_flags) if allowed_flags is not None else None,
        "primary_result_files": primary_files,
        "data_files": data_files,
        "non_data_files": [str(item.get("path")) for item in files if item.get("role") != "data"][
            :8
        ],
    }
