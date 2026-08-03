"""Graphics frame facts: locate a CPU frame's window and scan it for evidence."""

from __future__ import annotations

from typing import Any

from .evidence import add_key
from .schema import (
    TABLE_DXGI_API,
    TABLE_ETW_EVENTS,
    TABLE_GENERIC_EVENT_TYPES,
    TABLE_GPU_CONTEXT_SWITCH,
    TABLE_OPENGL_API,
    TABLE_STRING_IDS,
    TABLE_VULKAN_API,
    TABLE_WDDM_DMA_PACKET_START,
    TABLE_WDDM_EVICT_ALLOCATION,
    TABLE_WDDM_PAGING_QUEUE_PACKET_INFO,
)
from .sql_utils import _existing_columns, _query_dicts, _scalar, _sql_string

# DxgKrnl Present kernel event; ids 42/43/184 exist, 184 avoids duplicates.
DXGKRNL_PRESENT_EVENT_ID = 184
_NEIGHBORHOOD = 5
_MAX_FRAMES = 200_000
_ANALYSIS_DETAILS = "ANALYSIS_DETAILS"

# (api table, preferred present-call names, StringIds LIKE pattern, source label)
_GRAPHICS_SOURCES = (
    (TABLE_DXGI_API, ("IDXGISwapChain::Present", "IDXGISwapChain1::Present1"), "%Present%", "dxgi_api"),
    (TABLE_VULKAN_API, ("vkQueuePresentKHR",), "%QueuePresent%", "vulkan_api"),
    (TABLE_OPENGL_API, ("wglSwapBuffers", "eglSwapBuffers", "glXSwapBuffers", "SwapBuffers"), "%SwapBuffers%", "opengl_api"),
)

# Cause-family tables: WDDM paging/scheduling events (not in the ETW stream) whose
# in-window rate rises during a stutter. Tuple is (table, time column, label);
# the WDDM packet tables key on start, GPU_CONTEXT_SWITCH on timestamp.
_WDDM_CAUSE_TABLES = (
    (TABLE_WDDM_EVICT_ALLOCATION, "start", "evictions"),
    (TABLE_WDDM_PAGING_QUEUE_PACKET_INFO, "start", "paging_packets"),
    (TABLE_WDDM_DMA_PACKET_START, "start", "dma_packets"),
    (TABLE_GPU_CONTEXT_SWITCH, "timestamp", "gpu_context_switches"),
)


def _detect_present_call(con: Any, table: str, preferred: tuple[str, ...], like: str) -> str | None:
    rows = _query_dicts(
        con,
        f'SELECT s.value AS name, COUNT(*) AS cnt FROM "{table}" d '
        f'JOIN "{TABLE_STRING_IDS}" s ON d.nameId = s.id '
        f"WHERE s.value LIKE {_sql_string(like)} GROUP BY s.value ORDER BY cnt DESC",
        max_rows=20,
    )
    counts = {str(row["name"]): int(row["cnt"]) for row in rows if row.get("name")}
    if not counts:
        return None
    return next((call for call in preferred if call in counts), max(counts, key=counts.__getitem__))


def _etw_present_source(con: Any, tables: set[str]) -> tuple[str | None, str | None, str | None]:
    """DxgKrnl ETW Present source, used when no graphics API present rows exist."""

    if not {TABLE_ETW_EVENTS, TABLE_GENERIC_EVENT_TYPES} <= tables:
        return None, None, None
    etw_filter = (
        f'FROM "{TABLE_ETW_EVENTS}" e JOIN "{TABLE_GENERIC_EVENT_TYPES}" t ON e.typeId = t.typeId '
        f"WHERE t.etwEventId = {DXGKRNL_PRESENT_EVENT_ID} AND e.opcode = 0"
    )
    if (_scalar(con, f"SELECT COUNT(*) {etw_filter}") or 0) <= 0:
        return None, None, None
    return (
        "etw_dxgkrnl_present",
        f"SELECT e.timestamp AS start_ns {etw_filter}",
        f"DxgKrnl Present (etwEventId={DXGKRNL_PRESENT_EVENT_ID}, opcode 0)",
    )


def _resolve_source(con: Any, tables: set[str]) -> tuple[str | None, str | None, str | None]:
    for table, preferred, like, label in _GRAPHICS_SOURCES:
        if table in tables:
            call = _detect_present_call(con, table, preferred, like)
            if call:
                query = (
                    f'SELECT d.start AS start_ns FROM "{table}" d '
                    f'JOIN "{TABLE_STRING_IDS}" s ON d.nameId = s.id '
                    f"WHERE s.value = {_sql_string(call)}"
                )
                return label, query, call
    return _etw_present_source(con, tables)


