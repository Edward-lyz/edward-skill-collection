"""Small SQL helpers for report-owned identifiers and bounded reads."""

from __future__ import annotations

import functools
import re
import time
from typing import Any

from .schema import SYNTHETIC_REPORT_INDEX, SYNTHETIC_REPORT_LABEL
from .serialization import _jsonable_row
from .types import ReportError


def _quote_identifier(value: str) -> str:
    if "\x00" in value:
        raise ReportError("SQL identifier contains a NUL byte")
    return '"' + value.replace('"', '""') + '"'


def _execute_identifier_sql(connection: Any, sql: str) -> Any:
    # Identifiers are loaded from report schema or sanitized filenames and are
    # quoted before this point.
    return connection.execute(sql)


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _sql_list(values: list[str]) -> str:
    return "[" + ", ".join(_sql_string(value) for value in values) + "]"


def _existing_columns(con: Any, table: str) -> set[str]:
    try:
        rows = _execute_identifier_sql(con, "PRAGMA table_info(" + _quote_identifier(table) + ")").fetchall()
    except Exception:
        return set()
    names: set[str] = set()
    for row in rows:
        # SQLite: (cid, name, type, ...). DuckDB table_info is compatible for
        # the first two positions in current releases.
        if len(row) > 1:
            names.add(str(row[1]))
    return names


def _query_dicts(
    con: Any,
    sql: str,
    *,
    max_rows: int,
    params: tuple[Any, ...] = (),
    suppress_errors: bool = True,
) -> list[dict[str, Any]]:
    try:
        cur = con.execute(sql, params)
        columns = [d[0] for d in cur.description or []]
        rows = cur.fetchmany(max_rows)
    except Exception:
        if not suppress_errors:
            raise
        return []
    return [dict(zip(columns, _jsonable_row(row), strict=False)) for row in rows]


def _scalar(con: Any, sql: str) -> Any:
    try:
        row = con.execute(sql).fetchone()
    except Exception:
        return None
    return row[0] if row else None


def _install_query_timeout(con: Any, timeout_s: float) -> None:
    if not timeout_s or timeout_s <= 0:
        return
    if hasattr(con, "set_progress_handler"):
        deadline = time.monotonic() + timeout_s

        def stop_when_expired() -> int:
            return 1 if time.monotonic() > deadline else 0

        con.set_progress_handler(stop_when_expired, 10_000)


def _multi_report_table_sql(table: str, files: list[tuple[Any, str, int]]) -> str:
    paths = [str(path) for path, _, _ in files]
    source_column = "__nsys_source_file"
    label_case = "CASE " + _quote_identifier(source_column) + " " + " ".join(
        f"WHEN {_sql_string(str(path))} THEN {_sql_string(label)}" for path, label, _ in files
    ) + " ELSE '<unknown>' END"
    index_case = "CASE " + _quote_identifier(source_column) + " " + " ".join(
        f"WHEN {_sql_string(str(path))} THEN {index}" for path, _, index in files
    ) + " ELSE NULL END"
    return (
        "CREATE OR REPLACE TABLE "
        + _quote_identifier(table)
        + " AS SELECT * EXCLUDE("
        + _quote_identifier(source_column)
        + "), "
        + label_case
        + f" AS {SYNTHETIC_REPORT_LABEL}, "
        + index_case
        + f" AS {SYNTHETIC_REPORT_INDEX} FROM read_parquet("
        + _sql_list(paths)
        + ", union_by_name=true, filename="
        + _sql_string(source_column)
        + ")"
    )


# --- DuckDB reserved-identifier repair for report SQL --------------------------
# The report query engine is DuckDB, where keywords such as ``end`` are reserved
# and must be double-quoted when used as column identifiers. nsys event tables
# pervasively expose ``start``/``end`` columns, so agents that write SQL in
# SQLite terms hit a parse error. The helpers below quote a bare reserved
# identifier the parser flags and re-run the query; ``duckdb_reserved_words``
# gates the repair so only genuine reserved words are quoted, leaving a
# non-reserved token in a real syntax error untouched (its original error surfaces).
# ``RESERVED_WORD_GUIDANCE`` is attached to a repaired query's payload so the agent
# learns to quote reserved words on subsequent queries.

RESERVED_WORD_GUIDANCE = (
    'Report SQL runs on DuckDB. Quote reserved-word column names with double '
    'quotes, e.g. "end" (durations are "end" - start). A bare reserved word is '
    "a syntax error."
)

