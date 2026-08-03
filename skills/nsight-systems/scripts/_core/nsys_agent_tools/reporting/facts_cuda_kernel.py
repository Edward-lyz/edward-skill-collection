"""CUDA kernel summary and duration-distribution facts."""

from __future__ import annotations

from typing import Any

from .facts_cuda_common import _key_rows, _report_select_group, _string_expr
from .schema import TABLE_CUDA_KERNEL
from .sql_utils import _existing_columns, _query_dicts

_UNIQUE_NAME_METRICS = {"count_distinct_name", "unique", "unique_kernels"}
_LAUNCH_COUNT_METRICS = {"launch_count", "total_launches", "count_all"}
_OVERALL_MEAN_METRICS = {
    "overall_mean_duration",
    "overall_avg_duration",
    "mean_launch_duration",
    "avg_launch_duration",
}

_ORDER_BY_METRIC = {
    "count": "launch_count DESC",
    "count_launches": "launch_count DESC",
    "sum_duration": "total_duration_ns DESC",
    "total_duration": "total_duration_ns DESC",
    "total_time": "total_duration_ns DESC",
    "mean_duration": "mean_duration_ns DESC",
    "avg_duration": "mean_duration_ns DESC",
    "max_single_duration": "max_duration_ns DESC",
    "longest": "max_duration_ns DESC",
}

_PRIMARY_MAX_METRICS = {"max_single_duration", "longest"}
_PRIMARY_TOTAL_METRICS = {"sum_duration", "total_duration", "total_time"}
_PRIMARY_MEAN_METRICS = {"mean_duration", "avg_duration"}
_KERNEL_DURATION_WHERE = 'WHERE "end" IS NOT NULL AND start IS NOT NULL AND "end" >= start'


def _kernel_summary(con: Any, tables: set[str], metric: str, max_rows: int) -> dict[str, Any]:
    name_expr, join = _string_expr(con, TABLE_CUDA_KERNEL, "k", "demangledName", tables)
    aggregate = _kernel_scalar_metric(con, metric, name_expr=name_expr, join=join)
    if aggregate is not None:
        return aggregate

    order_expr = _ORDER_BY_METRIC.get(metric)
    if not order_expr:
        return {
            "ok": False,
            "intent": "kernel_summary",
            "metric": metric,
            "error": "Unsupported kernel_summary metric.",
        }

    report_select, report_group = _kernel_report_grouping(con)
    rows = _kernel_summary_rows(
        con,
        name_expr=name_expr,
        join=join,
        order_expr=order_expr,
        max_rows=max_rows,
        report_select=report_select,
        report_group=report_group,
    )
    payload: dict[str, Any] = {
        "ok": True,
        "intent": "kernel_summary",
        "metric": metric,
        "rows": _key_rows(rows, "kernel-summary", "report_label", "kernel_name"),
        "answer_guidance": (
            "For cross-report or cross-rank slower/faster questions, state the comparison metric explicitly. "
            "Max single duration, total duration, mean duration, and timeline span can lead to different conclusions."
        ),
    }
    _add_kernel_comparison_rows(
        payload,
        con,
        metric=metric,
        name_expr=name_expr,
        join=join,
        max_rows=max_rows,
        report_select=report_select,
        report_group=report_group,
    )
    return payload


def _kernel_scalar_metric(
    con: Any, metric: str, *, name_expr: str, join: str
) -> dict[str, Any] | None:
    """Return single-row aggregate kernel metrics, or ``None`` for ranked metrics."""

    if metric in _UNIQUE_NAME_METRICS:
        rows = _query_dicts(
            con,
            f"SELECT COUNT(DISTINCT {name_expr}) AS unique_kernel_count, COUNT(*) AS launch_count "
            f'FROM "{TABLE_CUDA_KERNEL}" k {join}',
            max_rows=1,
            suppress_errors=False,
        )
        return {
            "ok": True,
            "intent": "kernel_summary",
            "metric": "count_distinct_name",
            **(rows[0] if rows else {}),
        }
    if metric in _LAUNCH_COUNT_METRICS:
        rows = _query_dicts(
            con,
            f'SELECT COUNT(*) AS launch_count FROM "{TABLE_CUDA_KERNEL}"',
            max_rows=1,
            suppress_errors=False,
        )
        return {
            "ok": True,
            "intent": "kernel_summary",
            "metric": "launch_count",
            **(rows[0] if rows else {}),
        }
    if metric in _OVERALL_MEAN_METRICS:
        rows = _query_dicts(
            con,
            'SELECT COUNT(*) AS launch_count, AVG("end" - start) AS mean_duration_ns '
            f'FROM "{TABLE_CUDA_KERNEL}"',
            max_rows=1,
            suppress_errors=False,
        )
        return {
            "ok": True,
            "intent": "kernel_summary",
            "metric": "overall_mean_duration",
            **(rows[0] if rows else {}),
        }
    return None


def _kernel_report_grouping(con: Any) -> tuple[str, str]:
    kernel_columns = _existing_columns(con, TABLE_CUDA_KERNEL)
    report_select, report_group, _ = _report_select_group(kernel_columns, "k")
    return report_select, report_group


