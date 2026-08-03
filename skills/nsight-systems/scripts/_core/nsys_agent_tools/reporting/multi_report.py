"""Multi-report directory handling backed by Parquet exports and DuckDB unions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .boundary_guidance import report_boundary_guidance
from .cache_events import cache_event, cache_timer_start, elapsed_ms
from .cache_keys import multi_report_cache_key
from .cache_manifest import write_duckdb_cache_manifest
from .connection import connect_session
from .doctor import doctor_worst_status, run_doctor_checks
from .duckdb_backend import _import_duckdb
from .errors import _safe_report_error
from .evidence import (
    add_key,
    capabilities_from_tables,
    capability_guidance,
    report_evidence,
)
from .facts_general import _report_highlights
from .file_utils import file_lock
from .parquet_cache import build_report_duckdb, prepare_parquet_exports
from .schema import interesting_tables
from .sql_utils import _install_query_timeout
from .types import ReportError, ReportSession

if TYPE_CHECKING:
    from .runtime import ReportRuntime


def multi_report_context(runtime: ReportRuntime, session: ReportSession, *, sample_limit: int = 4) -> dict[str, Any]:
    reports = list(session.multi_reports)
    samples = [
        add_key({"report_label": report.name}, "report-sample", report.name)
        for report in reports[:sample_limit]
    ]
    errors: list[dict[str, str]] = []
    highlights: dict[str, Any] = {}
    evidence_session = session
    try:
        prepared = load_multi_report_duckdb(runtime, session)
        evidence_session = prepared
        table_union = set(runtime.tables(prepared))
        with connect_session(prepared) as con:
            highlights = _report_highlights(con, table_union)
    except Exception as exc:  # noqa: BLE001 - context should preserve partial coverage
        table_union = set()
        errors.append({"report_label": session.display_label, "error": _safe_report_error(exc, session.input_path)})
    capabilities = capabilities_from_tables(table_union)
    evidence = report_evidence(evidence_session, command="nsys_get_report_context")
    payload = {
        "report_label": session.display_label,
        "paths_hidden": True,
        "source": "directory_nsys_reports_duckdb" if table_union else session.source,
        "evidence": evidence,
        "cache": evidence["cache"],
        "boundary_guidance": report_boundary_guidance(),
        "capabilities": capabilities,
        "capability_guidance": capability_guidance(capabilities),
        "report_count": len(reports),
        "sampled_report_count": len(samples),
        "partial_coverage": bool(errors),
        "tables": [
            add_key({"name": name, "rows": None}, "report-table", name)
            for name in sorted(table_union)
        ],
        "table_count": len(table_union),
        "interesting_tables": interesting_tables(table_union),
        "report_samples": samples,
        "errors": errors[:20],
        **highlights,
        "note": (
            "Directory context uses the multi-report DuckDB/parquet cache; it does not "
            "export sampled reports to SQLite. Direct SQL is available through union "
            "tables with __report_label and __report_index columns; group by "
            "__report_label for per-rank/per-report conclusions."
        ),
    }
    if len(reports) > len(samples):
        payload["report_samples_note"] = (
            "report_samples is a bounded preview. Use __report_label from SQL/fact rows "
            "as the stable citation anchor for reports not shown in the preview."
        )
    return payload


def multi_report_doctor(runtime: ReportRuntime, session: ReportSession) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    checks: list[dict[str, Any]] = []
    evidence_session = session
    try:
        prepared = load_multi_report_duckdb(runtime, session)
        evidence_session = prepared
        with connect_session(prepared) as con:
            _install_query_timeout(con, 15.0)
            tables = set(runtime.tables(prepared))
            checks = run_doctor_checks(con, tables, runtime.doctor_thresholds)
    except Exception as exc:  # noqa: BLE001 - preserve a JSON diagnostic
        errors.append({"report_label": session.display_label, "error": _safe_report_error(exc, session.input_path)})
    status = doctor_worst_status(checks)
    evidence = report_evidence(evidence_session, command="nsys_report_doctor")
    return {
        "ok": not errors or bool(checks),
        "report_label": session.display_label,
        "paths_hidden": True,
        "source": "directory_nsys_reports_duckdb" if checks else session.source,
        "evidence": evidence,
        "cache": evidence["cache"],
        "status": status,
        "report_count": len(session.multi_reports),
        "partial_coverage": bool(errors),
        "checks": checks,
        "errors": errors[:20],
        "note": (
            "Multi-report doctor uses the DuckDB/parquet cache for the whole report directory; "
            "it does not export sampled reports to SQLite."
        ),
    }


def load_multi_report_duckdb(
    runtime: ReportRuntime,
    session: ReportSession,
    *,
    table_patterns: tuple[str, ...] = (),
) -> ReportSession:
    """Build a DuckDB query session for a directory of native reports."""

    if not session.multi_reports:
        raise ReportError("multi-report DuckDB requires a directory report session")
    _import_duckdb()
    start = cache_timer_start()
    base_key = multi_report_cache_key(session.multi_reports, runtime.nsys_path)
    export_root = runtime.cache_dir / f"multi-{base_key}-parquet"
    lock_path = runtime.cache_dir / f"multi-{base_key}.lock"
    if table_patterns:
        full_db_path = runtime.cache_dir / f"multi-{base_key}.duckdb"
        full_manifest_path = full_db_path.with_suffix(full_db_path.suffix + ".manifest.json")
        if full_db_path.is_file() and full_manifest_path.is_file():
            return ReportSession(
                session.input_path,
                None,
                "directory_nsys_reports_duckdb",
                duckdb_path=full_db_path,
                parquet_root=export_root,
                report_count=len(session.multi_reports),
                cache_events=(
                    cache_event("duckdb_cache", hit=True, start=start, scoped=False),
                ),
            )
    key = multi_report_cache_key(
        session.multi_reports,
        runtime.nsys_path,
        table_patterns=table_patterns,
    )
    db_path = runtime.cache_dir / f"multi-{key}.duckdb"
    manifest_path = db_path.with_suffix(db_path.suffix + ".manifest.json")
    if db_path.is_file() and manifest_path.is_file():
        return ReportSession(
            session.input_path,
            None,
            "directory_nsys_reports_duckdb",
            duckdb_path=db_path,
            parquet_root=export_root,
            report_count=len(session.multi_reports),
            cache_events=(cache_event("duckdb_cache", hit=True, start=start, scoped=bool(table_patterns)),),
        )
    lock_start = cache_timer_start()
    with file_lock(lock_path, timeout_s=runtime.cache_lock_timeout_s(len(session.multi_reports))):
        lock_wait_ms = elapsed_ms(lock_start)
        built = False
        if not db_path.is_file():
            exported = prepare_parquet_exports(
                runtime,
                session.multi_reports,
                export_root,
                table_patterns=table_patterns,
            )
            build_report_duckdb(db_path, exported)
            built = True
        if built or not manifest_path.is_file():
            write_duckdb_cache_manifest(
                manifest_path,
                nsys_path=runtime.nsys_path,
                inputs=list(session.multi_reports),
                db_path=db_path,
                export_type="multi-report-parquet-duckdb",
            )
    return ReportSession(
        session.input_path,
        None,
        "directory_nsys_reports_duckdb",
        duckdb_path=db_path,
        parquet_root=export_root,
        report_count=len(session.multi_reports),
        cache_events=(
            cache_event(
                "duckdb_cache",
                hit=not built,
                start=start,
                scoped=bool(table_patterns),
                lock_wait_ms=lock_wait_ms,
            ),
        ),
    )
