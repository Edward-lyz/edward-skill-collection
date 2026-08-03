"""Shared SQL helpers for CUDA report facts."""

from __future__ import annotations

from typing import Any

from .evidence import add_key
from .schema import SYNTHETIC_REPORT_INDEX, SYNTHETIC_REPORT_LABEL, TABLE_STRING_IDS
from .sql_utils import _existing_columns, _query_dicts, _quote_identifier


def _string_expr(
    con: Any, source_table: str, alias: str, column: str, tables: set[str]
) -> tuple[str, str]:
    if TABLE_STRING_IDS in tables:
        scope_join = ""
        source_columns = _existing_columns(con, source_table)
        string_columns = _existing_columns(con, TABLE_STRING_IDS)
        if SYNTHETIC_REPORT_INDEX in source_columns and SYNTHETIC_REPORT_INDEX in string_columns:
            scope_join = f" AND {alias}.{SYNTHETIC_REPORT_INDEX} = s.{SYNTHETIC_REPORT_INDEX} "
        elif SYNTHETIC_REPORT_LABEL in source_columns and SYNTHETIC_REPORT_LABEL in string_columns:
            scope_join = f" AND {alias}.{SYNTHETIC_REPORT_LABEL} = s.{SYNTHETIC_REPORT_LABEL} "
        return f"COALESCE(s.value, CAST({alias}.{_quote_identifier(column)} AS TEXT))", (
            f' LEFT JOIN "{TABLE_STRING_IDS}" s ON {alias}.{_quote_identifier(column)} = s.id {scope_join}'
        )
    return f"CAST({alias}.{_quote_identifier(column)} AS TEXT)", ""


def _enum_expr(
    con: Any,
    *,
    source_table: str,
    source_alias: str,
    source_column: str,
    enum_table: str,
    enum_alias: str,
    tables: set[str],
) -> tuple[str, str]:
    """Return a report-scoped enum label expression and join.

    Multi-report DuckDB sessions union per-report enum tables. Joining only by
    enum id would multiply facts by the number of reports because enum ids are
    repeated in each report. Scope joins by the synthetic report index/label
    when those columns exist, matching the string-id join behavior above.
    """

    quoted_column = _quote_identifier(source_column)
    fallback = f"CAST({source_alias}.{quoted_column} AS TEXT)"
    if enum_table not in tables:
        return fallback, ""
    enum_columns = _existing_columns(con, enum_table)
    label_column = (
        "label" if "label" in enum_columns else "name" if "name" in enum_columns else None
    )
    if label_column is None:
        return fallback, ""
    source_columns = _existing_columns(con, source_table)
    scope_join = ""
    if SYNTHETIC_REPORT_INDEX in source_columns and SYNTHETIC_REPORT_INDEX in enum_columns:
        scope_join = (
            f" AND {source_alias}.{SYNTHETIC_REPORT_INDEX} = "
            f"{enum_alias}.{SYNTHETIC_REPORT_INDEX} "
        )
    elif SYNTHETIC_REPORT_LABEL in source_columns and SYNTHETIC_REPORT_LABEL in enum_columns:
        scope_join = (
            f" AND {source_alias}.{SYNTHETIC_REPORT_LABEL} = "
            f"{enum_alias}.{SYNTHETIC_REPORT_LABEL} "
        )
    return (
        f"COALESCE({enum_alias}.{_quote_identifier(label_column)}, {fallback})",
        f' LEFT JOIN "{enum_table}" {enum_alias} ON {source_alias}.{quoted_column} = {enum_alias}.id {scope_join}',
    )


def _grouped_row_counts(con: Any, table: str) -> dict[str, int]:
    columns = _existing_columns(con, table)
    if SYNTHETIC_REPORT_LABEL in columns:
        rows = _query_dicts(
            con,
            f'SELECT {SYNTHETIC_REPORT_LABEL} AS report_label, COUNT(*) AS row_count '
            f'FROM "{table}" GROUP BY {SYNTHETIC_REPORT_LABEL}',
            max_rows=1000,
            suppress_errors=False,
        )
        return {
            str(row["report_label"]): int(row["row_count"])
            for row in rows
            if row.get("report_label")
        }
    rows = _query_dicts(
        con, f'SELECT COUNT(*) AS row_count FROM "{table}"', max_rows=1, suppress_errors=False
    )
    return {"loaded-report": int(rows[0]["row_count"])} if rows else {}


def _report_label_expr(columns: set[str], alias: str | None = None) -> str:
    """Return the SQL expression that identifies the report for a row set."""

    if SYNTHETIC_REPORT_LABEL not in columns:
        return "'loaded-report'"
    return f"{alias}.{SYNTHETIC_REPORT_LABEL}" if alias else SYNTHETIC_REPORT_LABEL


def _report_select_group(columns: set[str], alias: str) -> tuple[str, str, bool]:
    """Return SELECT/GROUP fragments for optional multi-report labels."""

    if SYNTHETIC_REPORT_LABEL not in columns:
        return "", "", False
    return f"{alias}.{SYNTHETIC_REPORT_LABEL} AS report_label,", "report_label, ", True


def _key_rows(rows: list[dict[str, Any]], kind: str, *fields: str) -> list[dict[str, Any]]:
    return [add_key(row, kind, *(row.get(field) for field in fields)) for row in rows]


def _first_existing_column(columns: set[str], *candidates: str) -> str | None:
    """Return the first preferred schema column present in a report table."""

    return next((column for column in candidates if column in columns), None)
