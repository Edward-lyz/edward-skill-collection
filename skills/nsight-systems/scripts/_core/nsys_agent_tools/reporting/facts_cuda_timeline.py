"""CUDA kernel timeline coverage facts."""

from __future__ import annotations

from typing import Any

from .evidence import add_key
from .facts_cuda_common import _report_label_expr
from .schema import (
    SYNTHETIC_REPORT_LABEL,
    TABLE_CUDA_GRAPH_TRACE,
    TABLE_CUDA_KERNEL,
    TABLE_GPU_METRICS,
    TABLE_TARGET_INFO_GPU_METRICS,
)
from .sql_utils import _existing_columns, _query_dicts, _scalar

TIMELINE_GROUP_LIMIT = 64
TINY_KERNEL_WINDOW_MAX_COUNT = 5
TINY_KERNEL_WINDOW_MAX_SPAN_NS = 1_000_000


def _timeline_summary(
    con: Any, tables: set[str], *, intent: str, multi_report: bool
) -> dict[str, Any]:
    """Summarize kernel timeline coverage without pretending it is exact SM utilization."""

    columns = _existing_columns(con, TABLE_CUDA_KERNEL)
    device_expr = "deviceId" if "deviceId" in columns else "0"
    report_expr = _report_label_expr(columns)
    groups = _query_dicts(
        con,
        f"""
        SELECT {report_expr} AS report_label,
               {device_expr} AS device_id,
               COUNT(*) AS kernel_count,
               MIN(start) AS first_kernel_start_ns,
               MAX("end") AS last_kernel_end_ns,
               SUM("end" - start) AS summed_kernel_duration_ns
        FROM "{TABLE_CUDA_KERNEL}"
        GROUP BY report_label, device_id
        ORDER BY report_label, device_id
        LIMIT ?
        """,
        max_rows=TIMELINE_GROUP_LIMIT,
        params=(TIMELINE_GROUP_LIMIT,),
        suppress_errors=False,
    )
    groups = [
        add_key(row, "timeline-coverage", row.get("report_label"), row.get("device_id"))
        for row in groups
    ]
    for row in groups:
        span = int(row.get("last_kernel_end_ns") or 0) - int(row.get("first_kernel_start_ns") or 0)
        summed = int(row.get("summed_kernel_duration_ns") or 0)
        row["kernel_timeline_span_ns"] = max(0, span)
        row["kernel_time_over_timeline_ratio_upper_bound"] = (summed / span) if span > 0 else None
        if (
            int(row.get("kernel_count") or 0) < TINY_KERNEL_WINDOW_MAX_COUNT
            or span < TINY_KERNEL_WINDOW_MAX_SPAN_NS
        ):
            row["coverage_scope"] = "tiny_kernel_window"
    gpu_metric_samples = (
        _scalar(con, f'SELECT COUNT(*) FROM "{TABLE_GPU_METRICS}"')
        if TABLE_GPU_METRICS in tables
        else None
    )
    gpu_metric_definitions = (
        _scalar(con, f'SELECT COUNT(*) FROM "{TABLE_TARGET_INFO_GPU_METRICS}"')
        if TABLE_TARGET_INFO_GPU_METRICS in tables
        else None
    )
    cuda_graph_trace_events = (
        _scalar(con, f'SELECT COUNT(*) FROM "{TABLE_CUDA_GRAPH_TRACE}"')
        if TABLE_CUDA_GRAPH_TRACE in tables
        else None
    )
    has_report_label = SYNTHETIC_REPORT_LABEL in columns
    gap_partition = f"{report_expr}, {device_expr}" if multi_report and has_report_label else device_expr
    top_gaps = _query_dicts(
        con,
        f"""
        SELECT report_label, device_id, gap_ns
        FROM (
          SELECT {report_expr} AS report_label,
                 {device_expr} AS device_id,
                 start - LAG("end") OVER (
                   PARTITION BY {gap_partition}
                   ORDER BY start
                 ) AS gap_ns
          FROM "{TABLE_CUDA_KERNEL}"
        )
        WHERE gap_ns IS NOT NULL AND gap_ns > 0
        ORDER BY gap_ns DESC
        LIMIT 5
        """,
        max_rows=5,
        suppress_errors=False,
    )
    top_gaps = [
        add_key(
            row, "kernel-idle-gap", row.get("report_label"), row.get("device_id"), row.get("gap_ns")
        )
        for row in top_gaps
    ]
    payload: dict[str, Any] = {
        "ok": True,
        "intent": intent,
        "metric": "kernel_timeline_coverage",
        "rows": groups,
        "top_idle_gaps": top_gaps,
        "gpu_metrics_present": bool(gpu_metric_samples),
        "gpu_metric_sample_count": gpu_metric_samples,
        "gpu_metric_definition_count": gpu_metric_definitions,
        "cuda_graph_trace_present": bool(cuda_graph_trace_events),
        "cuda_graph_trace_event_count": cuda_graph_trace_events,
        "note": (
            "The ratio is summed kernel duration divided by kernel timeline span. "
            "It covers only the first-to-last kernel window for each device/report. "
            "It is an upper-bound activity signal, not hardware SM utilization and not whole-report utilization. "
            "Use GPU metric tables or utilization recipes when exact utilization is required."
        ),
    }
    if intent == "gpu_utilization":
        payload["utilization_answer_guidance"] = _utilization_answer_guidance(
            groups,
            gpu_metric_samples=gpu_metric_samples,
        )
    if gpu_metric_samples:
        payload["note"] += (
            " GPU_METRICS samples are present; query metric tables or use a utilization recipe for exact hardware utilization."
        )
    if cuda_graph_trace_events:
        payload["note"] += (
            " CUDA Graph trace events are present; do not treat a low kernel launch count alone as proof of no GPU workload."
        )
    return payload


def _utilization_answer_guidance(
    groups: list[dict[str, Any]],
    *,
    gpu_metric_samples: int | None,
) -> dict[str, Any]:
    """Explain whether a low/high-utilization conclusion is supported."""

    total_kernels = sum(int(row.get("kernel_count") or 0) for row in groups)
    max_span_ns = max((int(row.get("kernel_timeline_span_ns") or 0) for row in groups), default=0)
    tiny_window = (
        total_kernels < TINY_KERNEL_WINDOW_MAX_COUNT
        or max_span_ns < TINY_KERNEL_WINDOW_MAX_SPAN_NS
    )
    if gpu_metric_samples:
        state = "gpu_metrics_present_not_aggregated"
        guidance = (
            "Do not conclude low or high hardware utilization from kernel timeline coverage alone. "
            "GPU metric samples are present; aggregate the relevant metric samples or run a utilization recipe."
        )
    elif tiny_window:
        state = "insufficient_tiny_kernel_window"
        guidance = (
            "Do not answer low/high utilization. The report has too little kernel activity to infer hardware utilization, "
            "and no GPU metric aggregate was computed."
        )
    else:
        state = "kernel_activity_upper_bound_only"
        guidance = "You may report kernel timeline coverage as an activity upper bound, but say it is not exact SM utilization."
    return {
        "state": state,
        "total_kernel_count": total_kernels,
        "max_kernel_timeline_span_ns": max_span_ns,
        "guidance": guidance,
    }
