"""Deterministic per-API graphics-call facts for the report-fact tool.

Auto-detects the present graphics API table (DX12 / DXGI / Vulkan / OpenGL, by
detection priority) and pairs it with its GPU-side workload table, then serves
three intents over those calls so the model never hand-writes graphics SQL:

- ``graphics_api_summary``: per-API call mix (count, total/avg/max ms) over the
  whole session or a single frame window, plus a GPU workload block.
- ``graphics_api_distribution``: session-wide per-API duration percentiles,
  optionally narrowed to one API via ``--metric``.
- ``graphics_api_timeline``: back-to-back / serialization timeline for one API's
  calls -- the in-order command queue pattern behind tiled-resource stutter.
"""

from __future__ import annotations

from typing import Any

from .facts_cuda_common import _key_rows, _string_expr
from .facts_graphics_frame import _frame_starts, _percentile
from .schema import GRAPHICS_API_WORKLOAD_PAIRS
from .sql_utils import _existing_columns, _query_dicts, _sql_string

# A gap at or below this (ns) counts two calls as back to back; the in-order command
# queue serializes such runs, the pattern behind tiled-resource stutter.
_BACK_TO_BACK_THRESHOLD_NS = 1000
_REQUIRED_COLUMNS = {"start", "end", "nameId"}
_MAX_CALLS = 200_000


def _detect_api_table(tables: set[str]) -> tuple[str | None, str | None]:
    """Return the first present (api_table, workload_table) by detection priority."""

    for api_table, workload_table in GRAPHICS_API_WORKLOAD_PAIRS:
        if api_table in tables:
            return api_table, (workload_table if workload_table in tables else None)
    return None, None


def _aggregate_calls(
    con: Any,
    table: str,
    tables: set[str],
    *,
    start_ns: int | None,
    end_ns: int | None,
    name_filter: str | None,
    max_rows: int,
) -> list[dict[str, Any]] | None:
    """Per-name count and total/avg/max ms over an optional window; None if shape wrong."""

    if not _REQUIRED_COLUMNS.issubset(_existing_columns(con, table)):
        return None
    name_expr, join = _string_expr(con, table, "d", "nameId", tables)
    where = _where_clause(name_expr, start_ns, end_ns, name_filter)
    rows = _query_dicts(
        con,
        f"SELECT {name_expr} AS api_name, COUNT(*) AS cnt, "
        f'SUM(d."end" - d.start) AS total_ns, AVG(d."end" - d.start) AS avg_ns, '
        f'MAX(d."end" - d.start) AS max_ns '
        f'FROM "{table}" d{join}{where} '
        f"GROUP BY api_name ORDER BY total_ns DESC",
        max_rows=max(1, max_rows),
    )
    return [
        {
            "api_name": row["api_name"],
            "count": int(row["cnt"]),
            "total_ms": round(int(row["total_ns"]) / 1e6, 3),
            "avg_ms": round(float(row["avg_ns"]) / 1e6, 3),
            "max_ms": round(int(row["max_ns"]) / 1e6, 3),
        }
        for row in rows
        if row.get("total_ns") is not None
    ]


def _distribution_rows(
    con: Any, table: str, tables: set[str], name_filter: str | None, max_rows: int
) -> list[dict[str, Any]] | None:
    """Per-name session-wide duration percentiles; None if table shape is wrong.

    Percentiles are computed in Python from the pulled durations (as in
    facts_graphics_frame) so this runs on the raw-sqlite backend, which has no
    percentile aggregate.
    """

    if not _REQUIRED_COLUMNS.issubset(_existing_columns(con, table)):
        return None
    name_expr, join = _string_expr(con, table, "d", "nameId", tables)
    where = _where_clause(name_expr, None, None, name_filter)
    rows = _query_dicts(
        con,
        f'SELECT {name_expr} AS api_name, d."end" - d.start AS dur '
        f'FROM "{table}" d{join}{where}',
        max_rows=_MAX_CALLS,
    )
    buckets: dict[str, list[float]] = {}
    for row in rows:
        if row.get("dur") is not None and row.get("api_name") is not None:
            buckets.setdefault(str(row["api_name"]), []).append(float(row["dur"]))
    ranked = sorted(buckets.items(), key=lambda item: sum(item[1]), reverse=True)[: max(1, max_rows)]
    out: list[dict[str, Any]] = []
    for api_name, raw in ranked:
        values = sorted(raw)
        out.append(
            {
                "api_name": api_name,
                "count": len(values),
                "min_ms": round(values[0] / 1e6, 3),
                "median_ms": round(_percentile(values, 0.5) / 1e6, 3),
                "p95_ms": round(_percentile(values, 0.95) / 1e6, 3),
                "p99_ms": round(_percentile(values, 0.99) / 1e6, 3),
                "max_ms": round(values[-1] / 1e6, 3),
            }
        )
    return out


