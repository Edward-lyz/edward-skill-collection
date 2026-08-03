"""Public report session types and report-runtime exceptions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReportSession:
    input_path: Path
    sqlite_path: Path | None
    source: str
    duckdb_path: Path | None = None
    parquet_root: Path | None = None
    multi_reports: tuple[Path, ...] = ()
    report_count: int = 0
    cache_events: tuple[dict[str, Any], ...] = ()

    @property
    def display_label(self) -> str:
        count = len(self.multi_reports) or self.report_count
        if count:
            return f"{self.input_path.name or 'report-directory'} ({count} reports)"
        return self.input_path.name or "loaded-report"


class ReportError(RuntimeError):
    """Raised when report loading or report analysis cannot proceed safely."""
