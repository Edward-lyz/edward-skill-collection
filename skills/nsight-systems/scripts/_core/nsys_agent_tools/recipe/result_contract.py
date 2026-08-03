"""Recipe output classification rules shared by runtime and BYO tools.

This module is intentionally free of file I/O.  It only interprets the file
list, schemas, and previews produced by recipe execution so the model sees a
stable contract: primary data tables, auxiliary artifacts, and output profile.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

PRIMARY_RECIPE_RESULT_FILE_LIMIT = 8
RECIPE_MANIFEST_FILES = frozenset({"files.parquet", "files.csv", "files.json"})
PREVIEW_SUFFIX_PRIORITY = {
    ".csv": 0,
    ".parquet": 1,
    ".json": 2,
    ".txt": 3,
    ".md": 4,
    ".log": 5,
}
STANDARD_RESULT_STEM_PRIORITY = {
    "all_stats": 0,
    "rank_stats": 1,
    "all_stats_by_device": 2,
    "rank_stats_by_device": 3,
    "analysis": 4,
}
MAGNITUDE_COLUMN_PRIORITY = (
    "sum",
    "total",
    "total_time",
    "total_time_ns",
    "duration",
    "duration_ns",
    "time",
    "time_ns",
    "elapsed",
    "elapsed_ns",
)


def recipe_file_role(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if is_recipe_manifest(path):
        return "metadata"
    if suffix in {".parquet", ".csv", ".json", ".jsonl", ".sqlite", ".db", ".arrow", ".hdf5"}:
        return "data"
    if suffix == ".ipynb":
        return "notebook"
    if suffix == ".nsys-analysis":
        return "analysis_metadata"
    if suffix in {".py", ".so", ".dll", ".dylib"}:
        return "helper"
    return "other"


def recipe_output_profile(*, recipe: str, files: list[dict[str, Any]]) -> str:
    """Infer the generated output shape from actual files, not a question."""

    names = {str(item.get("path", "")).lower() for item in files}
    stems = {Path(name).stem for name in names}
    if {"all_stats", "rank_stats", "all_stats_by_device", "rank_stats_by_device"} & stems or any(
        stem.endswith("_stats") for stem in stems
    ):
        return "stats"
    if "analysis" in stems:
        if any("trace" in name for name in names) or recipe.endswith("_trace"):
            return "trace"
        if "map" in recipe.split("_") or any("heatmap" in name for name in names):
            return "map"
        return "analysis_rows"
    if recipe == "diff" or any("diff" in name for name in names):
        return "diff"
    return "unknown"


def primary_result_files(
    files: list[dict[str, Any]],
    *,
    schemas: list[dict[str, Any]],
    previews: list[dict[str, Any]],
    limit: int = PRIMARY_RECIPE_RESULT_FILE_LIMIT,
) -> list[dict[str, Any]]:
    """Select model-facing recipe result tables from actual generated files."""

    schema_by_file = {str(item.get("file")): item for item in schemas if item.get("file")}
    preview_by_file = {str(item.get("file")): item for item in previews if item.get("file")}
    ranked: list[tuple[int, str, dict[str, Any]]] = []
    for item in files:
        rel = str(item.get("path") or "")
        if not rel or item.get("role") != "data" or is_recipe_manifest(rel):
            continue
        schema = schema_by_file.get(rel, {})
        preview = preview_by_file.get(rel, {})
        score, reason = _primary_result_score(rel, item, schema=schema, preview=preview)
        row: dict[str, Any] = {
            "path": rel,
            "bytes": item.get("bytes"),
            "role": item.get("role"),
            "reason": reason,
            "columns": [column.get("name") for column in schema.get("columns", [])[:20] if isinstance(column, dict)],
            "preview_available": bool(preview),
        }
        if schema.get("row_count") is not None:
            row["row_count"] = schema.get("row_count")
        if preview.get("preview_sort"):
            row["preview_sort"] = preview.get("preview_sort")
        ranked.append((score, rel, row))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [row for _score, _rel, row in ranked[: max(1, limit)]]


def expected_recipe_outputs_from_files(files: list[dict[str, Any]], *, supports_csv: bool) -> list[str]:
    """Return version-neutral notes inferred only from files that exist."""

    names = {str(item.get("path", "")) for item in files}
    notes: list[str] = []
    if any(name.endswith(".nsys-analysis") for name in names):
        notes.append(
            "The `.nsys-analysis` file is the JSON analysis metadata entry point for the output directory; "
            "it records recipe metadata, options/timing, and the generated output inventory."
        )
    if supports_csv and any(name.endswith(".parquet") for name in names):
        notes.append("This recipe's live help lists `--csv`; when that option is used, CSV companions may be generated for supported Parquet outputs.")
    if "rank_stats_by_device.parquet" in names:
        notes.append("`rank_stats_by_device.parquet` is the per-rank/per-input per-device statistics table.")
    if "all_stats_by_device.parquet" in names:
        notes.append("`all_stats_by_device.parquet` is the aggregate per-device statistics table.")
    return notes


def recipe_preview_priority(path: str) -> tuple[int, int, str]:
    """Return a stable preview order for generated recipe files."""

    suffix = Path(path).suffix.lower()
    priority = PREVIEW_SUFFIX_PRIORITY.get(suffix, 9)
    if is_recipe_manifest(path):
        priority = 99
    stem_priority = STANDARD_RESULT_STEM_PRIORITY.get(Path(path).stem.lower(), 5)
    return priority, stem_priority, path


def magnitude_sort_column(columns: Iterable[object]) -> object | None:
    """Pick the standard magnitude column used to sort model-facing previews."""

    normalized = {_normalize_column_name(column): column for column in columns}
    for key in MAGNITUDE_COLUMN_PRIORITY:
        column = normalized.get(key)
        if column is not None:
            return column
    return None


def is_recipe_manifest(path: str) -> bool:
    return Path(path).name.lower() in RECIPE_MANIFEST_FILES


def _normalize_column_name(column: object) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower())).strip("_")


def _primary_result_score(
    path: str,
    item: dict[str, Any],
    *,
    schema: dict[str, Any],
    preview: dict[str, Any],
) -> tuple[int, str]:
    score = 0
    reasons: list[str] = []
    name = Path(path).name.lower()
    stem = Path(path).stem.lower()
    if Path(path).suffix.lower() in {".parquet", ".csv", ".json", ".jsonl"}:
        score += 20
        reasons.append("data table")
    if schema.get("columns"):
        score += 30
        reasons.append("schema inspected")
    if isinstance(schema.get("row_count"), int) and schema.get("row_count") > 0:
        score += 20
        reasons.append("non-empty")
    if preview:
        score += 15
        reasons.append("preview available")
    if stem in {"analysis", "all_stats", "rank_stats", "all_stats_by_device", "rank_stats_by_device"}:
        score += 10
        reasons.append("standard recipe result name")
    elif any(token in name for token in ("stats", "summary", "analysis", "hist", "map", "trace", "gaps", "util")):
        score += 5
        reasons.append("result-like name")
    if int(item.get("bytes") or 0) > 0:
        score += 1
    return score, "; ".join(reasons or ["generated data file"])