def _where_clause(
    name_expr: str, start_ns: int | None, end_ns: int | None, name_filter: str | None
) -> str:
    terms: list[str] = []
    if start_ns is not None and end_ns is not None:
        terms.append(f"d.start >= {int(start_ns)} AND d.start < {int(end_ns)}")
    if name_filter:
        terms.append(f"LOWER({name_expr}) = {_sql_string(name_filter.lower())}")
    return (" WHERE " + " AND ".join(terms)) if terms else ""


def _workload_block(
    con: Any,
    workload_table: str | None,
    tables: set[str],
    *,
    start_ns: int | None,
    end_ns: int | None,
    name_filter: str | None,
    max_rows: int,
    distribution: bool,
) -> dict[str, Any]:
    """GPU-side aggregate paired with the API table, or a skip note when unavailable."""

    if workload_table is None:
        return {"source": "skipped", "note": "No paired GPU workload table in this report."}
    if distribution:
        rows = _distribution_rows(con, workload_table, tables, name_filter, max_rows)
    else:
        rows = _aggregate_calls(
            con, workload_table, tables, start_ns=start_ns, end_ns=end_ns, name_filter=name_filter, max_rows=max_rows
        )
    if rows is None:
        return {"source": "skipped", "note": f"{workload_table} lacks start/end/nameId columns."}
    return {"source": workload_table, "rows": _key_rows(rows, "graphics-workload", "api_name")}


def _resolve_frame_window(con: Any, tables: set[str], frame: int) -> dict[str, Any]:
    """Frame N window [start_ns, end_ns) from the present source, or an error dict."""

    _, _, starts = _frame_starts(con, tables)
    if not starts:
        return {"requested_frame_error": "No graphics present calls found to derive a frame window."}
    if not 1 <= frame < len(starts):
        return {"requested_frame_error": f"frame {frame} is out of range (1..{len(starts) - 1})."}
    start_ns, end_ns = starts[frame - 1], starts[frame]
    return {
        "frame_num": frame,
        "start_ns": start_ns,
        "end_ns": end_ns,
        "frame_ms": round((end_ns - start_ns) / 1e6, 3),
    }


