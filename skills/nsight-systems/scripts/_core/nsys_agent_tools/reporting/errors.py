"""Shared error handling for report helper scripts."""

from __future__ import annotations

import os
from pathlib import Path

from ..cli_tools import nsys_failure_hint
from ..prompt_safety import exception_message, sanitize_text


def safe_report_cli_error(
    nsys_path: str,
    exc: Exception,
    *,
    report_path: str | os.PathLike[str] | None = None,
) -> str:
    """Return a redacted, actionable report-script error.

    Missing report inputs and missing ``nsys`` binaries both surface as
    ``FileNotFoundError``. Keep those cases distinct so BYO scripts do not tell
    users to fix ``NSYS_PATH`` when the actual problem is the report argument.
    """

    if _is_missing_report_input(exc, report_path):
        name = Path(report_path).expanduser().name if report_path else "report"
        return f"report input not found: {name}"
    text = _safe_error_text(exc)
    if _looks_like_missing_nsys(exc, nsys_path):
        return nsys_failure_hint(nsys_path, exc)
    return text


def _safe_report_error(exc: Exception, report: Path) -> str:
    text = f"{type(exc).__name__}: {exc}"
    return sanitize_text(text.replace(str(report), report.name).replace(str(report.parent), "<report-dir>"))


def _safe_error_text(exc: Exception) -> str:
    return exception_message(exc, max_chars=4000)


def _is_missing_report_input(exc: Exception, report_path: str | os.PathLike[str] | None) -> bool:
    if report_path is None or not isinstance(exc, FileNotFoundError):
        return False
    filename = getattr(exc, "filename", None)
    report = Path(report_path).expanduser()
    if filename is not None:
        try:
            return Path(filename).expanduser().resolve() == report.resolve()
        except OSError:
            return Path(filename).expanduser().name == report.name
    return str(exc) == report.name or report.name in str(exc)


def _looks_like_missing_nsys(exc: Exception, nsys_path: str) -> bool:
    if not isinstance(exc, FileNotFoundError):
        return False
    filename = getattr(exc, "filename", None)
    if filename is None:
        # Some subprocess wrappers raise FileNotFoundError without filename but
        # include the executable token in the message. Keep the detection narrow
        # so unrelated missing files do not become misleading NSYS_PATH hints.
        text = str(exc).lower()
        return Path(nsys_path).name.lower() in text
    try:
        return Path(filename).expanduser().resolve() == Path(nsys_path).expanduser().resolve()
    except OSError:
        return Path(filename).expanduser().name == Path(nsys_path).expanduser().name
