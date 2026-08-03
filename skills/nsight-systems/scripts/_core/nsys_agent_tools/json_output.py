"""Consistent JSON emission for agent-facing command-line tools."""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from .prompt_safety import sanitize_value


def emit_json(
    payload: Any,
    *,
    sort_keys: bool = True,
    max_string_chars: int = 20000,
    file: TextIO | None = None,
) -> None:
    """Print sanitized, deterministic JSON to stdout."""

    safe = sanitize_value(payload, max_string_chars=max_string_chars)
    print(json.dumps(safe, indent=2, sort_keys=sort_keys), file=file or sys.stdout)