def _graphics_api_summary(
    con: Any,
    tables: set[str],
    *,
    multi_report: bool,
    frame: int | None,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    """Per-API call mix over the session or a frame window, with a GPU workload block."""

    if multi_report:
        return _single_report_note(intent)
    api_table, workload_table = _detect_api_table(tables)
    if api_table is None:
        return _no_api_note(intent)
    window: dict[str, Any] | None = None
    if frame is not None:
        window = _resolve_frame_window(con, tables, frame)
        if "requested_frame_error" in window:
            return {"ok": True, "intent": intent, "api_source": api_table, **window}
    start_ns = window["start_ns"] if window else None
    end_ns = window["end_ns"] if window else None
    api_rows = (
        _aggregate_calls(con, api_table, tables, start_ns=start_ns, end_ns=end_ns, name_filter=None, max_rows=max_rows)
        or []
    )
    frame_ms = window["frame_ms"] if window else None
    if frame_ms:
        for row in api_rows:
            row["pct_of_frame"] = round(row["total_ms"] / frame_ms * 100, 3)
    payload: dict[str, Any] = {
        "ok": True,
        "intent": intent,
        "api_source": api_table,
        "api": _key_rows(api_rows, "graphics-api", "api_name"),
        "workload": _workload_block(
            con, workload_table, tables, start_ns=start_ns, end_ns=end_ns, name_filter=None, max_rows=max_rows, distribution=False
        ),
        "note": (
            "Per-API CPU-call timing (ms), ranked by total_ms; duration is end - start. "
            "Pass --frame <N> to scope to a frame window (adds pct_of_frame) without pasting "
            "nanoseconds; workload is the paired GPU-side table. Confirm serialization with "
            "graphics_api_timeline --metric <api_name>."
        ),
    }
    if window:
        payload["window"] = window
    return payload


def _graphics_api_distribution(
    con: Any,
    tables: set[str],
    *,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    """Session-wide per-API duration percentiles; --metric narrows to one API."""

    if multi_report:
        return _single_report_note(intent)
    api_table, workload_table = _detect_api_table(tables)
    if api_table is None:
        return _no_api_note(intent)
    name_filter = metric or None
    api_rows = _distribution_rows(con, api_table, tables, name_filter, max_rows) or []
    return {
        "ok": True,
        "intent": intent,
        "api_source": api_table,
        "api": _key_rows(api_rows, "graphics-api-distribution", "api_name"),
        "workload": _workload_block(
            con, workload_table, tables, start_ns=None, end_ns=None, name_filter=name_filter, max_rows=max_rows, distribution=True
        ),
        "note": (
            "Per-API call-duration distribution (ms) across the whole session: min/median/"
            "p95/p99/max separate steady-state cost from the tail. Pass --metric <api_name> "
            "to narrow to one API."
        ),
    }


def _graphics_api_timeline(
    con: Any,
    tables: set[str],
    *,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    """Back-to-back / serialization timeline for one API's calls across the session."""

    del max_rows
    if multi_report:
        return _single_report_note(intent)
    api_table, _ = _detect_api_table(tables)
    if api_table is None:
        return _no_api_note(intent)
    name = (metric or "").strip()
    if not name:
        return {
            "ok": True,
            "intent": intent,
            "api_source": api_table,
            "note": "Pass --metric <api_name> (a name from graphics_api_summary) to inspect its call timeline.",
        }
    if not _REQUIRED_COLUMNS.issubset(_existing_columns(con, api_table)):
        return _no_api_note(intent)
    name_expr, join = _string_expr(con, api_table, "d", "nameId", tables)
    # Resolve the metric as a case-insensitive substring so a short name (UpdateTileMappings)
    # finds the fully-qualified API; disambiguate when it matches more than one.
    matched = _query_dicts(
        con,
        f'SELECT {name_expr} AS api_name, COUNT(*) AS cnt FROM "{api_table}" d{join} '
        f"WHERE LOWER({name_expr}) LIKE {_sql_string('%' + name.lower() + '%')} "
        f"GROUP BY api_name ORDER BY cnt DESC",
        max_rows=25,
    )
    candidates = [str(row["api_name"]) for row in matched if row.get("api_name") is not None]
    if not candidates:
        return {
            "ok": True,
            "intent": intent,
            "api_source": api_table,
            "api_name": name,
            "call_count": 0,
            "note": f"No {api_table} call name matches '{name}'.",
        }
    if len(candidates) > 1:
        return {
            "ok": True,
            "intent": intent,
            "api_source": api_table,
            "candidates": candidates[:10],
            "note": (
                f"'{name}' matches {len(candidates)} API names; re-run graphics_api_timeline "
                "--metric with one exact name from candidates."
            ),
        }
    resolved = candidates[0]
    calls = _query_dicts(
        con,
        f'SELECT d.start AS start_ns, d."end" AS end_ns FROM "{api_table}" d{join} '
        f"WHERE LOWER({name_expr}) = {_sql_string(resolved.lower())} ORDER BY d.start",
        max_rows=_MAX_CALLS,
    )
    return {
        "ok": True,
        "intent": intent,
        "api_source": api_table,
        "api_name": resolved,
        "back_to_back_threshold_ns": _BACK_TO_BACK_THRESHOLD_NS,
        **_timeline_metrics(calls),
        "note": (
            "back_to_back_count and longest_run measure serialized chaining (gap at or below "
            "back_to_back_threshold_ns) on the in-order command queue; occupancy_pct is summed "
            "call time over the covered span. Counts are evidence, not a verdict."
        ),
    }


def _timeline_metrics(calls: list[dict[str, Any]]) -> dict[str, Any]:
    starts = [int(row["start_ns"]) for row in calls if row.get("start_ns") is not None]
    ends = [int(row["end_ns"]) for row in calls if row.get("end_ns") is not None]
    count = min(len(starts), len(ends))
    if count == 0:
        return {"call_count": 0}
    starts, ends = starts[:count], ends[:count]
    gaps = [starts[i] - ends[i - 1] for i in range(1, count)]
    durations = [ends[i] - starts[i] for i in range(count)]
    longest_run = current = 1
    for gap in gaps:
        current = current + 1 if gap <= _BACK_TO_BACK_THRESHOLD_NS else 1
        longest_run = max(longest_run, current)
    span = ends[-1] - starts[0]
    return {
        "call_count": count,
        "min_gap_ns": int(min(gaps)) if gaps else None,
        "median_gap_ns": _percentile(sorted(float(gap) for gap in gaps), 0.5) if gaps else None,
        "back_to_back_count": sum(1 for gap in gaps if gap <= _BACK_TO_BACK_THRESHOLD_NS),
        "longest_run": longest_run,
        "occupancy_pct": round(sum(durations) / span * 100, 3) if span > 0 else None,
    }

#TODO: This is a temporary constraint - we should be able to run the callstack analysis on multiple reports. See DTSP-22718.
def _single_report_note(intent: str) -> dict[str, Any]:
    return {
        "ok": True,
        "intent": intent,
        "api_source": "multi_report_unsupported",
        "note": "Graphics-API analysis applies to a single report; load one .nsys-rep, not a directory.",
    }


def _no_api_note(intent: str) -> dict[str, Any]:
    return {
        "ok": True,
        "intent": intent,
        "api_source": "none",
        "note": (
            "No DX12_API/VULKAN_API/OPENGL_API call table found; recapture with a graphics API "
            "trace, or use frame_summary for present-based frame timing."
        ),
    }
