"""JSON-safe value conversion for report query rows."""

from __future__ import annotations

from typing import Any

from ..prompt_safety import sanitize_text, sanitize_value


def _jsonable_row(row: tuple[Any, ...]) -> list[Any]:
    values: list[Any] = []
    for value in row:
        if isinstance(value, bytes):
            values.append(f"<bytes:{len(value)}>")
        elif isinstance(value, str):
            values.append(sanitize_text(value))
        elif hasattr(value, "isoformat"):
            values.append(value.isoformat())
        else:
            values.append(sanitize_value(value))
    return values


def _jsonable_rows(rows: list[tuple[Any, ...]]) -> list[list[Any]]:
    return [_jsonable_row(tuple(row)) for row in rows]
