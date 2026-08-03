"""Backend connection helpers for prepared report sessions."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from urllib.parse import quote

from .duckdb_backend import _connect_hardened_duckdb
from .types import ReportError, ReportSession


def connect_session(session: ReportSession):
    """Open the read-only query backend for a prepared report session."""

    if session.sqlite_path:
        return _connect_sqlite(session.sqlite_path)
    if session.duckdb_path:
        return _connect_hardened_duckdb(session.duckdb_path)
    raise ReportError("Report session has no query backend")


def _connect_sqlite(path: Path) -> sqlite3.Connection:
    uri = f"file:{quote(path.as_posix(), safe='/')}?mode=ro"
    return sqlite3.connect(uri, uri=True)
