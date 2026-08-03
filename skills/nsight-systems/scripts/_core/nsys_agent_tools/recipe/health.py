"""Recipe preflight, outcome, and failure classification helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .report_inputs import recipe_report_files


def recipe_preflight(
    *,
    recipe: str,
    report_path: Path,
    output_root: Path,
    extra_args: list[str],
) -> dict[str, Any]:
    """Return a cheap recipe execution health snapshot.

    This does not export or open the report. It captures the facts needed to
    explain failures before the expensive recipe subprocess runs: local input
    existence, input kind/size, requested extra arguments, runtime-owned path
    controls, and whether the runtime-owned output root is writable.
    """

    report_input: dict[str, Any] = {
        "exists": report_path.exists(),
        "label": report_path.name,
        "kind": _report_input_kind(report_path),
    }
    if report_path.is_file():
        report_input["bytes"] = _safe_size(report_path)
    elif report_path.is_dir():
        reports = recipe_report_files(report_path)
        report_input["report_count"] = len(reports)
        report_input["total_bytes"] = sum(_safe_size(path) for path in reports)
        if len(reports) > 1:
            report_input["note"] = "directory input; recipe runtime may process multiple reports"
    warnings: list[str] = []
    if int(report_input.get("report_count", 1)) > 1:
        warnings.append("multi_report_recipe_may_be_expensive")
    return {
        "ok": False,
        "recipe": recipe,
        "recipe_name_valid": bool(re.fullmatch(r"[a-z0-9_]+", recipe)),
        "recipe_available": False,
        "live_help_ok": False,
        "recipe_catalog_ok": False,
        "nsys_version_ok": False,
        "report_input": report_input,
        "runtime_controls_input_output": True,
        "output_root_label": output_root.name,
        "output_root_writable": False,
        "requested_extra_args": list(extra_args),
        "accepted_extra_args": [],
        "warnings": warnings,
    }


def recipe_failure_payload(
    *,
    recipe: str,
    error: str,
    preflight: dict[str, Any],
    category: str,
) -> dict[str, Any]:
    guidance = recipe_failure_guidance(category)
    return {
        "ok": False,
        "recipe": recipe,
        "error": error,
        "failure_category": category,
        "failure_guidance": guidance,
        "recipe_outcome": {
            "status": "failed",
            "data_available": False,
            "category": category,
            "guidance": guidance,
        },
        "preflight": preflight,
    }


def classify_recipe_failure(stderr: str, stdout: str) -> str:
    text = f"{stderr}\n{stdout}".lower()
    if "nodataerror" in text or "no data" in text:
        return "no_matching_data"
    if "no such file" in text or "not found" in text:
        return "input_or_dependency_missing"
    if "permission denied" in text:
        return "permission_denied"
    if "out of memory" in text or "memoryerror" in text or "cannot allocate memory" in text:
        return "resource_exhausted"
    if "database is locked" in text or ("disk" in text and "full" in text):
        return "storage_or_cache_error"
    if "traceback" in text or "exception" in text:
        return "recipe_exception"
    return "recipe_failed"


def recipe_failure_guidance(category: str) -> list[str]:
    common = [
        "Use report doctor/context to check whether the loaded report contains the data required by this recipe.",
        "Use recipe help to verify options for this installed Nsight Systems version.",
    ]
    specific = {
        "nsys_unavailable": [
            "Check NSYS_PATH or install Nsight Systems so `nsys --version` works.",
        ],
        "unknown_recipe": [
            "List installed recipes with `nsys recipe --help` and choose a recipe from that catalog.",
        ],
        "recipe_help_unavailable": [
            "Retry without extra recipe arguments, or fix the local `nsys recipe <name> --help` failure first.",
        ],
        "invalid_recipe_args": [
            "Remove path-control arguments such as --input, --output, --output-dir, or --export-dir; the runtime owns those paths.",
            "Do not retry with a direct `nsys recipe` command as a workaround for rejected runtime path controls.",
            "Only pass options that appear in live help for this recipe.",
        ],
        "report_missing": [
            "Load an existing `.nsys-rep`, `.qdrep`, exported report, or report directory before running the recipe.",
        ],
        "invalid_report_input": [
            "Use a regular report file or a directory containing report files.",
        ],
        "output_root_unavailable": [
            "Choose or configure a writable recipe output root.",
        ],
        "recipe_timeout": [
            "For large inputs, narrow the report set, use documented filters such as --filter-time or --filter-nvtx when supported, or increase the timeout.",
        ],
        "no_matching_data": [
            "The recipe ran but did not find the activity type it analyzes; inspect report inventory before retrying.",
        ],
        "resource_exhausted": [
            "Try fewer reports, directory :n limits where documented, --mode none where supported, or a narrower time/NVTX filter.",
        ],
        "storage_or_cache_error": [
            "Check free disk space and clear stale recipe/cache outputs if needed.",
        ],
    }
    return specific.get(category, []) + common


def recipe_outcome(
    *,
    returncode: int,
    primary_files: list[dict[str, Any]],
    stderr: str,
    stdout: str,
) -> dict[str, Any]:
    if returncode != 0:
        category = classify_recipe_failure(stderr, stdout)
        return {
            "status": "failed",
            "data_available": False,
            "category": category,
            "guidance": recipe_failure_guidance(category),
        }
    if primary_files:
        return {
            "status": "completed_with_results",
            "data_available": True,
            "primary_result_count": len(primary_files),
        }
    category = classify_recipe_failure(stderr, stdout)
    if category == "recipe_failed":
        category = "no_matching_data"
    return {
        "status": "completed_no_data",
        "data_available": False,
        "category": category,
        "guidance": recipe_failure_guidance(category),
    }


def _report_input_kind(path: Path) -> str:
    if path.is_file():
        return "file"
    if path.is_dir():
        return "directory"
    if path.exists():
        return "other"
    return "missing"


def _safe_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0
