"""Nsight Compute handoff facts derived from CUDA kernel activity."""

from __future__ import annotations

from typing import Any

from .evidence import add_key
from .facts_cuda_common import _first_existing_column, _report_label_expr, _string_expr
from .schema import TABLE_CUDA_KERNEL
from .sql_utils import _existing_columns, _query_dicts


def _nsight_compute_handoff_candidates(con: Any, tables: set[str], max_rows: int) -> dict[str, Any]:
    """Identify kernels that are good candidates for separate Nsight Compute inspection.

    Nsight Systems can rank candidate kernels by timeline impact and launch
    context, but it cannot prove kernel-internal causes such as occupancy,
    memory stalls, or source-line bottlenecks. Keep the payload as handoff
    metadata instead of pretending to run or replace Nsight Compute.
    """

    columns = _existing_columns(con, TABLE_CUDA_KERNEL)
    required = {"start", "end"}
    if not required.issubset(columns):
        missing = ", ".join(sorted(required - set(columns)))
        return {
            "ok": False,
            "intent": "nsight_compute_handoff",
            "error": f"{TABLE_CUDA_KERNEL} is missing required timing column(s): {missing}.",
        }
    name_column = _first_existing_column(columns, "demangledName", "shortName", "mangledName", "nameId")
    if name_column:
        name_expr, join = _string_expr(con, TABLE_CUDA_KERNEL, "k", name_column, tables)
    else:
        name_expr, join = "'<unknown-kernel>'", ""
    report_expr = _report_label_expr(columns, "k")
    select_terms = [
        f"{report_expr} AS report_label",
        f"{name_expr} AS kernel_name",
        "COUNT(*) AS launch_count",
        'SUM(k."end" - k.start) AS total_duration_ns',
        'MAX(k."end" - k.start) AS max_duration_ns',
        'AVG(k."end" - k.start) AS mean_duration_ns',
        "MIN(k.start) AS first_start_ns",
        'MAX(k."end") AS last_end_ns',
    ]
    group_terms = ["report_label", "kernel_name"]
    if "deviceId" in columns:
        select_terms.append("MIN(k.deviceId) AS example_device_id")
    if "contextId" in columns:
        select_terms.append("MIN(k.contextId) AS example_context_id")
    if "streamId" in columns:
        select_terms.append("MIN(k.streamId) AS example_stream_id")
    for column in ("gridX", "gridY", "gridZ", "blockX", "blockY", "blockZ"):
        if column in columns:
            select_terms.append(f"MIN(k.{column}) AS example_{column}")
    rows = _query_dicts(
        con,
        f"""
        SELECT {", ".join(select_terms)}
        FROM "{TABLE_CUDA_KERNEL}" k
        {join}
        GROUP BY {", ".join(group_terms)}
        ORDER BY total_duration_ns DESC, max_duration_ns DESC, launch_count DESC
        LIMIT ?
        """,
        max_rows=max_rows,
        params=(max_rows,),
        suppress_errors=False,
    )
    if not rows:
        return {
            "ok": False,
            "intent": "nsight_compute_handoff",
            "error": "No CUDA kernel rows were available for handoff ranking.",
        }
    keyed_rows = []
    for row in rows:
        candidate = add_key(
            row, "nsight-compute-handoff-candidate", row.get("report_label"), row.get("kernel_name")
        )
        candidate["handoff_reason"] = (
            "Candidate ranked by total kernel duration in the Nsight Systems timeline. "
            "Use Nsight Compute separately to validate kernel-internal bottlenecks."
        )
        keyed_rows.append(candidate)
    return {
        "ok": True,
        "intent": "nsight_compute_handoff",
        "metric": "candidate_kernels_by_total_duration",
        "rows": keyed_rows,
        "handoff_boundary": (
            "This is Nsight Systems handoff metadata only. It identifies candidate kernels and launch context; "
            "it does not execute Nsight Compute and does not prove occupancy, stall, SASS, or source-line causes."
        ),
        "answer_guidance": (
            "Recommend a separate Nsight Compute inspection for material candidate kernels. "
            "Do not invent exact Nsight Compute or ncu command flags; inspect live Nsight Compute help or user-provided workflow evidence first."
        ),
    }
