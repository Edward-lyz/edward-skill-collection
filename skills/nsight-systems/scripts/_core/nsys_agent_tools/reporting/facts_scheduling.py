"""Per-thread CPU scheduling facts: is a thread working, or stuck waiting?

Every thread is either running on a CPU or parked waiting for something. This
module turns the OS scheduling log into a simple per-thread summary so callers
never write that SQL themselves. It powers the ``thread_scheduling`` report fact
(also ``blocking_waits`` / ``sched_summary``), over the whole run or a single
frame, reporting per thread:

- upper bounds on how long it spent running vs. blocked, with confidence ratios,
  real thread IDs, and names;
- why it usually goes to sleep -- a voluntary wait, lock contention, or being
  preempted because more threads are busy than there are CPU cores;
- the specific OS wait calls (e.g. `WaitForSingleObjectEx` on Windows,
  `pthread_cond_wait` on Linux) it lost the most time to.
"""

from __future__ import annotations

from typing import Any

from .evidence import add_key
from .facts_cuda_common import _key_rows, _string_expr
from .facts_graphics_api import _resolve_frame_window
from .schema import (
    TABLE_ENUM_SCHEDULING_THREAD_BLOCK,
    TABLE_OSRT_API,
    TABLE_SCHED_EVENTS,
    TABLE_STRING_IDS,
    TABLE_THREAD_NAMES,
)
from .sql_utils import _existing_columns, _query_dicts

_MAX_QUERY_FETCH_SIZE = 100_000
_REQUIRED_SCHED_COLUMNS = {"start", "isSchedIn", "globalTid"}

# A thread's off-CPU time is often split across several block reasons. Only Keep the reasons that
# are a material share of the thread's off-CPU time.  If none pass this threshold,
# fall back to the top _TOP_MINOR_BLOCK_REASONS_COUNT reasons and let the caller see that none dominates.
_THREAD_TIME_FRACTION_THRESHOLD = 0.25
_TOP_MINOR_BLOCK_REASONS_COUNT = 4


def _window_clause(column: str, start_ns: int | None, end_ns: int | None) -> str:
    if start_ns is None or end_ns is None:
        return ""
    return f" {column} >= {int(start_ns)} AND {column} < {int(end_ns)}"


def _thread_times(
    con: Any,
    start_ns: int | None,
    end_ns: int | None,
    max_rows: int,
    order_by: str,
) -> list[dict[str, Any]] | None:
    """Per-thread on-CPU and blocked (off-CPU) nanosecond bounds; None if shape is wrong."""

    if not _REQUIRED_SCHED_COLUMNS.issubset(_existing_columns(con, TABLE_SCHED_EVENTS)):
        return None
    if order_by not in {
        "blocked_upper_bound_ns DESC",
        "on_cpu_upper_bound_ns DESC",
    }:
        raise ValueError(f"Unsupported thread scheduling order: {order_by}")

    # Attribute each interval by its starting state for the upper bounds, and
    # separately sum strict opposite-state transitions for the lower bounds.
    sched = (
        "WITH sched AS (SELECT globalTid, start, isSchedIn, "
        "LEAD(start) OVER (PARTITION BY globalTid ORDER BY start) AS next_start, "
        "LEAD(isSchedIn) OVER (PARTITION BY globalTid ORDER BY start) AS next_sched "
        f'FROM "{TABLE_SCHED_EVENTS}") '
    )
    if start_ns is not None and end_ns is not None:
        clipped_start = f"CASE WHEN start > {int(start_ns)} THEN start ELSE {int(start_ns)} END"
        clipped_end = (
            f"CASE WHEN COALESCE(next_start, {int(end_ns)}) < {int(end_ns)} "
            f"THEN COALESCE(next_start, {int(end_ns)}) ELSE {int(end_ns)} END"
        )
        duration = f"({clipped_end}) - ({clipped_start})"
        eligible = (
            f"start < {int(end_ns)} AND "
            f"COALESCE(next_start, {int(end_ns)}) > {int(start_ns)}"
        )
        on_cpu_transition = "(next_sched = 0 OR next_start IS NULL)"
        blocked_transition = "(next_sched = 1 OR next_start IS NULL)"
    else:
        duration = "next_start - start"
        eligible = "next_start IS NOT NULL"
        on_cpu_transition = "next_sched = 0"
        blocked_transition = "next_sched = 1"
    sql = sched + (
        "SELECT globalTid, "
        f"SUM(CASE WHEN isSchedIn = 1 THEN {duration} ELSE 0 END) AS on_cpu_upper_bound_ns, "
        f"SUM(CASE WHEN isSchedIn = 1 AND {on_cpu_transition} "
        f"THEN {duration} ELSE 0 END) AS on_cpu_lower_bound_ns, "
        f"SUM(CASE WHEN isSchedIn = 0 THEN {duration} ELSE 0 END) AS blocked_upper_bound_ns, "
        f"SUM(CASE WHEN isSchedIn = 0 AND {blocked_transition} "
        f"THEN {duration} ELSE 0 END) AS blocked_lower_bound_ns, "
        "SUM(CASE WHEN isSchedIn = 0 THEN 1 ELSE 0 END) AS block_events "
        f"FROM sched WHERE {eligible} "
        f"GROUP BY globalTid ORDER BY {order_by}"
    )
    return _query_dicts(con, sql, max_rows=max(2, max_rows + 1))


