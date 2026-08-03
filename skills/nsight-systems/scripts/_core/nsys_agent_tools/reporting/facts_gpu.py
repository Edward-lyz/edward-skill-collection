"""GPU identity and logical-device mapping facts."""

from __future__ import annotations

from typing import Any

from .evidence import add_key
from .gpu_mapping import active_gpu_rows
from .schema import TABLE_TARGET_INFO_GPU
from .sql_utils import _existing_columns, _query_dicts, _quote_identifier


def _gpu_device_fact(
    con: Any,
    tables: set[str],
    max_rows: int,
    *,
    multi_report: bool,
    report_count: int,
    display_label: str,
) -> dict[str, Any]:
    """Return table-ready GPU identity facts.

    GPU attribution is easy to phrase incorrectly in multi-report workflows:
    activity tables use report-local logical GPU IDs, while physical metadata
    lives in ``TARGET_INFO_GPU``. This payload returns both the visible GPU
    metadata and, when kernel activity is present, the active logical-GPU to
    physical-GPU mapping scoped by report label.
    """

    rows = _gpu_rows(con, max_rows)
    active_rows = active_gpu_rows(con, tables, max_rows)
    names = sorted(
        {
            str(row.get("name"))
            for row in [*active_rows, *rows]
            if row.get("name") not in (None, "")
        }
    )
    active_ids = sorted(
        {
            int(row["logical_gpu_id"])
            for row in active_rows
            if isinstance(row.get("logical_gpu_id"), int)
        }
    )
    visible_ids = {
        row.get("id")
        for row in rows
        if row.get("id") not in (None, "")
    }
    payload: dict[str, Any] = {
        "ok": True,
        "intent": "gpu_devices",
        "input_label": display_label,
        "multi_report": multi_report,
        "report_count": int(report_count or 1),
        "rows": rows,
        "summary": {
            "gpu_model_names": names,
            "active_logical_gpu_ids": active_ids,
            "visible_logical_gpu_count": len(visible_ids) if visible_ids else len(rows),
            "visible_physical_gpu_count": len(visible_ids) if visible_ids else len(rows),
            "active_mapping_rows": len(active_rows),
        },
        "answer_guidance": (
            "Use active_gpu_rows for questions about GPUs being used by kernel activity; "
            "rows lists visible GPU metadata and may include GPUs with no kernel activity. "
            "When physical_gpu_id differs from logical_gpu_id, report both or use physical_gpu_id "
            "for hardware/metrics attribution. "
            "For multi-report inputs, say 'loaded report directory' or 'loaded reports' "
            "instead of singular 'this report'. If active_gpu_rows is present and small, "
            "prefer a concise Markdown table with report_label, logical_gpu_id, physical_gpu_id, name, and busLocation."
        ),
    }
    if active_rows:
        payload["active_gpu_rows"] = active_rows
    return payload


def _gpu_rows(con: Any, max_rows: int) -> list[dict[str, Any]]:
    columns = _existing_columns(con, TABLE_TARGET_INFO_GPU)
    wanted = [
        "id",
        "name",
        "busLocation",
        "chipName",
        "computeMajor",
        "computeMinor",
        "smCount",
        "totalMemory",
        "memoryBandwidth",
        "clockRate",
        "uuid",
    ]
    selected = [column for column in wanted if column in columns]
    if not selected:
        return []
    # Multi-report parquet unions can contain the same visible GPUs once per
    # report/rank. Group by human-facing device identity first so a directory
    # report returns GPU IDs 0..N instead of repeated rows for the first reports.
    grouping_columns = [column for column in selected if column != "uuid"]
    if grouping_columns:
        select_exprs = [_quote_identifier(column) for column in grouping_columns]
        if "uuid" in columns:
            select_exprs.append("COUNT(DISTINCT uuid) AS distinct_uuid_count")
            select_exprs.append("MIN(uuid) AS sample_uuid")
        sql = (
            "SELECT "
            + ", ".join(select_exprs)
            + f' FROM "{TABLE_TARGET_INFO_GPU}" GROUP BY '
            + ", ".join(_quote_identifier(column) for column in grouping_columns)
            + ' ORDER BY id, name LIMIT ?'
        )
    else:
        sql = f'SELECT DISTINCT * FROM "{TABLE_TARGET_INFO_GPU}" LIMIT ?'
    rows = _query_dicts(con, sql, max_rows=max_rows, params=(max_rows,), suppress_errors=False)
    return [
        add_key(row, "gpu-metadata", row.get("id"), row.get("busLocation"), row.get("sample_uuid") or row.get("uuid"))
        for row in rows
    ]
