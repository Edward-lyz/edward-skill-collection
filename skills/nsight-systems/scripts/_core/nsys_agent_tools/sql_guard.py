"""SQL safety checks shared by report-query adapters."""

from __future__ import annotations

import re

READ_ONLY_RE = re.compile(r"^\s*(select|with)\b", re.IGNORECASE | re.DOTALL)
BLOCKED_SQL_KEYWORDS = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "attach",
    "detach",
    "copy",
    "pragma",
    "vacuum",
    "replace",
)
BLOCKED_RE = re.compile(r"\b(" + "|".join(BLOCKED_SQL_KEYWORDS) + r")\b", re.IGNORECASE)
EVENT_TABLE_RE = re.compile(r'\b"?(CUPTI_ACTIVITY_KIND_|CUDA_|NVTX_|OSRT_|MPI_|NCCL_)[A-Za-z0-9_]*"?\b', re.IGNORECASE)
AGGREGATE_RE = re.compile(r"\b(count|sum|avg|min|max)\s*\(|\bgroup\s+by\b", re.IGNORECASE)
GROUP_BY_RE = re.compile(r"\bgroup\s+by\b", re.IGNORECASE)
REPORT_LABEL_RE = re.compile(r"\b(__report_label|__report_index|__source_dir__|source_dir|report_source)\b", re.IGNORECASE)
DUCKDB_EXTERNAL_FUNCTIONS = (
    "read_csv",
    "read_csv_auto",
    "read_parquet",
    "read_json",
    "read_json_auto",
    "read_text",
    "read_blob",
    "parquet_scan",
    "csv_scan",
    "json_scan",
    "glob",
    "query_table",
    "query",
    "sqlite_scan",
    "postgres_scan",
)
DUCKDB_EXTERNAL_FILE_FUNCTIONS = tuple(
    term for term in DUCKDB_EXTERNAL_FUNCTIONS if term not in {"query", "query_table"}
)
EXTERNAL_FILE_SQL_BOUNDARY_TERMS = (*DUCKDB_EXTERNAL_FILE_FUNCTIONS, "attach")
# Supported report queries use exported report tables, not DuckDB reader
# functions. Block read_* so new file readers are rejected by default.
_DUCKDB_EXTERNAL_RE_TERMS = (
    r"read_\w+",
    *(re.escape(term) for term in DUCKDB_EXTERNAL_FUNCTIONS if not term.startswith("read_")),
)
DUCKDB_EXTERNAL_RE = re.compile(r"\b(" + "|".join(_DUCKDB_EXTERNAL_RE_TERMS) + r")\s*\(", re.IGNORECASE)


def clean_sql(sql: str) -> str:
    text = sql.strip()
    masked, _comments, _error = _mask_literals_and_comments(text)
    if masked.rstrip().endswith(";") and masked.count(";") == 1:
        text = text[:-1].strip()
    return text


def validate_sql(sql: str) -> str | None:
    """Return an error message when SQL is outside the supported read-only subset."""

    if not sql:
        return "SQL is empty"
    masked, has_comments, mask_error = _mask_literals_and_comments(sql)
    if mask_error is not None:
        return mask_error
    if has_comments:
        return "SQL comments are not supported in report queries"
    if ";" in masked:
        return "Only one SQL statement is allowed"
    if not READ_ONLY_RE.match(masked):
        return "Only SELECT or WITH queries are allowed"
    if BLOCKED_RE.search(masked):
        return "SQL contains a blocked statement or pragma"
    if DUCKDB_EXTERNAL_RE.search(masked):
        return "SQL contains an external file or table function that is not allowed"
    if EVENT_TABLE_RE.search(masked) and not re.search(r"\blimit\b", masked, re.IGNORECASE) and not AGGREGATE_RE.search(masked):
        return "Large event/activity table queries must include LIMIT or an aggregate"
    return None


def _mask_literals_and_comments(sql: str) -> tuple[str, bool, str | None]:
    """Mask quoted strings so safety checks inspect SQL structure only.

    This is intentionally a small scanner rather than a full SQL parser: the
    runtime supports a conservative SELECT/WITH subset, rejects comments, and
    delegates real execution to bounded read-only SQLite/DuckDB connections.
    """

    chars = list(sql)
    has_comments = False
    state = "normal"
    i = 0
    while i < len(chars):
        char = chars[i]
        nxt = chars[i + 1] if i + 1 < len(chars) else ""
        if state == "normal":
            if char == "'":
                chars[i] = " "
                state = "single"
            elif char == '"':
                chars[i] = " "
                state = "double_identifier"
            elif char == "`":
                return "".join(chars), has_comments, "Backtick-quoted identifiers are not supported"
            elif char == "-" and nxt == "-":
                has_comments = True
                chars[i] = chars[i + 1] = " "
                state = "line_comment"
                i += 1
            elif char == "/" and nxt == "*":
                has_comments = True
                chars[i] = chars[i + 1] = " "
                state = "block_comment"
                i += 1
        elif state == "single":
            chars[i] = " "
            if char == "'" and nxt == "'":
                chars[i + 1] = " "
                i += 1
            elif char == "'":
                state = "normal"
        elif state == "double_identifier":
            if char == '"' and nxt == '"':
                chars[i] = chars[i + 1] = " "
                i += 1
            elif char == '"':
                chars[i] = " "
                state = "normal"
        elif state == "line_comment":
            chars[i] = " "
            if char == "\n":
                state = "normal"
        elif state == "block_comment":
            chars[i] = " "
            if char == "*" and nxt == "/":
                chars[i + 1] = " "
                state = "normal"
                i += 1
        i += 1
    if state in {"single", "double_identifier"}:
        return "".join(chars), has_comments, "SQL string literal is not closed"
    if state == "block_comment":
        return "".join(chars), has_comments, "SQL block comment is not closed"
    return "".join(chars), has_comments, None


def multi_report_scope_warning(sql: str) -> str | None:
    """Return a warning for aggregate SQL that may hide per-report skew.

    A directory of ``.nsys-rep`` files is represented as union tables with
    ``__report_label`` and ``__report_index`` columns. Global aggregates are
    still valid for questions asking for a global total, but many multi-rank
    questions require per-report grouping. This helper adds evidence metadata;
    it does not reject the query because global totals are sometimes intended.
    """

    if not AGGREGATE_RE.search(sql):
        return None
    if GROUP_BY_RE.search(sql) and REPORT_LABEL_RE.search(sql):
        return None
    return (
        "This query aggregates across multiple loaded reports without grouping by "
        "__report_label. Use GROUP BY __report_label for per-rank/per-report conclusions, "
        "or state that the result is a global aggregate across all loaded reports."
    )