def _analysis_window_end(con: Any) -> int | None:
    """Valid analysis-window end (ns); excludes warm-up and sentinel timestamps."""

    for sql in (
        f'SELECT duration FROM "{_ANALYSIS_DETAILS}" LIMIT 1',
        f'SELECT TraceDurationInNs FROM "{_ANALYSIS_DETAILS}" LIMIT 1',
        f"SELECT CAST(value AS BIGINT) FROM \"{_ANALYSIS_DETAILS}\" WHERE key = 'TraceDurationInNs' LIMIT 1",
    ):
        value = _scalar(con, sql)
        if value is not None:
            return int(value)
    return None


def _frame_starts(con: Any, tables: set[str]) -> tuple[str | None, str | None, list[int]]:
    """Resolve the present source and return sorted, in-window present timestamps."""

    source, query, present_call = _resolve_source(con, tables)
    if query is None:
        return None, None, []
    window_end = _analysis_window_end(con)
    starts = sorted(
        value
        for value in (
            int(row["start_ns"])
            for row in _query_dicts(con, query, max_rows=_MAX_FRAMES, suppress_errors=False)
            if row.get("start_ns") is not None
        )
        if value >= 0 and (window_end is None or value <= window_end)
    )
    return source, present_call, starts


def _percentile(sorted_values: list[float], fraction: float) -> float | None:
    if not sorted_values:
        return None
    rank = fraction * (len(sorted_values) - 1)
    low = int(rank)
    high = min(low + 1, len(sorted_values) - 1)
    return round(sorted_values[low] + (sorted_values[high] - sorted_values[low]) * (rank - low), 3)


def _frame_row(frame_num: int, starts: list[int]) -> dict[str, Any]:
    # Frame N is the interval ending at the Nth present (GUI convention).
    end_ns = starts[frame_num]
    start_ns = starts[frame_num - 1] if frame_num >= 1 else None
    frame_ms = round((end_ns - start_ns) / 1e6, 3) if start_ns is not None else None
    return add_key(
        {"frame_num": frame_num, "start_ns": start_ns, "end_ns": end_ns, "frame_ms": frame_ms},
        "graphics-frame",
        frame_num,
    )


def _window_event_counts(con: Any, start_ns: int, end_ns: int, max_rows: int) -> list[dict[str, Any]]:
    duration_ms = (end_ns - start_ns) / 1e6
    rows = _query_dicts(
        con,
        f'SELECT s.value AS event_name, COUNT(*) AS cnt FROM "{TABLE_ETW_EVENTS}" e '
        f'JOIN "{TABLE_GENERIC_EVENT_TYPES}" t ON e.typeId = t.typeId '
        f'JOIN "{TABLE_STRING_IDS}" s ON t.nameId = s.id '
        "WHERE e.timestamp >= ? AND e.timestamp < ? "
        "GROUP BY s.value ORDER BY cnt DESC",
        max_rows=max(1, max_rows),
        params=(start_ns, end_ns),
        suppress_errors=False,
    )
    return [
        {
            "event_name": row["event_name"],
            "count": int(row["cnt"]),
            "per_ms": round(int(row["cnt"]) / duration_ms, 4) if duration_ms > 0 else None,
        }
        for row in rows
    ]


def _window_wddm_counts(con: Any, tables: set[str], start_ns: int, end_ns: int) -> dict[str, dict[str, Any]]:
    duration_ms = (end_ns - start_ns) / 1e6
    counts: dict[str, dict[str, Any]] = {}
    for table, time_col, label in _WDDM_CAUSE_TABLES:
        if table not in tables or time_col not in _existing_columns(con, table):
            continue
        total = _scalar(
            con,
            f'SELECT COUNT(*) FROM "{table}" WHERE {time_col} >= {int(start_ns)} AND {time_col} < {int(end_ns)}',
        )
        count = int(total or 0)
        counts[label] = {
            "count": count,
            "per_ms": round(count / duration_ms, 4) if duration_ms > 0 else None,
        }
    return counts