def _top_block_reasons_by_thread(
    con: Any, tables: set[str], start_ns: int | None, end_ns: int | None
) -> dict[int, list[dict[str, Any]]]:
    """Map globalTid to the filtered top block reasons by attributed duration."""

    columns = _existing_columns(con, TABLE_SCHED_EVENTS)
    if "threadBlock" not in columns or "isSchedIn" not in columns:
        return {}
    if TABLE_ENUM_SCHEDULING_THREAD_BLOCK in tables:
        reason_expr = "COALESCE(b.name, CAST(s.threadBlock AS TEXT))"
        join = (
            f' LEFT JOIN "{TABLE_ENUM_SCHEDULING_THREAD_BLOCK}" b '
            "ON s.threadBlock = b.id"
        )
    else:
        reason_expr = "CAST(s.threadBlock AS TEXT)"
        join = ""
    sched = (
        "WITH sched AS (SELECT globalTid, start, isSchedIn, threadBlock, "
        "LEAD(start) OVER (PARTITION BY globalTid ORDER BY start) AS next_start "
        f'FROM "{TABLE_SCHED_EVENTS}") '
    )
    if start_ns is not None and end_ns is not None:
        clipped_start = f"CASE WHEN s.start > {int(start_ns)} THEN s.start ELSE {int(start_ns)} END"
        clipped_end = (
            f"CASE WHEN COALESCE(s.next_start, {int(end_ns)}) < {int(end_ns)} "
            f"THEN COALESCE(s.next_start, {int(end_ns)}) ELSE {int(end_ns)} END"
        )
        duration = f"({clipped_end}) - ({clipped_start})"
        eligible = (
            f"s.start < {int(end_ns)} AND "
            f"COALESCE(s.next_start, {int(end_ns)}) > {int(start_ns)}"
        )
    else:
        duration = "s.next_start - s.start"
        eligible = "s.next_start IS NOT NULL"
    rows = _query_dicts(
        con,
        sched
        + f"SELECT s.globalTid AS globalTid, {reason_expr} AS reason, "
        f"COUNT(*) AS events, SUM({duration}) AS total_ns "
        f"FROM sched s{join} WHERE s.isSchedIn = 0 AND {eligible} "
        "GROUP BY globalTid, reason "
        "ORDER BY globalTid, total_ns DESC, events DESC",
        max_rows=_MAX_QUERY_FETCH_SIZE,
    )
    raw: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        gid = row.get("globalTid")
        reason = row.get("reason")
        total_ns = row.get("total_ns")
        if gid is None or reason is None or total_ns is None:
            continue
        raw.setdefault(int(gid), []).append(
            {
                "reason": str(reason),
                "events": int(row.get("events") or 0),
                "total_ns": int(total_ns),
            }
        )
    return {gid: _select_top_block_reasons(reasons) for gid, reasons in raw.items()}


