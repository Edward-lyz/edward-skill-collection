"""Report-analysis dependency readiness helpers.

The BYO report path needs a small Python data stack, but the dependency policy
belongs in one shared helper rather than in prompt text or per-script error
strings. This module only inspects the Python environment that is actually
running the command; product packaging or the skill bootstrap decides how that
environment is populated.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import platform
import shlex
import subprocess
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any

from ..defaults import NSYS_AGENT_REPORT_REQUIREMENTS_ENV

REPORT_DEPENDENCIES = ("duckdb", "pyarrow", "pandas")


def report_dependency_status() -> dict[str, Any]:
    """Return readiness for the report-analysis packages in this Python."""

    packages = {name: _package_status(name) for name in REPORT_DEPENDENCIES}
    missing = [name for name, status in packages.items() if not status["available"]]
    payload: dict[str, Any] = {
        "ready": not missing,
        "missing": missing,
        "packages": packages,
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
    }
    if missing:
        payload["install_hint"] = report_dependency_install_hint()
    return payload


def report_dependency_install_hint() -> str:
    """Return the preferred one-line installation hint for this environment."""

    requirements = _report_requirements_path()
    if requirements and Path(requirements).is_file():
        command = _install_command(
            [sys.executable, "-m", "pip", "install", "-r", requirements]
        )
        return (
            "Install the packaged report dependencies once with: "
            f"{command}. "
            "This installs only the report stack."
        )
    extras = "nsys-agent-tools[report]"

    # The extras bracket must survive the target shell. POSIX shells treat "[" as a glob,
    # so single quotes protect it; cmd.exe/PowerShell keep the literal text but need double quotes,
    # so the whole spec stays one pasteable argument.
    quoted_extras = f'"{extras}"' if os.name == "nt" else shlex.quote(extras)
    return (
        "Install the optional report dependencies with: "
        f"pip install {quoted_extras}."
    )


def _install_command(argv: list[str]) -> str:
    """Return a pasteable install command quoted for the current platform's shell."""

    if os.name == "nt":
        return subprocess.list2cmdline(argv)
    return " ".join(shlex.quote(arg) for arg in argv)


def _package_status(name: str) -> dict[str, Any]:
    available = importlib.util.find_spec(name) is not None
    payload: dict[str, Any] = {"available": available}
    if available:
        with suppress(importlib.metadata.PackageNotFoundError):
            payload["version"] = importlib.metadata.version(name)
    return payload


def _report_requirements_path() -> str:
    return os.environ.get(NSYS_AGENT_REPORT_REQUIREMENTS_ENV, "")
