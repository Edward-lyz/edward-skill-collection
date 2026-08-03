"""Small shared helpers for response guardrail checks."""

from __future__ import annotations

from typing import Any


def _mentions_any(text: str, needles: set[str]) -> bool:
    return any(needle in text for needle in needles)


def _successful_tool_names(trace: list[dict[str, Any]]) -> set[str]:
    # Evidence traces must explicitly mark successful tools. Treating missing
    # outcomes as success can hide malformed traces and over-credit evidence.
    return {
        str(item.get("tool"))
        for item in trace
        if str(item.get("outcome", "")).lower() in {"ok", "success"}
    }
