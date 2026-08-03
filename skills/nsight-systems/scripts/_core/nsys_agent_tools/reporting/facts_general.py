"""General report metadata facts.

These helpers expose small context facts that are useful before the model
chooses a deeper report query: export metadata, session start time, visible GPU
metadata, system environment, and diagnostics. They are intentionally not a
natural-language router.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from .evidence import add_key
from .schema import (
    SYSTEM_ENV_CONTEXT_FIELDS,
    TABLE_DIAGNOSTIC_EVENT,
    TABLE_META_DATA_EXPORT,
    TABLE_TARGET_INFO_GPU,
    TABLE_TARGET_INFO_SESSION_START_TIME,
    TABLE_TARGET_INFO_SYSTEM_ENV,
)
from .sql_utils import (
    _execute_identifier_sql,
    _existing_columns,
    _query_dicts,
    _quote_identifier,
    _scalar,
)


def _export_schema_version(con: sqlite3.Connection) -> str | None:
    try:
        table_exists = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (TABLE_META_DATA_EXPORT,),
        ).fetchone()
        if not table_exists:
            return None
        rows = _execute_identifier_sql(
            con,
            f'SELECT name, value FROM "{TABLE_META_DATA_EXPORT}"'
        ).fetchall()
    except sqlite3.Error:
        return None
    for name, value in rows:
        if str(name) == "EXPORT_SCHEMA_VERSION":
            return str(value)
    return None


def _report_highlights(con: Any, tables: set[str]) -> dict[str, Any]:
    """Return small, high-value report facts that help the LLM choose tools."""

    highlights: dict[str, Any] = {}
    if TABLE_META_DATA_EXPORT in tables:
        highlights["export_metadata"] = [
            add_key(row, "export-metadata", row.get("name"))
            for row in _query_dicts(
                con,
                f"""
                SELECT name, value
                FROM "{TABLE_META_DATA_EXPORT}"
                WHERE name IN (
                  'EXPORT_PRODUCT_NAME',
                  'EXPORT_PRODUCT_VERSION',
                  'EXPORT_PRODUCT_DATE',
                  'EXPORT_SCHEMA_VERSION'
                )
                ORDER BY name
                """,
                max_rows=20,
            )
        ]
    if TABLE_TARGET_INFO_SESSION_START_TIME in tables:
        highlights["session_start"] = [
            add_key(row, "session-start", row.get("utcEpochNs"), row.get("utcTime"))
            for row in _query_dicts(
                con,
                f"""
                SELECT utcTime, localTime, utcEpochNs
                FROM "{TABLE_TARGET_INFO_SESSION_START_TIME}"
                LIMIT 4
                """,
                max_rows=4,
            )
        ]
    if TABLE_TARGET_INFO_GPU in tables:
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
        selected = [c for c in wanted if c in columns]
        if selected:
            sql = (
                "SELECT "
                + ", ".join(_quote_identifier(c) for c in selected)
                + f' FROM "{TABLE_TARGET_INFO_GPU}" ORDER BY id LIMIT 16'
            )
            highlights["gpus"] = [
                add_key(row, "gpu-metadata", row.get("id"), row.get("busLocation"))
                for row in _query_dicts(con, sql, max_rows=16)
            ]
    if TABLE_TARGET_INFO_SYSTEM_ENV in tables:
        placeholders = ", ".join("?" for _ in SYSTEM_ENV_CONTEXT_FIELDS)
        highlights["system_environment"] = [
            add_key(row, "system-environment", row.get("name"))
            for row in _query_dicts(
                con,
                f"""
                SELECT name, value
                FROM "{TABLE_TARGET_INFO_SYSTEM_ENV}"
                WHERE name IN ({placeholders})
                ORDER BY name
                LIMIT 20
                """,
                max_rows=20,
                params=SYSTEM_ENV_CONTEXT_FIELDS,
            )
        ]
    if TABLE_DIAGNOSTIC_EVENT in tables:
        highlights["diagnostics"] = {
            "row_count": _scalar(
                con,
                f'SELECT COUNT(*) FROM "{TABLE_DIAGNOSTIC_EVENT}"',
            ),
            "sample": [
                add_key(row, "diagnostic-event", row.get("timestamp"), row.get("severity"))
                for row in _query_dicts(
                    con,
                    f"""
                    SELECT timestamp, severity, text
                    FROM "{TABLE_DIAGNOSTIC_EVENT}"
                    ORDER BY timestamp
                    LIMIT 8
                    """,
                    max_rows=8,
                )
            ],
        }
    return highlights
