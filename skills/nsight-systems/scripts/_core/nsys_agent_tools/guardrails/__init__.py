"""Response guardrail orchestration.

This module is intentionally small: it coordinates reviewed boundary checks,
report evidence checks, CLI/recipe/env claim checks, and local safety checks.
The regex/word-set signals live in ``guardrails.policy`` and the check bodies
live in focused modules in this package so product policy does not hide
inside the agent loop.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .boundary_checks import _boundary_issues, _local_boundary_issues
from .common import _successful_tool_names
from .entities import build_entity_index
from .evidence_checks import (
    _cli_claim_issues,
    _env_claim_issues,
    _recipe_claim_issues,
    _report_evidence_issues,
)
from .types import EntityIndex, GuardrailIssue, GuardrailResult

__all__ = [
    "EntityIndex",
    "GuardrailIssue",
    "GuardrailResult",
    "build_entity_index",
    "check_response",
]


def check_response(
    *,
    question: str,
    answer: str,
    trace: list[dict[str, Any]],
    tool_evidence_text: str,
    report_loaded: bool,
    entity_index: EntityIndex,
    report_count: int | None = None,
    report_table_names: Iterable[str] | None = None,
    report_reference_roots: Iterable[str | Path] | None = None,
) -> GuardrailResult:
    tool_names = {str(item.get("tool")) for item in trace}
    successful_tool_names = _successful_tool_names(trace)
    q = question.lower()
    a = answer.lower()

    issues: list[GuardrailIssue] = []
    issues.extend(
        _boundary_issues(
            question=question,
            answer=answer,
            report_loaded=report_loaded,
            report_count=report_count,
            report_table_names=report_table_names,
        )
    )
    issues.extend(
        _local_boundary_issues(
            question,
            answer,
            trace,
            tool_evidence_text=tool_evidence_text,
            report_loaded=report_loaded,
            report_reference_roots=report_reference_roots,
        )
    )
    issues.extend(
        _report_evidence_issues(
            question_lower=q,
            answer=answer,
            answer_lower=a,
            tool_evidence_text=tool_evidence_text,
            tool_names=tool_names,
            successful_tool_names=successful_tool_names,
            report_loaded=report_loaded,
            entity_index=entity_index,
        )
    )
    issues.extend(
        _cli_claim_issues(
            question=question,
            question_lower=q,
            answer=answer,
            successful_tool_names=successful_tool_names,
            tool_evidence_text=tool_evidence_text,
            entity_index=entity_index,
        )
    )
    issues.extend(
        _recipe_claim_issues(
            question=question,
            question_lower=q,
            answer=answer,
            successful_tool_names=successful_tool_names,
            tool_evidence_text=tool_evidence_text,
            entity_index=entity_index,
            existing_issue_codes={issue.code for issue in issues},
        )
    )
    issues.extend(_env_claim_issues(answer, tool_evidence_text=tool_evidence_text, entity_index=entity_index))

    return GuardrailResult(_dedupe_issues(issues))


def _dedupe_issues(issues: Iterable[GuardrailIssue]) -> tuple[GuardrailIssue, ...]:
    """Return issues with first occurrence per guardrail code preserved."""

    deduped: list[GuardrailIssue] = []
    seen: set[str] = set()
    for issue in issues:
        if issue.code in seen:
            continue
        seen.add(issue.code)
        deduped.append(issue)
    return tuple(deduped)
