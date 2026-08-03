"""CPU callstack facts: what code was a thread running, or stuck in?

This module reports what a thread was actually doing by
counting Nsight's periodic stack samples so callers never write that SQL
themselves. It powers the ``callstack_summary`` report fact (also ``hotspots``),
for all threads or one thread (pass its ``global_tid``):

- ``hotspots``: the functions where the thread spent its running time;
- ``blocked_stacks``: the exact call the thread was sitting in when it went to
  sleep (e.g. a fence or wait).
"""

from __future__ import annotations

from typing import Any

from .facts_cuda_common import _first_existing_column, _key_rows, _string_expr
from .facts_graphics_api import _resolve_frame_window
from .facts_scheduling import _thread_names
from .schema import (
    TABLE_COMPOSITE_EVENTS,
    TABLE_SAMPLING_CALLCHAINS,
    TABLE_STRING_IDS,
)
from .sql_utils import _existing_columns, _query_dicts


def _leaf_symbol_rows(
    con: Any,
    tables: set[str],
    *,
    cpu_cycles: int | None,
    gid: int | None,
    start_ns: int | None,
    end_ns: int | None,
    max_rows: int,
) -> list[dict[str, Any]] | None:
    """Top leaf (depth 0) symbols for a stack type; None if the shape is wrong."""

    sc_columns = _existing_columns(con, TABLE_SAMPLING_CALLCHAINS)
    cc_columns = _existing_columns(con, TABLE_COMPOSITE_EVENTS)
    # Native nsys exports name these `symbol`/`stackDepth`; accept the older
    # `symbolId`/`depth` spelling too so both schema variants resolve.
    symbol_col = _first_existing_column(sc_columns, "symbol", "symbolId")
    depth_col = _first_existing_column(sc_columns, "stackDepth", "depth")
    if symbol_col is None or "id" not in sc_columns or "id" not in cc_columns:
        return None
    name_expr, join = _string_expr(con, TABLE_SAMPLING_CALLCHAINS, "sc", symbol_col, tables)
    terms: list[str] = []
    if cpu_cycles is not None and "cpuCycles" in cc_columns:
        terms.append(f"ce.cpuCycles = {int(cpu_cycles)}")
    if depth_col is not None:
        terms.append(f"sc.{depth_col} = 0")
    if gid is not None and "globalTid" in cc_columns:
        terms.append(f"ce.globalTid = {int(gid)}")
    if start_ns is not None and end_ns is not None:
        terms.append(f"ce.start >= {int(start_ns)} AND ce.start < {int(end_ns)}")
    where = (" WHERE " + " AND ".join(terms)) if terms else ""
    # GROUP BY position avoids ambiguity when symbol_col is literally `symbol`
    # (the SELECT alias would otherwise collide with the base column).
    sql = (
        f"SELECT {name_expr} AS symbol, COUNT(*) AS n "
        f'FROM "{TABLE_SAMPLING_CALLCHAINS}" sc '
        f'JOIN "{TABLE_COMPOSITE_EVENTS}" ce ON sc.id = ce.id'
        f"{join}{where} GROUP BY 1 ORDER BY n DESC"
    )
    return _query_dicts(con, sql, max_rows=max(1, max_rows))


