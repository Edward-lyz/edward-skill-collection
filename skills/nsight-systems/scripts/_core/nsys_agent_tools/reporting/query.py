"""Report context, table inspection, and bounded SQL execution."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from ..prompt_safety import sanitize_text, sanitize_value
from ..sql_guard import clean_sql, multi_report_scope_warning, validate_sql
from .boundary_guidance import (
    recipe_domain_query_warning,
    report_boundary_guidance,
)
from .connection import connect_session
from .duckdb_backend import _query_duckdb_subprocess
from .errors import _safe_error_text
from .evidence import (
    add_key,
    capabilities_from_tables,
    capability_guidance,
    report_evidence,
)
from .facts_general import _export_schema_version, _report_highlights
from .load import load_native_report_duckdb
from .multi_report import load_multi_report_duckdb, multi_report_context
from .schema import interesting_tables
from .serialization import _jsonable_row
from .sql_utils import (
    RESERVED_WORD_GUIDANCE,
    _execute_identifier_sql,
    _install_query_timeout,
    _quote_identifier,
    repair_reserved_identifiers,
)
from .types import ReportSession

if TYPE_CHECKING:
    from .runtime import ReportRuntime


def context(runtime: ReportRuntime, session: ReportSession) -> dict[str, Any]:
    if session.multi_reports:
        return multi_report_context(runtime, session)
    if session.source == "native_report":
        session = load_native_report_duckdb(runtime, session.input_path)
    tables = runtime.tables(session)
    table_rows = []
    table_errors = []
    with connect_session(session) as con:
        table_set = set(tables)
        for table in tables:
            try:
                count = _execute_identifier_sql(
                    con, "SELECT COUNT(*) FROM " + _quote_identifier(table)
                ).fetchone()[0]
            except Exception as exc:  # noqa: BLE001 - context should report partial coverage
                count = None
                table_errors.append({"table": table, "error_type": type(exc).__name__})
            table_rows.append(add_key({"name": table, "rows": count}, "report-table", table))
        schema_version = _export_schema_version(con) if session.sqlite_path else None
        highlights = _report_highlights(con, table_set)
    capabilities = capabilities_from_tables(table_set)
    evidence = report_evidence(session, command="nsys_get_report_context")
    return {
        "report_label": session.display_label,
        "paths_hidden": True,
        "source": session.source,
        "evidence": evidence,
        "cache": evidence["cache"],
        "boundary_guidance": report_boundary_guidance(),
        "capabilities": capabilities,
        "capability_guidance": capability_guidance(capabilities),
        "export_schema_version": schema_version,
        "table_count": len(tables),
        "tables": table_rows,
        "table_count_errors": table_errors[:20],
        "interesting_tables": interesting_tables(tables),
        **highlights,
    }


def tables(
    runtime: ReportRuntime,
    session: ReportSession,
    *,
    table_patterns: tuple[str, ...] = (),
) -> list[str]:
    if session.multi_reports:
        prepared = load_multi_report_duckdb(
            runtime,
            session,
            table_patterns=table_patterns,
        )
        return runtime.tables(prepared)
    if session.source == "native_report":
        prepared = load_native_report_duckdb(
            runtime,
            session.input_path,
            table_patterns=table_patterns,
        )
        return runtime.tables(prepared)
    with connect_session(session) as con:
        if session.sqlite_path:
            rows = con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        else:
            rows = con.execute("SHOW TABLES").fetchall()
    return [str(row[0]) for row in rows]


def describe_tables(runtime: ReportRuntime, session: ReportSession, tables_to_describe: list[str]) -> dict[str, Any]:
    if session.multi_reports:
        try:
            session = load_multi_report_duckdb(
                runtime,
                session,
                table_patterns=tuple(tables_to_describe),
            )
        except Exception:  # noqa: BLE001 - unknown/missing scoped tables should stay cheap
            return {
                "tables": [
                    add_key(
                        {
                            "table": table,
                            "error": "unable to prepare scoped table cache",
                        },
                        "report-table",
                        table,
                    )
                    for table in tables_to_describe
                ]
            }
    elif session.source == "native_report":
        try:
            session = load_native_report_duckdb(
                runtime,
                session.input_path,
                table_patterns=tuple(tables_to_describe),
            )
        except Exception:  # noqa: BLE001 - unknown/missing scoped tables should stay cheap
            return {
                "tables": [
                    add_key(
                        {
                            "table": table,
                            "error": "unable to prepare scoped table cache",
                        },
                        "report-table",
                        table,
                    )
                    for table in tables_to_describe
                ]
            }
    output = []
    with connect_session(session) as con:
        known = set(runtime.tables(session))
        for table in tables_to_describe:
            if table not in known:
                output.append(add_key({"table": table, "error": "unknown table"}, "report-table", table))
                continue
            if session.sqlite_path:
                columns = _execute_identifier_sql(
                    con, "PRAGMA table_info(" + _quote_identifier(table) + ")"
                ).fetchall()
                column_info = [{"name": sanitize_text(str(c[1])), "type": sanitize_text(str(c[2]))} for c in columns]
                names = [sanitize_text(str(c[1])) for c in columns]
            else:
                columns = _execute_identifier_sql(
                    con, "DESCRIBE SELECT * FROM " + _quote_identifier(table)
                ).fetchall()
                column_info = [{"name": sanitize_text(str(c[0])), "type": sanitize_text(str(c[1]))} for c in columns]
                names = [sanitize_text(str(c[0])) for c in columns]
            sample = _execute_identifier_sql(
                con, "SELECT * FROM " + _quote_identifier(table) + " LIMIT 5"
            ).fetchall()
            output.append(
                add_key(
                    {
                        "table": table,
                        "columns": column_info,
                        "sample_rows": [
                            dict(zip(names, _jsonable_row(row), strict=False))
                            for row in sample
                        ],
                    },
                    "report-table",
                    table,
                )
            )
    return {"tables": output}


def query(
    runtime: ReportRuntime,
    session: ReportSession,
    sql: str,
    *,
    max_rows: int = 100,
    max_chars: int = 40000,
    timeout_s: float = 10.0,
    question: str = "",
) -> dict[str, Any]:
    max_rows = max(1, min(int(max_rows), 1000))
    max_chars = max(1000, min(int(max_chars), 200000))
    multi_report_input = bool(session.multi_reports)
    if session.multi_reports:
        session = load_multi_report_duckdb(runtime, session)
    elif session.source == "native_report":
        session = load_native_report_duckdb(runtime, session.input_path)
    cleaned = clean_sql(sql)
    error = validate_sql(cleaned)
    if error:
        return {"ok": False, "error": error}
    recipe_domain_warning = recipe_domain_query_warning(cleaned, question=question)

    def _run_once(sql_text: str) -> tuple[list[str], list[tuple[Any, ...]]]:
        if session.duckdb_path:
            return _query_duckdb_subprocess(session.duckdb_path, sql_text, max_rows + 1, timeout_s)
        with connect_session(session) as con:
            _install_query_timeout(con, timeout_s)
            cur = con.execute(sql_text)
            return [d[0] for d in cur.description or []], cur.fetchmany(max_rows + 1)

    normalized_tokens: list[str] = []
    try:
        # DuckDB reserves keywords (e.g. ``end``) that nsys event tables use as
        # columns; quote a bare reserved identifier the parser flags and retry.
        columns, rows, normalized_tokens = repair_reserved_identifiers(_run_once, cleaned)
    except Exception as exc:
        engine = "sqlite" if session.sqlite_path else "duckdb"
        return {"ok": False, "error": f"{engine} error: {_safe_error_text(exc)}"}
    truncated_rows = len(rows) > max_rows
    rows = rows[:max_rows]
    safe_columns = [sanitize_text(str(column)) for column in columns]
    json_rows = [dict(zip(safe_columns, _jsonable_row(row), strict=False)) for row in rows]
    payload: dict[str, Any] = {
        "ok": True,
        "evidence": report_evidence(session, command="nsys_query_report"),
        "sql": sanitize_text(cleaned, max_chars=8000),
        "columns": safe_columns,
        "rows": json_rows,
        "returned_row_count": len(json_rows),
        "truncated_rows": truncated_rows,
        "row_key_policy": (
            "Ad-hoc SQL rows do not receive synthetic keys; select stable identity "
            "columns such as __report_label, ids, names, start, and end when rows "
            "must be cited or compared."
        ),
    }
    if truncated_rows:
        payload["truncation_note"] = (
            f"The result was truncated to {max_rows} rows and more rows exist. "
            "Raise the limit with --max-rows (maximum 1000), or preferably aggregate "
            "or filter in SQL with WHERE, GROUP BY, or LIMIT instead of returning raw rows."
        )
    if normalized_tokens:
        payload["normalized_identifiers"] = sorted(set(normalized_tokens))
        payload["normalized_note"] = RESERVED_WORD_GUIDANCE
    if recipe_domain_warning:
        payload["boundary_warnings"] = [recipe_domain_warning]
    if multi_report_input or session.report_count > 1:
        payload["report_count"] = session.report_count or 0
        payload["multi_report"] = True
        warning = multi_report_scope_warning(cleaned)
        if warning:
            payload["scope_warnings"] = [warning]
    serialized = json.dumps(sanitize_value(payload, max_string_chars=max_chars))
    if len(serialized) > max_chars:
        payload["ok"] = False
        payload["rows"] = []
        payload["returned_row_count"] = 0
        payload["truncated_chars"] = True
        payload["error"] = "result exceeded serialized character budget; select fewer columns"
    return payload
