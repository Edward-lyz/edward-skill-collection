"""CUDA activity inventory facts."""

from __future__ import annotations

from typing import Any

from .evidence import add_key
from .facts_cuda_common import _grouped_row_counts, _report_label_expr
from .gpu_mapping import active_gpu_rows
from .schema import (
    SYNTHETIC_REPORT_LABEL,
    TABLE_CUDA_KERNEL,
    TABLE_CUDA_RUNTIME,
    TABLE_MPI_COLLECTIVES,
    TABLE_NVTX_EVENTS,
    TABLE_TARGET_INFO_GPU,
)
from .sql_utils import _existing_columns, _query_dicts


def _activity_summary(con: Any, tables: set[str], max_rows: int) -> dict[str, Any]:
    """Return per-report activity inventory for common timeline categories.

    This is a semantic convenience fact rather than a recipe replacement.  It
    prevents a common attribution mistake: joining visible GPU metadata from
    ``TARGET_INFO_GPU`` and calling every visible device "active".  Active GPU
    IDs come from kernel activity rows; visible GPUs remain metadata only.
    """

    labels = _report_labels_for_activity(con, tables, max_rows)
    active_rows = active_gpu_rows(con, tables, max_rows=max_rows * 8)
    active_by_label = _kernel_device_ids_by_label(con, tables)
    active_physical_by_label: dict[str, set[int]] = {}
    active_display_by_label: dict[str, list[str]] = {}
    for row in active_rows:
        label = str(row.get("report_label") or "loaded-report")
        logical_id = _as_int(row.get("logical_gpu_id"))
        physical_id = _as_int(row.get("physical_gpu_id"))
        if logical_id is None:
            continue
        active_by_label.setdefault(label, set()).add(logical_id)
        if physical_id is not None:
            active_physical_by_label.setdefault(label, set()).add(physical_id)
        active_display_by_label.setdefault(label, []).append(
            _active_gpu_label(
                logical_id=logical_id,
                physical_id=physical_id,
                name=str(row.get("name")) if row.get("name") else None,
            )
        )
    count_tables = {
        "kernel_rows": TABLE_CUDA_KERNEL,
        "cuda_runtime_rows": TABLE_CUDA_RUNTIME,
        "mpi_collective_rows": TABLE_MPI_COLLECTIVES,
        "nvtx_rows": TABLE_NVTX_EVENTS,
    }
    counts = {
        field: _grouped_row_counts(con, table) if table in tables else {}
        for field, table in count_tables.items()
    }
    if not labels:
        labels = sorted({label for table_counts in counts.values() for label in table_counts})
    if not labels:
        labels = ["loaded-report"]

    rows: list[dict[str, Any]] = []
    for label in labels[:max_rows]:
        active_ids = sorted(set(active_by_label.get(label, [])))
        active_display = active_display_by_label.get(label) or [str(gpu_id) for gpu_id in active_ids]
        row: dict[str, Any] = {
            "report_label": label,
            "active_logical_gpu_ids": active_ids,
            "active_physical_gpu_ids": sorted(active_physical_by_label.get(label, [])),
            "active_gpu": ", ".join(active_display) or None,
        }
        for field in count_tables:
            row[field] = counts[field].get(label, 0)
        rows.append(add_key(row, "activity-summary", label))

    return {
        "ok": True,
        "intent": "activity_summary",
        "metric": "per_report_activity_counts",
        "rows": rows,
        "active_gpu_rows": active_rows[: max_rows * 8],
        "answer_guidance": (
            "Use active_logical_gpu_ids/active_gpu for GPUs used by kernel activity. "
            "Do not substitute all visible TARGET_INFO_GPU rows for active GPUs."
        ),
    }


def _report_labels_for_activity(con: Any, tables: set[str], max_rows: int) -> list[str]:
    labels: set[str] = set()
    for table in (
        TABLE_CUDA_KERNEL,
        TABLE_CUDA_RUNTIME,
        TABLE_MPI_COLLECTIVES,
        TABLE_NVTX_EVENTS,
        TABLE_TARGET_INFO_GPU,
    ):
        if table not in tables:
            continue
        columns = _existing_columns(con, table)
        if SYNTHETIC_REPORT_LABEL not in columns:
            continue
        rows = _query_dicts(
            con,
            f'SELECT DISTINCT {SYNTHETIC_REPORT_LABEL} AS report_label '
            f'FROM "{table}" ORDER BY report_label LIMIT ?',
            max_rows=max_rows,
            params=(max_rows,),
            suppress_errors=False,
        )
        labels.update(str(row["report_label"]) for row in rows if row.get("report_label"))
    return sorted(labels)


def _kernel_device_ids_by_label(con: Any, tables: set[str]) -> dict[str, set[int]]:
    if TABLE_CUDA_KERNEL not in tables:
        return {}
    columns = _existing_columns(con, TABLE_CUDA_KERNEL)
    if "deviceId" not in columns:
        return {}
    label_expr = _report_label_expr(columns)
    rows = _query_dicts(
        con,
        f"""
        SELECT {label_expr} AS report_label, deviceId AS logical_gpu_id
        FROM "{TABLE_CUDA_KERNEL}"
        WHERE deviceId IS NOT NULL
        GROUP BY report_label, logical_gpu_id
        ORDER BY report_label, logical_gpu_id
        """,
        max_rows=1000,
        suppress_errors=False,
    )
    by_label: dict[str, set[int]] = {}
    for row in rows:
        try:
            gpu_id = int(row["logical_gpu_id"])
        except (KeyError, TypeError, ValueError):
            continue
        by_label.setdefault(str(row.get("report_label") or "loaded-report"), set()).add(gpu_id)
    return by_label


def _active_gpu_label(*, logical_id: int, physical_id: int | None, name: str | None) -> str:
    mapped_id = physical_id if physical_id is not None else logical_id
    prefix = str(logical_id) if mapped_id == logical_id else f"{logical_id}->{mapped_id}"
    return f"{prefix}:{name}" if name else prefix


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
