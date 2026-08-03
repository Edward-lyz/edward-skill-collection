"""Path-redacted report cache status helpers.

Status inspection must not export reports. It only classifies the input and
checks whether the private Parquet/DuckDB sidecar artifacts already exist.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .cache_keys import multi_report_cache_key
from .file_utils import safe_child_files
from .parquet_cache import full_parquet_exports_ready, report_parquetdir_name

if TYPE_CHECKING:
    from .runtime import ReportRuntime


def report_cache_status(runtime: ReportRuntime, report: str | Path) -> dict[str, Any]:
    """Return cache readiness for a report path without creating artifacts."""

    path = Path(report).expanduser().resolve()
    base: dict[str, Any] = {
        "ok": path.exists(),
        "paths_hidden": True,
        "report_label": path.name or "report-directory",
    }
    if not path.exists():
        return {**base, "state": "missing", "cache_ready": False}
    if path.is_dir():
        reports = safe_child_files(path, "*.nsys-rep")
        if reports:
            status = _native_cache_status(runtime, tuple(reports), artifact_prefix="multi")
            return {
                **base,
                **status,
                "input_kind": "native_report_directory",
                "report_count": len(reports),
                "state": _native_cache_state(status),
            }
        if safe_child_files(path, "*.parquet") or safe_child_files(path, "*.csv"):
            return {
                **base,
                "input_kind": "advanced_tabular_directory",
                "backend": "duckdb",
                "cache_ready": False,
                "state": "advanced_input",
            }
        if safe_child_files(path, "*.sqlite"):
            return {
                **base,
                "input_kind": "advanced_sqlite_directory",
                "backend": "sqlite",
                "cache_ready": False,
                "state": "advanced_input",
            }
        return {
            **base,
            "ok": False,
            "input_kind": "unsupported_directory",
            "cache_ready": False,
            "state": "unsupported",
        }
    if path.suffix.lower() == ".nsys-rep":
        status = _native_cache_status(runtime, (path,), artifact_prefix="report")
        return {
            **base,
            **status,
            "input_kind": "native_report",
            "report_count": 1,
            "state": _native_cache_state(status),
        }
    if path.suffix.lower() == ".sqlite":
        return {
            **base,
            "input_kind": "advanced_sqlite",
            "backend": "sqlite",
            "cache_ready": False,
            "state": "advanced_input",
        }
    if path.suffix.lower() in {".parquet", ".csv"}:
        return {
            **base,
            "input_kind": "advanced_tabular_file",
            "backend": "duckdb",
            "cache_ready": False,
            "state": "advanced_input",
        }
    return {
        **base,
        "ok": False,
        "input_kind": "unsupported_file",
        "cache_ready": False,
        "state": "unsupported",
    }


def _native_cache_status(
    runtime: ReportRuntime,
    reports: tuple[Path, ...],
    *,
    artifact_prefix: str,
) -> dict[str, Any]:
    key = multi_report_cache_key(reports, runtime.nsys_path)
    db_path = runtime.cache_dir / f"{artifact_prefix}-{key}.duckdb"
    export_root = runtime.cache_dir / f"{artifact_prefix}-{key}-parquet"
    parquet_ready = all(
        safe_child_files(export_root / report_parquetdir_name(report), "*.parquet")
        for report in reports
    )
    full_export_ready = full_parquet_exports_ready(reports, export_root)
    cache_artifact_ready = db_path.is_file()
    return {
        "backend": "parquet_duckdb",
        "cache_artifact_label": db_path.name,
        "cache_artifact_ready": cache_artifact_ready,
        "parquet_export_label": export_root.name,
        "parquet_export_ready": parquet_ready,
        "full_parquet_export_ready": full_export_ready,
        "partial_cache_ready": cache_artifact_ready or parquet_ready,
        "cache_ready": cache_artifact_ready and parquet_ready,
    }


def _native_cache_state(status: dict[str, Any]) -> str:
    if status["cache_ready"]:
        return "ready"
    if status.get("partial_cache_ready"):
        return "partial"
    return "not_prepared"
