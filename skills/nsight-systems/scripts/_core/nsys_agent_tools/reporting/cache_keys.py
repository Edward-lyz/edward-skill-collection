"""Cache-key helpers for report-derived DuckDB artifacts."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


def multi_report_cache_key(
    reports: tuple[Path, ...],
    nsys_path: str,
    *,
    table_patterns: tuple[str, ...] = (),
) -> str:
    parts = [_nsys_cache_identity(nsys_path)]
    if table_patterns:
        parts.append("tables=" + ",".join(sorted(table_patterns)))
    for report in reports:
        stat = report.stat()
        parts.append(f"{report}:{stat.st_mtime_ns}:{stat.st_size}")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def _nsys_cache_identity(nsys_path: str) -> str:
    """Return a cheap cache identity for the configured Nsys exporter."""

    candidate = Path(nsys_path).expanduser()
    if not candidate.exists() and not candidate.is_absolute():
        resolved = shutil.which(nsys_path)
        if resolved:
            candidate = Path(resolved)
    try:
        resolved_path = candidate.resolve()
        stat = resolved_path.stat()
    except OSError:
        return f"nsys={nsys_path}"
    return f"nsys={resolved_path}:{stat.st_mtime_ns}:{stat.st_size}"
