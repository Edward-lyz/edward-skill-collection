"""Table-name helpers for runtime-owned tabular artifacts."""

from __future__ import annotations

import re
from pathlib import Path


def safe_table_name(name: str) -> str:
    """Return a DuckDB-safe table name derived from a file stem."""

    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"table_{cleaned}"
    return cleaned


def unique_table_name(base: str, used: set[str]) -> str:
    """Return a table name that is unique within one tabular artifact load."""

    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}_{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def tabular_table_names(paths: list[Path]) -> dict[str, str]:
    """Map relative/absolute tabular file paths to generated DuckDB table names.

    ``ReportRuntime.load`` creates one DuckDB table per CSV/Parquet file.  The
    table name is derived from the file stem and de-duplicated in load order.
    Recipe-output schema payloads expose this mapping so agents query stable
    in-database table names instead of attempting local file reads.
    """

    used: set[str] = set()
    names: dict[str, str] = {}
    for path in paths:
        names[path.as_posix()] = unique_table_name(safe_table_name(path.stem), used)
    return names
