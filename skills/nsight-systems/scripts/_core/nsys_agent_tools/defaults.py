"""Shared defaults that do not import optional report dependencies."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

NSYS_AGENT_SKILL_PACK_ENV = "NSYS_AGENT_SKILL_PACK"
NSYS_AGENT_CACHE_DIR_ENV = "NSYS_AGENT_CACHE_DIR"
NSYS_AGENT_RECIPE_OUTPUT_DIR_ENV = "NSYS_AGENT_RECIPE_OUTPUT_DIR"
NSYS_AGENT_REPORT_ROOTS_ENV = "NSYS_AGENT_REPORT_ROOTS"
NSYS_AGENT_REPORT_REQUIREMENTS_ENV = "NSYS_AGENT_REPORT_REQUIREMENTS"


def configured_report_roots() -> tuple[Path, ...]:
    """Return the optional host/eval allow-list for report inputs.

    ``NSYS_AGENT_REPORT_ROOTS`` is not required for normal local use. Hosts and
    eval harnesses set it when an LLM controls ``nsys_skill_cli --report`` and the
    report argument must stay under known directories. The same roots also tell
    response guardrails which local-looking paths are legitimate report
    references rather than leaked cache or filesystem paths.
    """

    value = os.environ.get(NSYS_AGENT_REPORT_ROOTS_ENV, "")
    return tuple(
        Path(item).expanduser().resolve(strict=False)
        for item in value.split(os.pathsep)
        if item.strip()
    )


DEFAULT_AGENT_CACHE_DIR = os.environ.get(
    NSYS_AGENT_CACHE_DIR_ENV,
    str(
        Path(os.environ.get("NSYS_TMPDIR") or tempfile.gettempdir())
        / "nvidia"
        / "nsight_systems"
        / "nsys-skill-cache"
    ),
)
DEFAULT_AGENT_RECIPE_OUTPUT_DIR = os.environ.get(
    NSYS_AGENT_RECIPE_OUTPUT_DIR_ENV,
    str(Path(DEFAULT_AGENT_CACHE_DIR) / "nsys-recipe-output"),
)
