#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path
from typing import Any


def _report_requirements_env_key() -> str:
    try:
        from nsys_agent_tools.defaults import NSYS_AGENT_REPORT_REQUIREMENTS_ENV
    except ImportError:
        return "NSYS_AGENT_REPORT_REQUIREMENTS"
    return NSYS_AGENT_REPORT_REQUIREMENTS_ENV


def ensure_core() -> None:
    """Prefer the vendored agent core when this script is inside a built skill pack.

    Source-tree tests/development use the editable package path instead. Built
    skill packs include `scripts/_core/nsys_agent_tools`, copied from the
    `nsys_agent_tools` package during `nsys-skill-build`, so BYO scripts and
    the installed CLI share the same implementation authority.

    It then exports NSYS_PATH in-process (if unset) so that it's propagated to
    subsequent scripts that rely on it.
    """
    core = Path(__file__).resolve().parent
    if (core / "nsys_agent_tools").is_dir():
        sys.path.insert(0, str(core))
    _populate_report_requirements_env()
    _populate_nsys_env()


def skill_pack_root() -> Path:
    root = Path(__file__).resolve().parents[2]
    if not (root / "SKILL.md").is_file():
        raise RuntimeError(f"script is not inside a built skill pack: {root}")
    return root


def print_json(payload: Any) -> None:
    """Print agent-facing JSON after applying the shared redaction sanitizer."""

    from nsys_agent_tools.prompt_safety import sanitize_value

    print(json.dumps(sanitize_value(payload, max_string_chars=20000), indent=2, sort_keys=True))


def default_cache_dir() -> str:
    """Return the BYO script cache directory."""

    from nsys_agent_tools.defaults import DEFAULT_AGENT_CACHE_DIR

    return DEFAULT_AGENT_CACHE_DIR


def default_recipe_output_dir() -> str:
    """Return the BYO script recipe-output directory."""

    from nsys_agent_tools.defaults import DEFAULT_AGENT_RECIPE_OUTPUT_DIR

    return DEFAULT_AGENT_RECIPE_OUTPUT_DIR


def _derive_platform(root: Path) -> str:
    for host_dir in sorted(root.glob("host-*")):
        if host_dir.is_dir():
            return host_dir.name.removeprefix("host-")
    machine = platform.machine().lower()
    if sys.platform == "win32":
        return "windows-armv8" if machine in ("aarch64", "arm64") else "windows-x64"
    os_name = "macos" if sys.platform == "darwin" else "linux"
    arch = "sbsa-armv8" if machine in ("aarch64", "arm64") else "x64"
    return f"{os_name}-{arch}"


def _populate_nsys_env() -> None:
    """Set NSYS_PATH (if unset) to the Nsys for this host's platform, else standard discovery."""

    if os.environ.get("NSYS_PATH"):
        return
    try:
        root = skill_pack_root().parents[1]
        from nsys_agent_tools.cli_tools import resolve_nsys

        exe = "nsys.exe" if sys.platform == "win32" else "nsys"
        skill_relative = root / f"target-{_derive_platform(root)}" / exe
        # TODO(DTSP-23276): The cached path supersedes all others, so only the paths the
        # bootstrap scripts resolve are authoritative.  Aggregate every candidate path into
        # a single source of truth and make the bootstrap scripts read it.
        cached_nsys_path = Path(default_cache_dir()) / "NSYS_PATH"
        resolved = None
        if cached_nsys_path.is_file():
            cached_raw = cached_nsys_path.read_text(encoding="utf-8").strip()
            if cached_raw:
                resolved = resolve_nsys((Path(cached_raw),))
        if not resolved:
            resolved = resolve_nsys((skill_relative,))
        if resolved:
            os.environ["NSYS_PATH"] = str(resolved)
    except Exception:
        return


def _populate_report_requirements_env() -> None:
    """Point vendored BYO scripts at their version-matched report requirements."""

    env_key = _report_requirements_env_key()
    if os.environ.get(env_key):
        return
    try:
        requirements = skill_pack_root() / "scripts" / "requirements.txt"
    except RuntimeError:
        return
    if requirements.is_file():
        os.environ[env_key] = str(requirements)