def _add_kernel_comparison_rows(
    payload: dict[str, Any],
    con: Any,
    *,
    metric: str,
    name_expr: str,
    join: str,
    max_rows: int,
    report_select: str,
    report_group: str,
) -> None:
    """Attach alternate rankings for ambiguous kernel-duration questions."""

    alternates = (
        ("top_by_max_single_duration", "max_duration_ns DESC", _PRIMARY_MAX_METRICS),
        ("top_by_total_duration", "total_duration_ns DESC", _PRIMARY_TOTAL_METRICS),
        ("top_by_mean_duration", "mean_duration_ns DESC", _PRIMARY_MEAN_METRICS),
    )
    for field, order_expr, primary_metrics in alternates:
        if metric in primary_metrics:
            continue
        payload[field] = _key_rows(
            _kernel_summary_rows(
                con,
                name_expr=name_expr,
                join=join,
                order_expr=order_expr,
                max_rows=min(max_rows, 5),
                report_select=report_select,
                report_group=report_group,
            ),
            "kernel-summary",
            "report_label",
            "kernel_name",
        )


def _kernel_summary_rows(
    con: Any,
    *,
    name_expr: str,
    join: str,
    order_expr: str,
    max_rows: int,
    report_select: str,
    report_group: str,
) -> list[dict[str, Any]]:
    return _query_dicts(
        con,
        f"""
        SELECT {report_select} {name_expr} AS kernel_name,
               COUNT(*) AS launch_count,
               SUM(k."end" - k.start) AS total_duration_ns,
               AVG(k."end" - k.start) AS mean_duration_ns,
               MAX(k."end" - k.start) AS max_duration_ns,
               MIN(k."end" - k.start) AS min_duration_ns
        FROM "{TABLE_CUDA_KERNEL}" k
        {join}
        GROUP BY {report_group}kernel_name
        ORDER BY {order_expr}
        LIMIT ?
        """,
        max_rows=max_rows,
        params=(max_rows,),
        suppress_errors=False,
    )


def _kernel_variance(con: Any, tables: set[str]) -> dict[str, Any]:
    _ = tables
    summary = _query_dicts(
        con,
        f"""
        SELECT COUNT(*) AS duration_count,
               MAX("end" - start) AS max_duration_ns
        FROM "{TABLE_CUDA_KERNEL}"
        {_KERNEL_DURATION_WHERE}
        """,
        max_rows=1,
        suppress_errors=False,
    )
    if not summary:
        return {
            "ok": False,
            "intent": "kernel_variance",
            "error": "No kernel durations were available.",
        }
    duration_count = int(summary[0].get("duration_count") or 0)
    if duration_count <= 0:
        return {
            "ok": False,
            "intent": "kernel_variance",
            "error": "No valid kernel durations were available.",
        }
    p50_offsets = _percentile_offsets(duration_count, 0.50)
    p95_offsets = _percentile_offsets(duration_count, 0.95)
    durations = _durations_at_offsets(con, _duration_offset_positions(p50_offsets, p95_offsets))
    p50 = _interpolate_offsets(durations, p50_offsets)
    p95 = _interpolate_offsets(durations, p95_offsets)
    max_duration = int(summary[0].get("max_duration_ns") or 0)
    ratio = (p95 / p50) if p50 > 0 else None
    return {
        "ok": True,
        "intent": "kernel_variance",
        "metric": "duration_distribution",
        "duration_count": duration_count,
        "p50_duration_ns": p50,
        "p95_duration_ns": p95,
        "max_duration_ns": max_duration,
        "p95_over_p50": ratio,
        "note": "The distribution is computed from all valid kernel durations.",
    }


def _percentile_offsets(count: int, percentile: float) -> tuple[int, int, float]:
    if count <= 1:
        return (0, 0, 0.0)
    index = percentile * (count - 1)
    lower = int(index)
    upper = min(lower + 1, count - 1)
    return (lower, upper, index - lower)


def _durations_at_offsets(con: Any, offsets: list[int]) -> dict[int, float]:
    if not offsets:
        return {}
    placeholders = ", ".join("?" for _ in offsets)
    rows = _query_dicts(
        con,
        f"""
        SELECT rn, duration_ns
        FROM (
            SELECT ("end" - start) AS duration_ns,
                   ROW_NUMBER() OVER (ORDER BY ("end" - start)) - 1 AS rn
            FROM "{TABLE_CUDA_KERNEL}"
            {_KERNEL_DURATION_WHERE}
        )
        WHERE rn IN ({placeholders})
        """,
        max_rows=len(offsets),
        params=tuple(offsets),
        suppress_errors=False,
    )
    return {int(row["rn"]): float(row.get("duration_ns") or 0.0) for row in rows}


def _duration_offset_positions(*offsets: tuple[int, int, float]) -> list[int]:
    """Return only integer row positions needed for percentile interpolation."""

    return sorted({position for lower, upper, _fraction in offsets for position in (lower, upper)})


def _interpolate_offsets(
    durations: dict[int, float],
    offsets: tuple[int, int, float],
) -> float:
    lower, upper, fraction = offsets
    lower_value = durations.get(lower, 0.0)
    upper_value = durations.get(upper, lower_value)
    return lower_value * (1.0 - fraction) + upper_value * fraction