def _callstack_summary(
    con: Any,
    tables: set[str],
    *,
    multi_report: bool,
    metric: str,
    frame: int | None,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    """Leaf-symbol hotspots (cpuCycles=1) and blocked stacks (cpuCycles=0)."""

    if multi_report:
        return _single_report_note(intent)
    if TABLE_COMPOSITE_EVENTS not in tables or TABLE_STRING_IDS not in tables:
        return _no_samples_note(intent)
    gid = int(metric) if metric.isdigit() else None
    cc_columns = _existing_columns(con, TABLE_COMPOSITE_EVENTS)
    has_cpu_cycles = "cpuCycles" in cc_columns
    window: dict[str, Any] | None = None
    if frame is not None:
        window = _resolve_frame_window(con, tables, frame)
        if "requested_frame_error" in window:
            return {"ok": True, "intent": intent, **window}
    frame_applied = window is not None
    start_ns = int(window["start_ns"]) if frame_applied else None
    end_ns = int(window["end_ns"]) if frame_applied else None
    # A gid only narrows results when COMPOSITE_EVENTS actually has globalTid;
    # otherwise the filter is dropped and symbols still mix across threads.
    gid_applied = gid is not None and "globalTid" in cc_columns
    hotspots = _leaf_symbol_rows(
        con,
        tables,
        cpu_cycles=1 if has_cpu_cycles else None,
        gid=gid,
        start_ns=start_ns,
        end_ns=end_ns,
        max_rows=max_rows,
    )
    if hotspots is None:
        return _no_samples_note(intent)
    blocked = (
        _leaf_symbol_rows(
            con,
            tables,
            cpu_cycles=0,
            gid=gid,
            start_ns=start_ns,
            end_ns=end_ns,
            max_rows=max_rows,
        )
        if has_cpu_cycles
        else None
    )
    if gid is not None and not gid_applied:
        target = f"all_threads (requested thread:{gid}, but COMPOSITE_EVENTS has no globalTid column)"
    elif gid is not None:
        target = f"thread:{gid}"
    else:
        target = "all_threads"
    if frame_applied:
        target = f"{target} in frame {frame}"
    elif frame is not None:
        target = (
            f"{target} session-wide (requested frame {frame}, but failed to set time window)"
        )
    scope_note = (
        f" Samples are restricted to frame {frame}'s [start_ns, end_ns) window using "
        f"COMPOSITE_EVENTS.start."
        if frame_applied
        else (
            f" Frame {frame} was requested, but failed to set time window;"
            "results remain session-wide."
            if frame is not None
            else ""
        )
    )
    payload: dict[str, Any] = {
        "ok": True,
        "intent": intent,
        "target": target,
        "scope": "frame" if frame_applied else "session",
        "thread_name": _thread_names(con, tables).get(gid) if gid_applied else None,
        "cpu_cycles_split": has_cpu_cycles,
        "hotspots": _key_rows(
            [{"symbol": row["symbol"], "samples": int(row["n"])} for row in hotspots],
            "callstack-hotspot",
            "symbol",
        ),
        "note": (
            "hotspots are leaf symbols of periodic CPU samples (cpuCycles=1) ranked by sample "
            "count -- time/where-it-runs attribution. blocked_stacks are leaf symbols of scheduling "
            "event callstacks (cpuCycles=0) -- why a thread came off CPU (e.g. a fence/wait call). "
            "Pass --metric <globalTid> (from thread_scheduling) to target one thread; without it "
            f"symbols mix across threads. Counts are evidence, not a verdict.{scope_note}"
        ),
    }
    if frame_applied:
        payload["window"] = window
    if blocked is not None:
        payload["blocked_stacks"] = _key_rows(
            [{"symbol": row["symbol"], "events": int(row["n"])} for row in blocked],
            "callstack-blocked",
            "symbol",
        )
    else:
        payload["blocked_stacks_note"] = (
            "COMPOSITE_EVENTS has no cpuCycles column; cannot separate periodic samples from "
            "scheduling event callstacks, so hotspots may mix both stack types."
        )
    return payload


#TODO: This is a temporary constraint - we should be able to run the analysis on multiple reports. See DTSP-22718.
def _single_report_note(intent: str) -> dict[str, Any]:
    return {
        "ok": True,
        "intent": intent,
        "target": "multi_report_unsupported",
        "note": "Callstack analysis applies to a single report; load one .nsys-rep, not a directory.",
    }


def _no_samples_note(intent: str) -> dict[str, Any]:
    return {
        "ok": True,
        "intent": intent,
        "target": "none",
        "note": (
            "No usable CPU sampling callstacks (need COMPOSITE_EVENTS + SAMPLING_CALLCHAINS + "
            "StringIds); recapture with CPU sampling enabled to attribute thread callstacks."
        ),
    }
