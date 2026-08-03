"""Report-session store: hides local report paths behind session IDs."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .report import ReportRuntime, ReportSession


@dataclass(frozen=True)
class ReportSessionRef:
    """Public reference for a loaded report session.

    The ref intentionally contains no absolute local path. Callers that need to
    operate on the report resolve the opaque ID through `ReportSessionStore`.
    """

    session_id: str
    display_label: str
    source: str
    report_count: int = 1
    report_labels: tuple[str, ...] = ()


class ReportSessionStore:
    """Small in-process report-session boundary.

    This is not a multi-user service framework. It is the one place where
    adapters convert user-supplied paths into opaque session IDs and where
    internal `ReportSession` objects remain hidden from model-visible output.
    """

    def __init__(self, runtime: ReportRuntime) -> None:
        self._runtime = runtime
        self._sessions: dict[str, ReportSession] = {}
        self._lock = threading.RLock()

    def load_path(self, report: str | Path, *, session_id: str | None = None) -> ReportSessionRef:
        session = self._runtime.load(report)
        with self._lock:
            key = session_id or uuid.uuid4().hex[:12]
            while key in self._sessions:
                if session_id:
                    raise ValueError(f"report session already exists: {key}")
                key = uuid.uuid4().hex[:12]
            self._sessions[key] = session
            return self._ref_from_session(key, session)

    def ref(self, session_id: str) -> ReportSessionRef:
        session = self.get(session_id)
        return self._ref_from_session(session_id, session)

    def _ref_from_session(self, session_id: str, session: ReportSession) -> ReportSessionRef:
        return ReportSessionRef(
            session_id=session_id,
            display_label=session.display_label,
            source=session.source,
            report_count=len(session.multi_reports) if session.multi_reports else 1,
            report_labels=tuple(path.name for path in session.multi_reports),
        )

    def get(self, session_id: str) -> ReportSession:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(
                "Unknown report session. Use a session_id returned by the report loader."
            )
        return session

    def resolve(self, session_id: str = "") -> tuple[str, ReportSession] | None:
        """Resolve explicit ID, or the only loaded session when unambiguous."""

        with self._lock:
            if session_id:
                session = self._sessions.get(session_id)
                return (session_id, session) if session is not None else None
            if len(self._sessions) == 1:
                key = next(iter(self._sessions))
                return key, self._sessions[key]
        return None

    def close(self, session_id: str = "") -> bool:
        with self._lock:
            resolved = self.resolve(session_id)
            if resolved is None:
                return False
            key, _session = resolved
            self._sessions.pop(key, None)
            return True

    def list_refs(self) -> list[ReportSessionRef]:
        """Return loaded report sessions without exposing local paths."""

        with self._lock:
            return [
                self._ref_from_session(key, session)
                for key, session in sorted(self._sessions.items())
            ]

    def first_session(self) -> ReportSession | None:
        resolved = self.resolve("")
        return resolved[1] if resolved else None

    def first_session_id(self) -> str | None:
        resolved = self.resolve("")
        return resolved[0] if resolved else None
