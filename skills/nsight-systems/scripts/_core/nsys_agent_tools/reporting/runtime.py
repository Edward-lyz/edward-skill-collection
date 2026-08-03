"""ReportRuntime facade for Nsight Systems report analysis.

The public runtime stays intentionally small: it owns configuration and exposes
stable methods.  Focused implementation modules handle loading/export, SQL
querying, deterministic facts, doctor checks, and multi-report cache building.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..defaults import DEFAULT_AGENT_CACHE_DIR
from .cache_status import report_cache_status as _report_cache_status
from .connection import connect_session as _connect_session_impl
from .doctor import DoctorThresholds, doctor_worst_status, run_doctor_checks
from .errors import _safe_error_text
from .evidence import report_evidence
from .facts_dispatch import available_fact_intents
from .facts_dispatch import fact as _fact
from .load import load_native_report_duckdb
from .load import load_report as _load_report
from .multi_report import multi_report_doctor as _multi_report_doctor_impl
from .query import context as _context
from .query import describe_tables as _describe_tables
from .query import query as _query
from .query import tables as _tables
from .sql_utils import _install_query_timeout
from .types import ReportSession


class ReportRuntime:
    """Load Nsight Systems reports and expose bounded analysis helpers.

    Prefer passing native ``.nsys-rep`` files. Exported SQLite/Parquet inputs
    are accepted as advanced/debug shortcuts; they are not the normal user
    contract.
    """

    def __init__(
        self,
        *,
        nsys_path: str = "nsys",
        cache_dir: str | Path = DEFAULT_AGENT_CACHE_DIR,
        max_reports: int = 256,
        export_timeout_s: float = 300.0,
        # Heartbeat cadence for the otherwise-silent cache export; keep it under
        # the agent's exec yield window. Non-positive disables it.
        export_progress_interval_s: float = 8.0,
        cache_lock_base_timeout_s: float = 30.0,
        # The per-report lock wait intentionally exceeds export_timeout_s so a
        # second process can wait behind a legitimate first process exporting a
        # large report instead of deleting/rebuilding the same cache.
        cache_lock_per_report_timeout_s: float = 320.0,
        doctor_thresholds: DoctorThresholds | None = None,
    ) -> None:
        self.nsys_path = nsys_path
        self.cache_dir = Path(cache_dir).expanduser().resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_reports = max(1, int(max_reports))
        self.export_timeout_s = max(1.0, float(export_timeout_s))
        self.export_progress_interval_s = float(export_progress_interval_s)
        self.cache_lock_base_timeout_s = max(1.0, float(cache_lock_base_timeout_s))
        self.cache_lock_per_report_timeout_s = max(1.0, float(cache_lock_per_report_timeout_s))
        self.doctor_thresholds = doctor_thresholds or DoctorThresholds()

    def cache_lock_timeout_s(self, report_count: int = 1) -> float:
        """Return the lock wait for a cache build covering ``report_count`` reports."""

        return self.cache_lock_base_timeout_s + self.cache_lock_per_report_timeout_s * max(
            1, int(report_count)
        )

    def load(self, report: str | Path) -> ReportSession:
        return _load_report(self, report)

    def cache_status(self, report: str | Path) -> dict[str, Any]:
        """Return native report cache readiness without exporting the report."""

        return _report_cache_status(self, report)

    def context(self, session: ReportSession) -> dict[str, Any]:
        payload = _context(self, session)
        table_names = {
            str(item.get("name"))
            for item in payload.get("tables", [])
            if isinstance(item, dict) and item.get("name")
        }
        payload["available_fact_intents"] = available_fact_intents(table_names)
        return payload

    def tables(
        self,
        session: ReportSession,
        *,
        table_patterns: tuple[str, ...] = (),
    ) -> list[str]:
        return _tables(self, session, table_patterns=table_patterns)

    def describe_tables(self, session: ReportSession, tables: list[str]) -> dict[str, Any]:
        return _describe_tables(self, session, tables)

    def query(
        self,
        session: ReportSession,
        sql: str,
        *,
        max_rows: int = 100,
        max_chars: int = 40000,
        timeout_s: float = 10.0,
        question: str = "",
    ) -> dict[str, Any]:
        return _query(
            self,
            session,
            sql,
            max_rows=max_rows,
            max_chars=max_chars,
            timeout_s=timeout_s,
            question=question,
        )

    def fact(
        self,
        session: ReportSession,
        *,
        intent: str,
        metric: str = "",
        max_rows: int = 10,
        frame: int | None = None,
    ) -> dict[str, Any]:
        """Return deterministic common report facts selected by intent."""

        if frame is None:
            return _fact(self, session, intent=intent, metric=metric, max_rows=max_rows)
        return _fact(self, session, intent=intent, metric=metric, max_rows=max_rows, frame=frame)

    def doctor(self, session: ReportSession) -> dict[str, Any]:
        """Run deterministic health checks on the loaded report."""

        if session.multi_reports:
            return _multi_report_doctor_impl(self, session)
        if session.source == "native_report":
            session = load_native_report_duckdb(self, session.input_path)
        try:
            with _connect_session_impl(session) as con:
                _install_query_timeout(con, 15.0)
                tables = set(self.tables(session))
                checks = run_doctor_checks(con, tables, self.doctor_thresholds)
        except Exception as exc:  # noqa: BLE001 - beta UX should return JSON failure
            return {"ok": False, "error": _safe_error_text(exc)}
        status = doctor_worst_status(checks)
        evidence = report_evidence(session, command="nsys_report_doctor")
        return {
            "ok": True,
            "report_label": session.display_label,
            "paths_hidden": True,
            "source": session.source,
            "evidence": evidence,
            "cache": evidence["cache"],
            "status": status,
            "checks": checks,
        }
