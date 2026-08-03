"""Public report-analysis API facade.

The implementation lives under :mod:`nsys_agent_tools.reporting` so report
loading/query/fact/doctor code can be split while the CLI, packaged scripts, and
eval share one stable import surface. New code should prefer importing from
the specific reporting module when it needs internals.
"""

from __future__ import annotations

from .reporting import (  # noqa: F401
    DoctorThresholds,
    ReportError,
    ReportRuntime,
    ReportSession,
)

__all__ = [
    "DoctorThresholds",
    "ReportError",
    "ReportRuntime",
    "ReportSession",
]
