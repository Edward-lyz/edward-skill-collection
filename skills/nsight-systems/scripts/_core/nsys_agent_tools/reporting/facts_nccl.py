"""NCCL report facts."""

from __future__ import annotations

from typing import Any

from .evidence import add_key
from .facts_cuda_common import _first_existing_column, _string_expr
from .schema import SYNTHETIC_REPORT_LABEL, TABLE_CUDA_KERNEL
from .sql_utils import _existing_columns, _query_dicts, _quote_identifier


def _nccl_distribution(con: Any, tables: set[str], *, multi_report: bool) -> dict[str, Any]:
    nccl_tables = [table for table in sorted(tables) if "NCCL" in table.upper()]
    for table in nccl_tables:
        columns = _existing_columns(con, table)
        if "start" not in columns or "end" not in columns:
            continue
        report_expr = SYNTHETIC_REPORT_LABEL if SYNTHETIC_REPORT_LABEL in columns else "'loaded-report'"
        group_clause = "GROUP BY report_label" if multi_report and SYNTHETIC_REPORT_LABEL in columns else ""
        rows = _query_dicts(
            con,
            f"""
            SELECT {report_expr} AS report_label,
                   COUNT(*) AS event_count,
                   AVG("end" - start) AS mean_duration_ns,
                   MAX("end" - start) AS max_duration_ns,
                   MIN("end" - start) AS min_duration_ns,
                   SUM("end" - start) AS total_duration_ns
            FROM {_quote_identifier(table)}
            WHERE "end" IS NOT NULL AND start IS NOT NULL AND "end" >= start
            {group_clause}
            ORDER BY total_duration_ns DESC
            LIMIT 32
            """,
            max_rows=32,
            suppress_errors=False,
        )
        return {
            "ok": True,
            "intent": "nccl_distribution",
            "metric": "duration_by_report" if group_clause else "duration_summary",
            "table": table,
            "rows": [add_key(row, "nccl-distribution", table, row.get("report_label")) for row in rows],
        }
    if TABLE_CUDA_KERNEL in tables:
        kernel_rows = _nccl_named_kernel_rows(con, tables, multi_report=multi_report)
        if kernel_rows:
            return {
                "ok": True,
                "intent": "nccl_distribution",
                "metric": "kernel_name_evidence_without_nccl_event_table",
                "table": TABLE_CUDA_KERNEL,
                "nccl_event_table_present": False,
                "rows": kernel_rows,
                "answer_guidance": (
                    "These are CUDA kernel names containing 'nccl', not NCCL API or collective event-table rows. "
                    "Use them as evidence that NCCL kernels executed, but do not claim NCCL tracing tables are present."
                ),
            }
    return {
        "ok": False,
        "intent": "nccl_distribution",
        "error": "No NCCL event table with start/end duration columns or NCCL-named CUDA kernels were found.",
    }


def _nccl_named_kernel_rows(con: Any, tables: set[str], *, multi_report: bool) -> list[dict[str, Any]]:
    """Return NCCL-looking CUDA kernels when no NCCL event table is available."""

    columns = _existing_columns(con, TABLE_CUDA_KERNEL)
    name_column = _kernel_name_column(columns)
    if name_column is None:
        return []
    name_expr, join = _string_expr(con, TABLE_CUDA_KERNEL, "k", name_column, tables)
    report_expr = f"k.{SYNTHETIC_REPORT_LABEL}" if SYNTHETIC_REPORT_LABEL in columns else "'loaded-report'"
    report_select = f"{report_expr} AS report_label, " if multi_report and SYNTHETIC_REPORT_LABEL in columns else ""
    report_group = "report_label, " if multi_report and SYNTHETIC_REPORT_LABEL in columns else ""
    rows = _query_dicts(
        con,
        f"""
        SELECT {report_select}
               {name_expr} AS kernel_name,
               COUNT(*) AS launch_count,
               SUM(k."end" - k.start) AS total_duration_ns,
               MAX(k."end" - k.start) AS max_duration_ns
        FROM "{TABLE_CUDA_KERNEL}" k
        {join}
        WHERE LOWER({name_expr}) LIKE '%nccl%'
          AND k."end" IS NOT NULL
          AND k.start IS NOT NULL
          AND k."end" >= k.start
        GROUP BY {report_group}kernel_name
        ORDER BY total_duration_ns DESC
        LIMIT 16
        """,
        max_rows=16,
        suppress_errors=False,
    )
    return [
        add_key(
            {
                **row,
                "evidence_type": "cuda_kernel_name_contains_nccl",
            },
            "nccl-kernel-name",
            row.get("report_label"),
            row.get("kernel_name"),
        )
        for row in rows
    ]


def _kernel_name_column(columns: set[str]) -> str | None:
    return _first_existing_column(columns, "demangledName", "shortName", "mangledName", "nameId")
