"""CUDA memcpy/memset summary facts."""

from __future__ import annotations

from typing import Any

from .evidence import add_key
from .facts_cuda_common import _enum_expr, _first_existing_column
from .schema import (
    TABLE_CUDA_MEMCPY,
    TABLE_CUDA_MEMSET,
    TABLE_ENUM_CUDA_MEM_KIND,
    TABLE_ENUM_CUDA_MEMCPY_OPER,
)
from .sql_utils import _existing_columns, _query_dicts, _quote_identifier


def _memory_summary(con: Any, tables: set[str], max_rows: int, metric: str = "") -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    if TABLE_CUDA_MEMCPY in tables:
        label_expr, join = _enum_expr(
            con,
            source_table=TABLE_CUDA_MEMCPY,
            source_alias="m",
            source_column="copyKind",
            enum_table=TABLE_ENUM_CUDA_MEMCPY_OPER,
            enum_alias="e",
            tables=tables,
        )
        rows.extend(
            _query_dicts(
                con,
                f"""
                SELECT 'Memcpy' AS operation_type,
                       {label_expr} AS operation_label,
                       m.copyKind AS operation_id,
                       COUNT(*) AS operation_count,
                       SUM(m.bytes) AS total_bytes,
                       MAX(m."end" - m.start) AS max_duration_ns,
                       SUM(m."end" - m.start) AS total_duration_ns
                FROM "{TABLE_CUDA_MEMCPY}" m
                {join}
                GROUP BY operation_label, m.copyKind
                ORDER BY total_duration_ns DESC
                LIMIT ?
                """,
                max_rows=max_rows,
                params=(max_rows,),
                suppress_errors=False,
            )
        )
    if TABLE_CUDA_MEMSET in tables:
        columns = _existing_columns(con, TABLE_CUDA_MEMSET)
        kind_col = _first_existing_column(columns, "memKind", "memoryKind")
        if kind_col:
            label_expr, join = _enum_expr(
                con,
                source_table=TABLE_CUDA_MEMSET,
                source_alias="ms",
                source_column=kind_col,
                enum_table=TABLE_ENUM_CUDA_MEM_KIND,
                enum_alias="e",
                tables=tables,
            )
            rows.extend(
                _query_dicts(
                    con,
                    f"""
                    SELECT 'Memset' AS operation_type,
                           {label_expr} AS operation_label,
                           ms.{_quote_identifier(kind_col)} AS operation_id,
                           COUNT(*) AS operation_count,
                           SUM(ms.bytes) AS total_bytes,
                           MAX(ms."end" - ms.start) AS max_duration_ns,
                           SUM(ms."end" - ms.start) AS total_duration_ns
                    FROM "{TABLE_CUDA_MEMSET}" ms
                    {join}
                    GROUP BY operation_label, ms.{_quote_identifier(kind_col)}
                    ORDER BY total_duration_ns DESC
                    LIMIT ?
                    """,
                    max_rows=max_rows,
                    params=(max_rows,),
                    suppress_errors=False,
                )
            )
    sort_field, normalized_metric = _memory_sort(metric)
    rows.sort(key=lambda row: int(row.get(sort_field) or 0), reverse=True)
    if not rows:
        return {
            "ok": False,
            "intent": "memcpy_summary",
            "error": "No CUDA memcpy/memset activity table is present in this report.",
        }
    return {
        "ok": True,
        "intent": "memcpy_summary",
        "metric": normalized_metric,
        "summary": "memory_operations_by_kind",
        "rows_sorted_by": sort_field,
        "rows": [
            add_key(
                row,
                "memory-summary",
                row.get("operation_type"),
                row.get("operation_id"),
                row.get("operation_label"),
            )
            for row in rows[:max_rows]
        ],
    }


def _memory_sort(metric: str) -> tuple[str, str]:
    metric = metric.strip().lower()
    if metric in {"bytes", "size", "total_bytes", "memory_size", "largest_bytes"}:
        return "total_bytes", "total_bytes"
    if metric in {"count", "operation_count", "ops"}:
        return "operation_count", "operation_count"
    return "total_duration_ns", "total_duration"