def _select_top_block_reasons(reasons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select the block reasons worth reporting from a duration-sorted list.

    Concentrated blocking keeps every reason at or above _THREAD_TIME_FRACTION_THRESHOLD
    of the thread's attributed off-CPU time. If no reason clears that threshold,
    keep the top _TOP_MINOR_BLOCK_REASONS_COUNT reasons.
    """

    total_ns = sum(reason["total_ns"] for reason in reasons)
    scored: list[tuple[float, dict[str, Any]]] = []
    for reason in reasons:
        share = reason["total_ns"] / total_ns if total_ns > 0 else 0.0
        scored.append(
            (
                share,
                {
                    "reason": reason["reason"],
                    "events": reason["events"],
                    "total_ms": round(reason["total_ns"] / 1e6, 3),
                    "pct_of_off_cpu": round(share * 100, 1),
                },
            )
        )
    significant = [entry for share, entry in scored if share >= _THREAD_TIME_FRACTION_THRESHOLD]
    if significant:
        return significant
    return [entry for _, entry in scored[:_TOP_MINOR_BLOCK_REASONS_COUNT]]


def _thread_names(con: Any, tables: set[str]) -> dict[int, str]:
    """Map globalTid -> thread name via ThreadNames joined to StringIds."""

    if TABLE_THREAD_NAMES not in tables or TABLE_STRING_IDS not in tables:
        return {}
    if not {"nameId", "globalTid"}.issubset(_existing_columns(con, TABLE_THREAD_NAMES)):
        return {}
    rows = _query_dicts(
        con,
        f'SELECT t.globalTid AS globalTid, s.value AS thread_name FROM "{TABLE_THREAD_NAMES}" t '
        f'JOIN "{TABLE_STRING_IDS}" s ON t.nameId = s.id',
        max_rows=_MAX_QUERY_FETCH_SIZE,
    )
    return {
        int(row["globalTid"]): str(row["thread_name"])
        for row in rows
        if row.get("globalTid") is not None and row.get("thread_name") is not None
    }


def _blocking_waits(
    con: Any, tables: set[str], start_ns: int | None, end_ns: int | None, max_rows: int
) -> list[dict[str, Any]]:
    """Top OS-runtime wait calls (e.g. `WaitForSingleObjectEx` on Windows, `pthread_cond_wait` on Linux) ranked by total time."""

    if TABLE_OSRT_API not in tables:
        return []
    if not {"start", "end", "nameId"}.issubset(_existing_columns(con, TABLE_OSRT_API)):
        return []
    name_expr, join = _string_expr(con, TABLE_OSRT_API, "o", "nameId", tables)
    window = _window_clause("o.start", start_ns, end_ns)
    where = f" WHERE{window}" if window else ""
    rows = _query_dicts(
        con,
        f"SELECT {name_expr} AS func, COUNT(*) AS calls, "
        f'SUM(o."end" - o.start) AS total_ns, AVG(o."end" - o.start) AS avg_ns '
        f'FROM "{TABLE_OSRT_API}" o{join}{where} GROUP BY func ORDER BY total_ns DESC',
        max_rows=max(1, max_rows),
    )
    return [
        {
            "func": row["func"],
            "calls": int(row["calls"]),
            "total_ms": round(int(row["total_ns"]) / 1e6, 3),
            "avg_ms": round(float(row["avg_ns"]) / 1e6, 3),
        }
        for row in rows
        if row.get("total_ns") is not None
    ]


def _enrich_thread_rows(
    rows: list[dict[str, Any]],
    names: dict[int, str],
    top_block_reasons_by_thread: dict[int, list[dict[str, Any]]],
    window: dict[str, Any] | None,
    key_namespace: str,
) -> list[dict[str, Any]]:
    """Add thread identity, upper bounds, confidence, reasons, and stable keys."""

    threads: list[dict[str, Any]] = []
    frame_ns = int(window["end_ns"]) - int(window["start_ns"]) if window else 0
    for row in rows:
        raw_gid = row.get("globalTid")
        if raw_gid is None:
            continue
        gid = int(raw_gid)
        on_cpu_upper_bound_ns = int(row.get("on_cpu_upper_bound_ns") or 0)
        on_cpu_lower_bound_ns = int(row.get("on_cpu_lower_bound_ns") or 0)
        blocked_upper_bound_ns = int(row.get("blocked_upper_bound_ns") or 0)
        blocked_lower_bound_ns = int(row.get("blocked_lower_bound_ns") or 0)
        top_block_reasons = top_block_reasons_by_thread.get(gid, [])
        thread = {
            "global_tid": gid,
            "tid": gid & 0xFFFFFF,
            "process_id": gid >> 24,
            "thread_name": names.get(gid),
            "on_cpu_ms_upper_bound": round(on_cpu_upper_bound_ns / 1e6, 3),
            "on_cpu_confirmed_pct": (
                round(on_cpu_lower_bound_ns / on_cpu_upper_bound_ns * 100, 1)
                if on_cpu_upper_bound_ns > 0
                else None
            ),
            "blocked_ms_upper_bound": round(blocked_upper_bound_ns / 1e6, 3),
            "blocked_confirmed_pct": (
                round(blocked_lower_bound_ns / blocked_upper_bound_ns * 100, 1)
                if blocked_upper_bound_ns > 0
                else None
            ),
            "block_events": int(row.get("block_events") or 0),
            "dominant_block_reason": (
                top_block_reasons[0]["reason"] if top_block_reasons else None
            ),
            "top_block_reasons": top_block_reasons,
        }
        if frame_ns > 0:
            thread["on_cpu_pct_of_frame"] = round(
                on_cpu_upper_bound_ns / frame_ns * 100,
                3,
            )
            thread["blocked_pct_of_frame"] = round(
                blocked_upper_bound_ns / frame_ns * 100,
                3,
            )
        threads.append(add_key(thread, key_namespace, gid))
    return threads


def _thread_scheduling_summary(
    con: Any,
    tables: set[str],
    *,
    multi_report: bool,
    frame: int | None,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    """Per-thread on-CPU and blocked (off-CPU) nanosecond duration sums. Sched event
    sequences that express schedIn 0 followed by schedIn 0 can happen with some threads
    on Windows. Therefore, the sum of durations without these gaps, and the one with
    these gaps are more like lower/upper bound on the total time rather than exact
    blocked CPU time for the thread.
    So relying on either value may be inaccurate, and this potential inaccuracy is
    communicated to the agent. It shouldn't treat the CPU on/blocked ms as verdict,
    and should depend more on magnitude and ordering instead of precision.
    """

    # Each scheduling fact returns two independent thread-time rankings, so this
    # limit keeps the combined payload similar in scale to other facts.
    max_thread_group_rows = max(max_rows // 2, 1)
    if multi_report:
        return _single_report_note(intent)
    window: dict[str, Any] | None = None
    if frame is not None:
        window = _resolve_frame_window(con, tables, frame)
        if "requested_frame_error" in window:
            return {"ok": True, "intent": intent, **window}
    start_ns = window["start_ns"] if window else None
    end_ns = window["end_ns"] if window else None
    blocked_rows = _thread_times(
        con,
        start_ns,
        end_ns,
        max_thread_group_rows,
        "blocked_upper_bound_ns DESC",
    )
    on_cpu_rows = _thread_times(
        con,
        start_ns,
        end_ns,
        max_thread_group_rows,
        "on_cpu_upper_bound_ns DESC",
    )
    if blocked_rows is None or on_cpu_rows is None:
        return _no_sched_note(intent)
    threads_by_blocked_ms_upper_bound_truncated = len(blocked_rows) > max_thread_group_rows
    threads_by_on_cpu_ms_upper_bound_truncated = len(on_cpu_rows) > max_thread_group_rows
    blocked_rows = blocked_rows[:max_thread_group_rows]
    on_cpu_rows = on_cpu_rows[:max_thread_group_rows]
    top_block_reasons_by_thread = _top_block_reasons_by_thread(
        con,
        tables,
        start_ns,
        end_ns,
    )
    names = _thread_names(con, tables)
    threads_by_blocked_ms_upper_bound = _enrich_thread_rows(
        blocked_rows,
        names,
        top_block_reasons_by_thread,
        window,
        "thread-scheduling-blocked",
    )
    threads_by_on_cpu_ms_upper_bound = _enrich_thread_rows(
        on_cpu_rows,
        names,
        top_block_reasons_by_thread,
        window,
        "thread-scheduling-on-cpu",
    )
    payload: dict[str, Any] = {
        "ok": True,
        "intent": intent,
        "scope": "frame" if window else "session",
        "threads_max_rows": max_rows,
        "threads_by_blocked_ms_upper_bound_returned_count": len(threads_by_blocked_ms_upper_bound),
        "threads_by_blocked_ms_upper_bound_truncated": (
            threads_by_blocked_ms_upper_bound_truncated
        ),
        "threads_by_on_cpu_ms_upper_bound_returned_count": len(threads_by_on_cpu_ms_upper_bound),
        "threads_by_on_cpu_ms_upper_bound_truncated": (threads_by_on_cpu_ms_upper_bound_truncated),
        "threads_by_blocked_ms_upper_bound": threads_by_blocked_ms_upper_bound,
        "threads_by_on_cpu_ms_upper_bound": threads_by_on_cpu_ms_upper_bound,
        "blocking_waits": _key_rows(
            _blocking_waits(con, tables, start_ns, end_ns, max_rows), "blocking-wait", "func"
        ),
        "note": (
            "threads_by_blocked_ms_upper_bound ranks blocked threads (off-CPU) by "
            "blocked_ms_upper_bound time; "
            "threads_by_on_cpu_ms_upper_bound ranks on-CPU threads by on_cpu_ms_upper_bound time. "
            "Missing thread scheduling transition events can inflate upper bounds; "
            "*_confirmed_pct is the share backed by sched-in/sched-out event pairs. "
            "Low confidence makes a bound useful for ranking, not exact timing. "
            "Frame percentages are not whole-system utilization, and neither candidate ranking proves "
            "the critical path or cause. "
            "dominant_block_reason is the longest attributed off-CPU reason; "
            "each top_block_reasons entry gives pct_of_off_cpu. Reasons at or above 25% are kept, "
            "or the top 4 when none reaches that threshold, so percentages need not sum to 100%. "
            "Limiter and background waits may be concurrent effects; "
            "blocking_waits ranks OSRT_API waits. With --frame <N>, results are frame-local; "
            "run the callstack follow-up before naming a cause (as detailed in stutter_analysis.md)."
        ),
    }
    if window:
        payload["window"] = window
    return payload
#TODO: This is a temporary constraint - we should be able to run the analysis on multiple reports. See DTSP-22718.
def _single_report_note(intent: str) -> dict[str, Any]:
    return {
        "ok": True,
        "intent": intent,
        "scope": "multi_report_unsupported",
        "threads_by_blocked_ms_upper_bound_returned_count": 0,
        "threads_by_on_cpu_ms_upper_bound_returned_count": 0,
        "note": "Thread-scheduling analysis applies to a single report; load one .nsys-rep, not a directory.",
    }


def _no_sched_note(intent: str) -> dict[str, Any]:
    return {
        "ok": True,
        "intent": intent,
        "scope": "none",
        "threads_by_blocked_ms_upper_bound_returned_count": 0,
        "threads_by_on_cpu_ms_upper_bound_returned_count": 0,
        "note": (
            "No usable SCHED_EVENTS (need start/isSchedIn/globalTid); recapture with CPU "
            "context-switch / scheduling tracing to get per-thread on-CPU and blocked-time bounds. "
            "The OSRT_API blocking-wait calls separately need --trace osrt."
        ),
    }
