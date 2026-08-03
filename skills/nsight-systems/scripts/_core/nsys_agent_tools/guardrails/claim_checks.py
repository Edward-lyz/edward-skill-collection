"""Claim checking for the gateway ``check-claims`` command.

Given a drafted answer and its gathered evidence, report any CLI flag, recipe
name, environment variable, or report number the answer states without support.
The command runs the answer through the ``check_response`` guardrail.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..env_vars import ALLOWED_ENV_VARS
from ..process_utils import run_bounded_process
from ..tool_registry import tool_names_in_guardrail_group
from . import check_response
from .policy import _FLAG_RE
from .types import EntityIndex

_CLI_EVIDENCE_TOOLS = tool_names_in_guardrail_group("cli_evidence")
_REPORT_EVIDENCE_TOOLS = tool_names_in_guardrail_group("report_evidence")
_RECIPE_EVIDENCE_TOOLS = tool_names_in_guardrail_group("recipe_evidence")

# Report-evidence signatures. Tokens ending in "_" are prefixes of enum-style
# identifiers. The rest are complete identifiers that must match on their own.
REPORT_EVIDENCE_TOKENS = (
    "CUPTI_ACTIVITY_KIND_",
    "TARGET_INFO_",
    "returned_row_count",
    "unique_kernel_count",
    "total_frames",
    "present_call",
    "frame_time_ms",
    "api_source",
)


def check_answer_claims(
    *,
    question: str,
    answer: str,
    evidence_text: str,
    trace_tools: set[str],
    flags: set[str],
    recipes: set[str],
) -> dict[str, Any]:
    """Return ``{"ok": bool, "issues": [...]}`` for a drafted answer.

    The ``check_response`` guardrail decides whether a claim is backed by looking
    at which tools ran. The ``check-claims`` command has no live tool trace, so
    this reconstructs one: it reads the evidence text (and any ``trace_tools``)
    to infer which tools would have produced it, then delegates to
    :func:`check_response`.
    """

    evidence_flags = {match.group(1) for match in _FLAG_RE.finditer(evidence_text)}
    evidence_recipe_names = set(recipes) & set(re.findall(r"\b[a-z][a-z0-9_]{2,60}\b", evidence_text))

    has_cli_evidence = bool(trace_tools & _CLI_EVIDENCE_TOOLS) or bool(evidence_flags)
    has_report_evidence = bool(trace_tools & _REPORT_EVIDENCE_TOOLS) or _evidence_has_token(
        evidence_text, REPORT_EVIDENCE_TOKENS
    )
    has_recipe_evidence = bool(trace_tools & _RECIPE_EVIDENCE_TOOLS) or bool(evidence_recipe_names)

    synthetic_tools = set(trace_tools)
    if has_cli_evidence:
        synthetic_tools.add("nsys_inspect_cli")
    if has_report_evidence:
        synthetic_tools.add("nsys_report_fact")
    if has_recipe_evidence:
        synthetic_tools.add("nsys_lookup_recipes")
    result = check_response(
        question=question,
        answer=answer,
        # Mark each tool as a successful run. Trace-file tools are already
        # filtered to successful ones, and without an outcome the guardrails
        # treat a tool as failed and flag claims the evidence supports.
        trace=[{"tool": tool, "outcome": "ok"} for tool in sorted(synthetic_tools)],
        tool_evidence_text=evidence_text,
        report_loaded=True,
        entity_index=EntityIndex(
            flags=frozenset(flags),
            recipes=frozenset(recipes),
            env_vars=ALLOWED_ENV_VARS,
        ),
    )
    issues = result.as_dicts()
    return {"ok": not issues, "issues": issues}


def _evidence_has_token(evidence_text: str, tokens: tuple[str, ...]) -> bool:
    for token in tokens:
        # Bound the start so tokens never match inside a larger word;
        # "_" prefixes keep an open end. Complete identifiers are bounded on both ends.
        pattern = r"\b" + re.escape(token)
        if not token.endswith("_"):
            pattern += r"\b"
        if re.search(pattern, evidence_text):
            return True
    return False


def trace_tools_from_file(path: str | None) -> set[str]:
    """Return successful tool names from an optional trace JSON/JSONL file.

    Items with a recorded failure outcome are excluded so a failed tool run
    cannot back a claim. Items without an outcome field count as successful,
    since a bare tool list is the caller stating which tools ran.
    """

    if not path:
        return set()
    trace_path = Path(path)
    if not trace_path.is_file():
        return set()
    text = trace_path.read_text(encoding="utf-8-sig", errors="replace")
    return {
        str(item["tool"])
        for data in _json_documents(text)
        for item in _trace_items(data)
        if isinstance(item, dict)
        and item.get("tool")
        and str(item.get("outcome", "ok")).lower() in ("ok", "success")
    }


def _json_documents(text: str) -> list[Any]:
    """Parse one whole JSON document, or fall back to JSONL lines."""

    try:
        return [json.loads(text)]
    except json.JSONDecodeError:
        pass
    documents = []
    for line in text.splitlines():
        try:
            documents.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return documents


def _trace_items(data: Any) -> list[Any]:
    """Accept a list of items, a {"trace": [...]} document, or one bare item."""

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        trace = data.get("trace")
        return trace if isinstance(trace, list) else [data]
    return []


def recipe_names_from_index(recipe_rows: list[dict[str, Any]]) -> set[str]:
    return {str(row.get("name")) for row in recipe_rows if isinstance(row, dict) and row.get("name")}


def collect_cli_flags(nsys_path: str, recipe_rows: list[dict[str, Any]]) -> set[str]:
    """Discover known CLI flags from live nsys help and packaged recipe options."""

    flags: set[str] = set()
    for target in ("", "profile", "launch", "start", "stop", "status", "stats", "export", "recipe"):
        cmd = [nsys_path, *target.split(), "--help"] if target else [nsys_path, "--help"]
        try:
            # Local `nsys --help` discovery for claim checking. The command is
            # an argv list (no shell), time-bounded, and reads help text only.
            completed = run_bounded_process(cmd, timeout_s=12)
        except Exception:
            continue
        flags.update(match.group(1) for match in _FLAG_RE.finditer(completed.stdout + "\n" + completed.stderr))
    for row in recipe_rows:
        if isinstance(row, dict):
            flags.update(str(flag).lstrip("-") for flag in row.get("options", []) if flag)
    return flags
