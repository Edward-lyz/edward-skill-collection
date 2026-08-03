"""Derived table metadata for report-fact rows.

Report facts are JSON-first. This module adds a small optional presentation
shape so agents and UIs can render the same rows as a table without a separate
display schema for each intent. The metadata comes from row keys and scalar
values; analysis meaning stays in the fact or recipe code.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

TABLE_VIEW_SCHEMA = "nsys-report-table-view-v1"

_INTERNAL_COLUMNS = {"key"}
_ACRONYMS = {
    "api": "API",
    "cpu": "CPU",
    "cuda": "CUDA",
    "gpu": "GPU",
    "id": "ID",
    "mpi": "MPI",
    "nccl": "NCCL",
    "ns": "ns",
    "ncu": "NCU",
    "nvtx": "NVTX",
    "pci": "PCI",
    "pid": "PID",
    "sm": "SM",
    "uuid": "UUID",
}
_UNIT_SUFFIXES = (
    ("_ns", "ns"),
    ("_ms", "ms"),
    ("_us", "us"),
    ("_bytes", "bytes"),
    ("_pct", "%"),
    ("_percent", "%"),
    ("_percentage", "%"),
)


def attach_table_view(payload: dict[str, Any], *, row_field: str = "rows") -> dict[str, Any]:
    """Attach derived table metadata for row-like fields when possible."""

    if "table_view" not in payload:
        primary = table_view(payload.get(row_field), row_field=row_field)
        if primary:
            payload["table_view"] = primary
    if "table_views" not in payload:
        secondary = {
            key: view
            for key, value in payload.items()
            if key not in {row_field, "evidence", "table_view", "table_views"}
            if (view := table_view(value, row_field=key))
        }
        if secondary:
            payload["table_views"] = secondary
    return payload


def table_view(rows: object, *, row_field: str = "rows") -> dict[str, Any] | None:
    """Return an optional table-view contract derived from row dictionaries."""

    row_dicts = list(_iter_row_dicts(rows))
    if not row_dicts:
        return None
    columns = [
        _column_shape(key, row_dicts)
        for key in _ordered_scalar_keys(row_dicts)
        if key not in _INTERNAL_COLUMNS and not key.startswith("__")
    ]
    if not columns:
        return None
    return {
        "schema": TABLE_VIEW_SCHEMA,
        "row_field": row_field,
        "columns": columns,
    }


def _iter_row_dicts(rows: object) -> Iterable[Mapping[str, Any]]:
    if not isinstance(rows, list):
        return ()
    return (row for row in rows if isinstance(row, Mapping))


def _ordered_scalar_keys(rows: list[Mapping[str, Any]]) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key, value in row.items():
            if key in seen:
                continue
            if (_is_scalar(value) and value is not None) or _all_values_scalar(rows, key):
                seen.add(key)
                keys.append(str(key))
    return keys


def _all_values_scalar(rows: list[Mapping[str, Any]], key: str) -> bool:
    values = [row.get(key) for row in rows if key in row]
    return bool(values) and all(_is_scalar(value) for value in values)


def _is_scalar(value: object) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _column_shape(key: str, rows: list[Mapping[str, Any]]) -> dict[str, str]:
    unit = _unit_for_key(key)
    column: dict[str, str] = {
        "key": key,
        "label": _label_for_key(key, unit=unit),
        "type": _type_for_key(key, rows),
    }
    if unit:
        column["unit"] = unit
    return column


def _unit_for_key(key: str) -> str:
    for suffix, unit in _UNIT_SUFFIXES:
        if key.endswith(suffix):
            return unit
    return ""


def _label_for_key(key: str, *, unit: str) -> str:
    label_key = key
    if unit:
        for suffix, suffix_unit in _UNIT_SUFFIXES:
            if suffix_unit == unit and label_key.endswith(suffix):
                if suffix == "_bytes":
                    break
                label_key = label_key[: -len(suffix)]
                break
    words = [_ACRONYMS.get(part, part) for part in _label_parts(label_key)]
    if not words:
        return key
    first = words[0] if words[0].isupper() else words[0].capitalize()
    return first + (" " + " ".join(words[1:]) if len(words) > 1 else "")


def _label_parts(key: str) -> list[str]:
    snake = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key.strip("_"))
    snake = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", snake)
    return [part.lower() for part in snake.split("_") if part]


def _type_for_key(key: str, rows: list[Mapping[str, Any]]) -> str:
    values = [row.get(key) for row in rows if row.get(key) is not None]
    if not values:
        return "string"
    if all(isinstance(value, bool) for value in values):
        return "boolean"
    if all(isinstance(value, int) and not isinstance(value, bool) for value in values):
        return "integer"
    if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
        return "number"
    return "string"
