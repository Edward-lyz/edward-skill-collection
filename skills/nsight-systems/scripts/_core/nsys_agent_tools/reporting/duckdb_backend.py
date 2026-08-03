"""DuckDB import, hardening, and killable worker execution."""

from __future__ import annotations

import multiprocessing as mp
import os
from contextlib import suppress
from pathlib import Path
from typing import Any

from .dependencies import report_dependency_install_hint
from .serialization import _jsonable_rows
from .types import ReportError

_DUCKDB_SETTING_QUERIES = {
    "enable_external_access": "SELECT current_setting('enable_external_access')",
    "allow_unsigned_extensions": "SELECT current_setting('allow_unsigned_extensions')",
    "allow_community_extensions": "SELECT current_setting('allow_community_extensions')",
    "lock_configuration": "SELECT current_setting('lock_configuration')",
}


def _import_duckdb():
    try:
        import duckdb  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ReportError(_missing_duckdb_message()) from exc
    return duckdb


def _missing_duckdb_message() -> str:
    return "DuckDB is required for report analysis. " + report_dependency_install_hint()


def _connect_hardened_duckdb(db_path: str | Path):
    """Open a read-only DuckDB connection and refuse it unless hardening holds."""

    duckdb = _import_duckdb()
    try:
        con = duckdb.connect(
            str(db_path),
            read_only=True,
            config={"enable_external_access": "false"},
        )
    except TypeError:
        con = duckdb.connect(str(db_path), read_only=True)
    try:
        _harden_duckdb_connection(con)
    except Exception:
        with suppress(Exception):
            con.close()
        raise
    return con


def _harden_duckdb_connection(con: Any) -> None:
    """Disable external access/resource surprises for model-provided SQL."""

    for statement in (
        "SET enable_external_access = false",
        "SET allow_unsigned_extensions = false",
        "SET allow_community_extensions = false",
        "SET lock_configuration = true",
    ):
        try:
            con.execute(statement)
        except Exception as exc:  # noqa: BLE001 - fail closed for older or changed DuckDB.
            if _duckdb_settings_are_hardened(con):
                return
            raise ReportError("DuckDB safety setup failed") from exc
    if not _duckdb_settings_are_hardened(con):
        raise ReportError("DuckDB safety setup failed")


def _duckdb_settings_are_hardened(con: Any) -> bool:
    """Return True only when all four safety settings read back as expected."""

    return all(
        _duckdb_setting_matches(con, name, expected=expected)
        for name, expected in (
            ("enable_external_access", False),
            ("allow_unsigned_extensions", False),
            ("allow_community_extensions", False),
            ("lock_configuration", True),
        )
    )


def _duckdb_setting_matches(con: Any, name: str, *, expected: bool) -> bool:
    """Query one setting and report whether it currently equals ``expected``."""

    try:
        row = con.execute(_DUCKDB_SETTING_QUERIES[name]).fetchone()
    except Exception:  # noqa: BLE001 - fail closed if the setting cannot be checked.
        return False
    actual = row[0] if row else None
    return _duckdb_bool_setting(actual) is expected


def _duckdb_bool_setting(value: object) -> bool | None:
    """Normalize a DuckDB setting value to a bool, or None if it is not boolean."""

    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "on"}:
            return True
        if normalized in {"false", "0", "off"}:
            return False
    return None


def _query_duckdb_subprocess(db_path: Path, sql: str, max_rows: int, timeout_s: float) -> tuple[list[str], list[tuple[Any, ...]]]:
    """Run DuckDB SQL in a killable worker process."""

    ctx = _worker_context()
    parent_conn, child_conn = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=_duckdb_query_worker, args=(str(db_path), sql, max_rows, child_conn))
    proc.start()
    child_conn.close()
    try:
        if not parent_conn.poll(timeout_s):
            proc.terminate()
            proc.join(2)
            if proc.is_alive():
                proc.kill()
                proc.join(2)
            raise TimeoutError(f"query exceeded {timeout_s:.1f}s timeout")
        payload = parent_conn.recv()
        proc.join(2)
        if proc.is_alive():
            proc.terminate()
            proc.join(2)
            if proc.is_alive():
                proc.kill()
                proc.join(2)
        if not isinstance(payload, dict):
            raise ReportError("DuckDB worker exited without a result")
        if not payload.get("ok"):
            raise ReportError(str(payload.get("error", "DuckDB query failed")))
        return list(payload.get("columns", [])), [tuple(row) for row in payload.get("rows", [])]
    except EOFError as exc:
        raise ReportError("DuckDB worker exited without a result") from exc
    finally:
        parent_conn.close()
        with suppress(Exception):
            proc.close()


def _duckdb_query_worker(db_path: str, sql: str, max_rows: int, connection: Any) -> None:
    try:
        con = _connect_hardened_duckdb(db_path)
        with con:
            cur = con.execute(sql)
            columns = [d[0] for d in cur.description or []]
            rows = cur.fetchmany(max_rows)
        connection.send({"ok": True, "columns": columns, "rows": _jsonable_rows(rows)})
    except Exception as exc:  # noqa: BLE001 - serialized back to parent
        connection.send({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
    finally:
        connection.close()


def _worker_context() -> mp.context.BaseContext:
    """Return the DuckDB worker start method.

    Prefer ``spawn``: report queries may run inside long-lived agent processes
    that also have model/client threads, and forking such processes is fragile.
    A developer can opt into fork for stdin-based smoke experiments with
    ``NSYS_AGENT_ALLOW_FORK_DUCKDB_WORKER=1``.
    """

    if (
        os.environ.get("NSYS_AGENT_ALLOW_FORK_DUCKDB_WORKER") == "1"
        and "fork" in mp.get_all_start_methods()
    ):
        return mp.get_context("fork")
    return mp.get_context("spawn")
