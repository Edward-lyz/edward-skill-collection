"""Report loading, query, fact, and doctor implementation modules.

This package owns data access for native reports, Parquet/DuckDB cache
preparation, bounded SQL, deterministic facts, and report health checks. It must
not depend on higher-level agent adapters.
"""

from .doctor import DoctorThresholds
from .runtime import ReportRuntime
from .types import ReportError, ReportSession

__all__ = [
    "DoctorThresholds",
    "ReportError",
    "ReportRuntime",
    "ReportSession",
]
