"""Shared Parquet export and DuckDB cache helpers for native reports."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ..process_utils import run_bounded_process, stderr_progress_heartbeat
from ..prompt_safety import sanitize_text
from ..tabular_tables import safe_table_name as _safe_table_name
from .duckdb_backend import _import_duckdb
from .file_utils import safe_child_files
from .sql_utils import _multi_report_table_sql
from .types import ReportError

if TYPE_CHECKING:
    from .runtime import ReportRuntime


FULL_EXPORT_MARKER = ".nsys-agent-full-export.json"
SCOPED_EXPORT_MARKER = ".nsys-agent-scoped-export.json"

# nsys export streams a `[===35%]` progress bar to stderr; match the percent.
_EXPORT_PERCENT = re.compile(r"(\d+)%")


@dataclass(frozen=True)
class PreparedParquetExport:
    """One private Parquet export used to build a DuckDB report cache."""

    path: Path
    report_label: str
    report_index: int


def prepare_parquet_exports(
    runtime: ReportRuntime,
    reports: tuple[Path, ...],
    export_root: Path,
    *,
    table_patterns: tuple[str, ...] = (),
) -> list[PreparedParquetExport]:
    """Return per-report Parquet exports, reusing valid sidecar exports.

    Export directories intentionally use the same ``<report>_pqtdir`` layout
    that the Nsight Systems recipe framework uses for ``--export-dir``. This
    makes raw report exports a shared cache for deterministic report facts,
    bounded SQL, and official recipe execution. Recipe result files still live
    under the recipe-output store; only raw report tables are shared here.

    Scoped callers pass ``table_patterns`` and export only missing requested
    tables. Full-cache callers pass no patterns; they create/update the export
    directory and write a local marker once a full export has completed for the
    report identity encoded in ``export_root``.
    """

    export_root.mkdir(parents=True, exist_ok=True)
    requested_tables = tuple(dict.fromkeys(table_patterns))
    prepared: list[PreparedParquetExport] = []
    for index, report in enumerate(reports):
        output_dir = export_root / report_parquetdir_name(report)
        if _needs_export(output_dir, requested_tables):
            export_report_parquetdir(
                runtime,
                report,
                output_dir,
                table_patterns=_missing_requested_tables(output_dir, requested_tables),
            )
            if requested_tables:
                _write_scoped_export_marker(output_dir, requested_tables)
            else:
                _write_full_export_marker(output_dir)
        prepared.append(PreparedParquetExport(output_dir, report.name, index))
    return prepared


def report_parquetdir_name(report: Path) -> str:
    """Return the recipe-compatible Parquet directory name for ``report``."""

    return f"{report.with_suffix('').name}_pqtdir"


def full_parquet_exports_ready(reports: tuple[Path, ...], export_root: Path) -> bool:
    """Return whether every report has a marked complete raw export."""

    return all(
        _full_export_marker_complete(export_root / report_parquetdir_name(report))
        and bool(safe_child_files(export_root / report_parquetdir_name(report), "*.parquet"))
        for report in reports
    )


def _needs_export(output_dir: Path, requested_tables: tuple[str, ...]) -> bool:
    if requested_tables:
        return bool(_missing_requested_tables(output_dir, requested_tables))
    return not _full_export_marker_complete(output_dir) or not safe_child_files(
        output_dir,
        "*.parquet",
    )


def _missing_requested_tables(output_dir: Path, requested_tables: tuple[str, ...]) -> tuple[str, ...]:
    if not requested_tables:
        return ()
    if _full_export_marker_complete(output_dir):
        return ()
    attempted = _read_scoped_export_marker(output_dir)
    return tuple(
        table
        for table in requested_tables
        if table not in attempted and not _literal_table_exported(output_dir, table)
    )


def _full_export_marker(output_dir: Path) -> Path:
    return output_dir / FULL_EXPORT_MARKER


def _full_export_marker_complete(output_dir: Path) -> bool:
    try:
        payload = json.loads(_full_export_marker(output_dir).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        payload.get("schema") == "nsys-agent-full-parquet-export-v1"
        and payload.get("complete") is True
    )


def _write_full_export_marker(output_dir: Path) -> None:
    payload = {
        "schema": "nsys-agent-full-parquet-export-v1",
        "complete": True,
    }
    _write_json_atomic(_full_export_marker(output_dir), payload)


def _scoped_export_marker(output_dir: Path) -> Path:
    return output_dir / SCOPED_EXPORT_MARKER


def _read_scoped_export_marker(output_dir: Path) -> set[str]:
    try:
        payload = json.loads(_scoped_export_marker(output_dir).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    patterns = payload.get("attempted_table_patterns", [])
    return {str(pattern) for pattern in patterns if str(pattern)}


def _write_scoped_export_marker(output_dir: Path, requested_tables: tuple[str, ...]) -> None:
    attempted = _read_scoped_export_marker(output_dir)
    attempted.update(requested_tables)
    payload = {
        "schema": "nsys-agent-scoped-parquet-export-v1",
        "attempted_table_patterns": sorted(attempted),
    }
    _write_json_atomic(_scoped_export_marker(output_dir), payload)


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _literal_table_exported(output_dir: Path, table_pattern: str) -> bool:
    if not re.fullmatch(r"[A-Za-z0-9_]+", table_pattern):
        return False
    return (output_dir / f"{table_pattern}.parquet").is_file()


def export_report_parquetdir(
    runtime: ReportRuntime,
    report: Path,
    output_dir: Path,
    *,
    table_patterns: tuple[str, ...] = (),
) -> None:
    """Export one native `.nsys-rep` to a private Parquet directory."""

    cmd = [runtime.nsys_path, "export"]
    if table_patterns:
        cmd.extend(["--tables", ",".join(table_patterns), "--append"])
    else:
        cmd.extend(["--force-overwrite", "true"])
    cmd.extend(
        [
            "--type",
            "parquetdir",
            "--quiet",
            "false",
            "--output",
            str(output_dir),
            str(report),
        ]
    )
    # A large capture can take minutes with no stdout, so tap the export's progress,
    # and heartbeat the latest percent to stderr to keep the step visibly alive.
    latest_percent: dict[str, int | None] = {"pct": None}

    def _note_progress(chunk: str) -> None:
        matches = _EXPORT_PERCENT.findall(chunk)
        if matches:
            latest_percent["pct"] = min(100, int(matches[-1]))

    label = f"Materializing report cache for {report.name}"
    with stderr_progress_heartbeat(
        label,
        interval_s=runtime.export_progress_interval_s,
        progress=lambda: latest_percent["pct"],
    ):
        completed = run_bounded_process(
            cmd,
            timeout_s=runtime.export_timeout_s,
            stderr_tap=_note_progress,
        )
    if completed.returncode != 0 or not safe_child_files(output_dir, "*.parquet"):
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
        raise ReportError(f"nsys export to parquetdir failed for {report.name}: {sanitize_text(detail)}")


def build_report_duckdb(db_path: Path, exports: list[PreparedParquetExport]) -> None:
    """Build a DuckDB database with one union table per Parquet table name."""

    if not exports:
        raise ReportError("No reports were provided for DuckDB cache build")
    table_files: dict[str, list[tuple[Path, str, int]]] = {}
    for export in exports:
        for parquet in safe_child_files(export.path, "*.parquet"):
            table_files.setdefault(_safe_table_name(parquet.stem), []).append(
                (parquet, export.report_label, export.report_index)
            )
    if not table_files:
        raise ReportError("No parquet tables were produced by report export")
    tmp_db = db_path.with_suffix(".building.duckdb")
    if tmp_db.exists():
        tmp_db.unlink()
    duckdb = _import_duckdb()
    with duckdb.connect(str(tmp_db)) as con:
        for table, files in sorted(table_files.items()):
            con.execute(_multi_report_table_sql(table, files))
    tmp_db.replace(db_path)
