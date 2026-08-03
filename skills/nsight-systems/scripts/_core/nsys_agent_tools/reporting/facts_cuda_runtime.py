"""CUDA runtime/API timing facts."""

from __future__ import annotations

from typing import Any

from .evidence import add_key
from .facts_cuda_common import _grouped_row_counts, _key_rows, _report_select_group, _string_expr
from .schema import TABLE_CUDA_RUNTIME
from .sql_utils import _existing_columns, _query_dicts


def _runtime_summary(con: Any, tables: set[str], metric: str, max_rows: int) -> dict[str, Any]:
    name_expr, join = _string_expr(con, TABLE_CUDA_RUNTIME, "r", "nameId", tables)
    runtime_columns = _existing_columns(con, TABLE_CUDA_RUNTIME)
    if metric in {"", "execution_time", "duration"}:
        return _runtime_time_interpretations(
            con, name_expr, join, max_rows, runtime_columns=runtime_columns
        )
    order_expr = {
        "count": "call_count DESC",
        "most_frequent": "call_count DESC",
        "sum_duration": "total_duration_ns DESC",
        "total_duration": "total_duration_ns DESC",
        "total_time": "total_duration_ns DESC",
        "mean_duration": "mean_duration_ns DESC",
        "avg_duration": "mean_duration_ns DESC",
        "max_single_duration": "max_duration_ns DESC",
        "longest": "max_duration_ns DESC",
    }.get(metric)
    if not order_expr:
        return {
            "ok": False,
            "intent": "cuda_api_summary",
            "metric": metric,
            "error": "Unsupported cuda_api_summary metric.",
        }
    rows = _runtime_rows(
        con, name_expr, join, order_expr, max_rows, runtime_columns=runtime_columns
    )
    payload: dict[str, Any] = {
        "ok": True,
        "intent": "cuda_api_summary",
        "metric": metric,
        "rows": rows,
    }
    if metric in {"count", "most_frequent"}:
        row_counts = _grouped_row_counts(con, TABLE_CUDA_RUNTIME)
        payload["runtime_table_row_counts"] = [
            add_key({"report_label": label, "row_count": count}, "cuda-runtime-row-count", label)
            for label, count in sorted(row_counts.items())
        ]
        payload["answer_guidance"] = (
            "`rows` ranks API names by call_count. If the user asks for total CUDA runtime table rows "
            "per report, answer from runtime_table_row_counts instead."
        )
    if metric in {"sum_duration", "total_duration", "total_time", "mean_duration", "avg_duration"}:
        # Ambiguous user wording ("highest execution time") commonly needs
        # both total and mean perspectives. Include single-row alternates so
        # the model can answer without issuing multiple tool calls.
        if metric not in {"sum_duration", "total_duration", "total_time"}:
            payload["top_by_total_duration"] = _runtime_rows(
                con,
                name_expr,
                join,
                "total_duration_ns DESC",
                1,
                runtime_columns=runtime_columns,
            )
        if metric not in {"mean_duration", "avg_duration"}:
            payload["top_by_mean_duration"] = _runtime_rows(
                con,
                name_expr,
                join,
                "mean_duration_ns DESC",
                1,
                runtime_columns=runtime_columns,
            )
        payload["metric_note"] = (
            "Execution time can mean total duration, mean duration per call, or longest single call."
        )
    return payload


def _runtime_time_interpretations(
    con: Any,
    name_expr: str,
    join: str,
    max_rows: int,
    *,
    runtime_columns: set[str],
) -> dict[str, Any]:
    """Return common API-time interpretations for unqualified timing questions."""

    return {
        "ok": True,
        "intent": "cuda_api_summary",
        "metric": "api_time_interpretations",
        "preferred_primary_metric": "mean_duration",
        "metric_note": (
            "Unqualified API execution time is ambiguous. Use mean_duration as the concise primary answer; "
            "also mention total duration and longest single call when they identify different APIs."
        ),
        "answer_guidance": (
            "When a report is loaded, do not answer only conceptually. Include the top API name and value "
            "for mean duration, total duration, and max single-call duration so the user can see why the wording is ambiguous."
        ),
        "top_by_mean_duration": _runtime_rows(
            con,
            name_expr,
            join,
            "mean_duration_ns DESC",
            max_rows,
            runtime_columns=runtime_columns,
        ),
        "top_by_total_duration": _runtime_rows(
            con,
            name_expr,
            join,
            "total_duration_ns DESC",
            min(max_rows, 5),
            runtime_columns=runtime_columns,
        ),
        "top_by_max_single_duration": _runtime_rows(
            con,
            name_expr,
            join,
            "max_duration_ns DESC",
            min(max_rows, 5),
            runtime_columns=runtime_columns,
        ),
    }


def _runtime_rows(
    con: Any,
    name_expr: str,
    join: str,
    order_expr: str,
    max_rows: int,
    *,
    runtime_columns: set[str],
) -> list[dict[str, Any]]:
    report_select, report_group, _ = _report_select_group(runtime_columns, "r")
    rows = _query_dicts(
        con,
        f"""
        SELECT {report_select} {name_expr} AS api_name,
               COUNT(*) AS call_count,
               SUM(r."end" - r.start) AS total_duration_ns,
               AVG(r."end" - r.start) AS mean_duration_ns,
               MAX(r."end" - r.start) AS max_duration_ns,
               MIN(r."end" - r.start) AS min_duration_ns
        FROM "{TABLE_CUDA_RUNTIME}" r
        {join}
        GROUP BY {report_group}api_name
        ORDER BY {order_expr}
        LIMIT ?
        """,
        max_rows=max_rows,
        params=(max_rows,),
        suppress_errors=False,
    )
    return _key_rows(rows, "cuda-api-summary", "report_label", "api_name")