def _frame_summary(
    con: Any,
    tables: set[str],
    *,
    multi_report: bool,
    frame: int | None,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    """Locate graphics frames and their time windows; return per-frame CPU timing."""

    if multi_report:
        return _single_report_note(intent)
    source, present_call, starts = _frame_starts(con, tables)
    if not starts:
        return _no_frames_note(intent)
    total_frames = len(starts)
    durations_ms = sorted((starts[i] - starts[i - 1]) / 1e6 for i in range(1, total_frames))
    median = _percentile(durations_ms, 0.5)
    slowest = sorted(
        ((i, (starts[i] - starts[i - 1]) / 1e6) for i in range(1, total_frames)),
        key=lambda pair: pair[1],
        reverse=True,
    )
    payload: dict[str, Any] = {
        "ok": True,
        "intent": intent,
        "source": source,
        "present_call": present_call,
        "total_frames": total_frames,
        "frame_time_ms": {
            "min": round(durations_ms[0], 3) if durations_ms else None,
            "median": median,
            "p95": _percentile(durations_ms, 0.95),
            "p99": _percentile(durations_ms, 0.99),
            "max": round(durations_ms[-1], 3) if durations_ms else None,
        },
        "slowest_frames": [_frame_row(i, starts) for i, _ in slowest[: max(1, max_rows)]],
        "note": (
            "frame_num is 0-indexed (GUI order); frame N is the interval ending at present N, "
            "window [start_ns, end_ns). CPU present times -- with DLSS Frame Generation the cadence "
            "bunches (see stutter_analysis.md). Scan a frame's window with frame_scan."
        ),
    }
    if median:
        short_frames = sum(1 for duration in durations_ms if duration < 0.5 * median)
        if short_frames:
            payload["short_frame_count"] = short_frames
    frame_index = frame
    if frame_index is not None and 0 <= frame_index < total_frames:
        low = max(0, frame_index - _NEIGHBORHOOD)
        high = min(total_frames, frame_index + _NEIGHBORHOOD + 1)
        payload["requested_frame"] = _frame_row(frame_index, starts)
        payload["neighbors"] = [_frame_row(i, starts) for i in range(low, high)]
    elif frame_index is not None:
        payload["requested_frame_error"] = f"frame {frame_index} is out of range (0..{max(0, total_frames - 1)})."
    if total_frames >= _MAX_FRAMES:
        payload["truncated"] = True
    return payload


def _frame_scan(
    con: Any,
    tables: set[str],
    *,
    multi_report: bool,
    frame: int | None,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    """Scan a frame's window for ETW event evidence, against a baseline neighbor."""

    if multi_report:
        return _single_report_note(intent)
    if frame is None:
        return {
            "ok": True,
            "intent": intent,
            "note": "Pass --frame <N> (a frame number from frame_summary) to scan that frame's window.",
        }
    if not {TABLE_ETW_EVENTS, TABLE_GENERIC_EVENT_TYPES, TABLE_STRING_IDS} <= tables:
        return {
            "ok": True,
            "intent": intent,
            "source": "no_etw",
            "note": "No ETW generic events to scan; this cause-scan covers ETW driver/kernel events.",
        }
    source, _, starts = _frame_starts(con, tables)
    if not starts:
        return _no_frames_note(intent)
    frame_index = frame
    if not 1 <= frame_index < len(starts):
        return {
            "ok": True,
            "intent": intent,
            "requested_frame_error": f"frame {frame_index} is out of range (1..{len(starts) - 1}).",
        }
    durations = [(i, starts[i] - starts[i - 1]) for i in range(1, len(starts))]
    sorted_durations = sorted(duration for _, duration in durations)
    median = sorted_durations[len(sorted_durations) // 2] if sorted_durations else 0
    neighbors = [
        (i, duration)
        for i, duration in durations
        if i != frame_index and abs(i - frame_index) <= _NEIGHBORHOOD
    ]
    baseline_index = min(neighbors, key=lambda pair: abs(pair[1] - median))[0] if neighbors else None
    win_start, win_end = starts[frame_index - 1], starts[frame_index]
    payload: dict[str, Any] = {
        "ok": True,
        "intent": intent,
        "source": source,
        "frame": _frame_row(frame_index, starts),
        "window_events": _window_event_counts(con, win_start, win_end, max_rows),
        "window_wddm": _window_wddm_counts(con, tables, win_start, win_end),
        "note": (
            "Counts are evidence, not a verdict. Compare matching per_ms rates against baseline_*; "
            "an unchanged or lower rate does not support attribution. window_events lists ETW event "
            "rates; window_wddm lists paging, eviction, DMA, and context-switch rates. Confirm "
            "magnitude, temporal order, and entity attribution (stutter_analysis.md)."
        ),
    }
    if baseline_index is not None:
        base_start, base_end = starts[baseline_index - 1], starts[baseline_index]
        payload["baseline_frame"] = _frame_row(baseline_index, starts)
        payload["baseline_events"] = _window_event_counts(con, base_start, base_end, max_rows)
        payload["baseline_wddm"] = _window_wddm_counts(con, tables, base_start, base_end)
    return payload

#TODO: This is a temporary constraint - we should be able to run the analysis on multiple reports. See DTSP-22718.
def _single_report_note(intent: str) -> dict[str, Any]:
    return {
        "ok": True,
        "intent": intent,
        "source": "multi_report_unsupported",
        "total_frames": 0,
        "note": "Frame analysis applies to a single report; load one .nsys-rep, not a directory.",
    }


def _no_frames_note(intent: str) -> dict[str, Any]:
    return {
        "ok": True,
        "intent": intent,
        "source": "none",
        "total_frames": 0,
        "note": (
            "No graphics API present calls (DXGI/Vulkan/OpenGL) and no DxgKrnl ETW Present "
            "(etwEventId=184) found; recapture with a graphics API or ETW present trace."
        ),
    }
