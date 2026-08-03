"""Small path-redacted cache timing helpers."""

from __future__ import annotations

import time
from typing import Any


def cache_timer_start() -> float:
    return time.perf_counter()


def elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000.0, 1)


def cache_event(
    stage: str,
    *,
    hit: bool,
    start: float,
    scoped: bool,
    lock_wait_ms: float | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "stage": stage,
        "hit": bool(hit),
        "scoped": bool(scoped),
        "duration_ms": elapsed_ms(start),
    }
    if lock_wait_ms is not None:
        event["lock_wait_ms"] = round(lock_wait_ms, 1)
    return event