_AT_OR_NEAR_RE = re.compile(r'at or near "([^"]+)"')
_LINE_PREFIX_RE = re.compile(r"(LINE (\d+):\s+)")
_SIMPLE_IDENT_RE = re.compile(r"[A-Za-z_]\w*\Z")


@functools.lru_cache(maxsize=1)
def duckdb_reserved_words() -> frozenset[str]:
    """Return DuckDB's reserved keywords, lowercased. Empty if DuckDB is absent."""

    try:
        from .duckdb_backend import _import_duckdb

        duckdb = _import_duckdb()
        con = duckdb.connect()
        try:
            rows = con.execute(
                "SELECT keyword_name FROM duckdb_keywords() "
                "WHERE keyword_category = 'reserved'"
            ).fetchall()
        finally:
            con.close()
    except Exception:  # noqa: BLE001 - annotation is best-effort
        return frozenset()
    return frozenset(str(row[0]).lower() for row in rows)


def locate_reserved_token(sql: str, error_text: str) -> tuple[int, str] | None:
    """Return (offset, token) of the bare identifier DuckDB flagged, or None.

    Uses DuckDB's ``at or near "<tok>"`` plus the caret line. Maps the caret to
    an absolute offset in ``sql`` and verifies the token is actually there; if
    the mapping is uncertain (truncated/multi-line display), returns None so the
    caller falls back to the plain error rather than quoting the wrong token.
    """

    match = _AT_OR_NEAR_RE.search(error_text)
    if not match:
        return None
    token = match.group(1)
    # Only quote genuine DuckDB reserved words. A non-reserved token flagged by a
    # real syntax error (e.g. a typo) must be left alone so its error is surfaced.
    if not _SIMPLE_IDENT_RE.match(token) or token.lower() not in duckdb_reserved_words():
        return None
    lines = error_text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 or not stripped or set(stripped) != {"^"}:
            continue
        prefix = _LINE_PREFIX_RE.match(lines[i - 1])
        if not prefix:
            return None
        content = lines[i - 1][len(prefix.group(1)):]
        caret_col = line.index("^") - len(prefix.group(1))
        line_no = int(prefix.group(2))
        sql_lines = sql.split("\n")
        if caret_col < 0 or caret_col > len(content) or not (1 <= line_no <= len(sql_lines)):
            return None
        target = sql_lines[line_no - 1]
        # DuckDB windows long error lines with a leading/trailing "..." ellipsis,
        # so the displayed content need not begin at column 0 of the SQL line.
        # Locate the token by matching the displayed text *before* the caret as a
        # substring of the SQL line rather than trusting the caret column, which
        # otherwise mislocates any token that is not near the start of a long query.
        before = content[:caret_col].lstrip()
        if before.startswith("..."):
            before = before[3:]
        before = before.strip()
        if before:
            idx = target.find(before)
            if idx == -1:
                return None
            pos_in_line = idx + len(before)
        else:
            pos_in_line = 0
        while pos_in_line < len(target) and target[pos_in_line].isspace():
            pos_in_line += 1
        base = sum(len(part) + 1 for part in sql_lines[: line_no - 1])
        pos = base + pos_in_line
        if sql[pos : pos + len(token)].lower() != token.lower():
            return None
        return pos, token
    return None


def _quote_at(sql: str, pos: int, token: str) -> str:
    return sql[:pos] + '"' + sql[pos : pos + len(token)] + '"' + sql[pos + len(token) :]


def repair_reserved_identifiers(run_once, sql: str, *, max_iters: int = 20):
    """Execute ``sql`` via ``run_once``; quote bare reserved identifiers on a
    locatable parse error and retry (bounded). Returns (columns, rows,
    normalized_tokens). Re-raises when the error is not a locatable reserved-word
    parse error or cannot be repaired."""

    normalized: list[str] = []
    current = sql
    last_exc: Exception | None = None
    for _ in range(max_iters + 1):
        try:
            columns, rows = run_once(current)
            return columns, rows, normalized
        except Exception as exc:  # noqa: BLE001 - inspected as text, fails safe
            last_exc = exc
            located = locate_reserved_token(current, str(exc))
            if located is None:
                raise
            pos, token = located
            current = _quote_at(current, pos, token)
            normalized.append(token)
    assert last_exc is not None
    raise last_exc
