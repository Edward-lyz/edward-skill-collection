"""Shared report-boundary guidance and SQL boundary checks.

Report tools expose measured Nsight Systems evidence, but a few product
boundaries are easy for agents to cross while working with reports:

* local cache/output paths are implementation details and must stay hidden;
* recipe/domain metrics such as communication/compute overlap require a
  recipe-owned workflow, not an ad-hoc raw-table query.

Keep this module declarative and tied to the reviewed capability contract.  It
is intentionally not an eval router: callers pass user/question context when
available, and SQL receives structured warnings instead of being rejected when
it approaches unsupported recipe/domain semantics.
"""

from __future__ import annotations

import re
from typing import Any

from ..boundary_text import (
    DERIVED_ANALYSIS_VERBS_RE,
    LOCAL_PATH_LEAK_MESSAGE,
    RECIPE_DOMAIN_SEMANTIC_TERMS_RE,
    RECIPE_DOMAIN_SEMANTICS_MESSAGE,
)
from ..domain_semantics import recipe_domain_sql_alias_terms_re

_RECIPE_DOMAIN_CODE = "recipe_domain_semantics_unvalidated"
_LOCAL_PATH_CODE = "local_path_leak"

_SQL_SINGLE_QUOTED_STRING_RE = re.compile(r"'(?:''|[^'])*'", re.DOTALL)
# SQL alias signals are intentionally narrower than the user-question product
# boundary terms in boundary_text.py.  A raw report query can expose supporting
# facts with many labels; warn only on aliases that look like recipe-owned
# output metrics, and leave final overclaim enforcement to response guardrails.
_RECIPE_DOMAIN_SQL_ALIAS_RE = re.compile(
    rf"\b{recipe_domain_sql_alias_terms_re()}\b",
    re.IGNORECASE,
)
_GENERIC_OVERLAP_OR_EXPOSED_RE = re.compile(r"\b(?:overlap|overlapped|exposed)\w*\b", re.IGNORECASE)
_DOMAIN_SQL_CONTEXT_RE = re.compile(
    r"\b(?:comm|communication|compute|mpi|nccl|gpu)\w*\b",
    re.IGNORECASE,
)
_INTERVAL_OVERLAP_SQL_RE = re.compile(
    r"\b(?:greatest|max)\s*\(.+\b(?:least|min)\s*\(|"
    r"\b(?:least|min)\s*\(.+\b(?:greatest|max)\s*\(",
    re.IGNORECASE | re.DOTALL,
)
_RECIPE_DOMAIN_QUESTION_RE = re.compile(
    rf"\b{DERIVED_ANALYSIS_VERBS_RE}\b.{{0,140}}\b{RECIPE_DOMAIN_SEMANTIC_TERMS_RE}\b|"
    rf"\b{RECIPE_DOMAIN_SEMANTIC_TERMS_RE}\b.{{0,140}}"
    r"\b(?:with|using|from|via|over|query|duckdb|sql|raw\s+tables?|report\s+tables?)\b",
    re.IGNORECASE,
)


def report_boundary_guidance() -> list[dict[str, str]]:
    """Return stable, compact guidance carried by report-facing payloads."""

    return [
        {
            "code": _LOCAL_PATH_CODE,
            "message": LOCAL_PATH_LEAK_MESSAGE,
            "use": "report_label, output_handle/output_label, sanitized file names, and bounded previews",
            "avoid": "cache paths, recipe-output roots, temporary directories, and host workspace paths",
        },
        {
            "code": _RECIPE_DOMAIN_CODE,
            "message": RECIPE_DOMAIN_SEMANTICS_MESSAGE,
            "use": "an installed recipe/domain workflow, or clearly labeled supporting facts only",
            "avoid": "validated overlap, exposed-communication, straggler, utilization-map, or pacing metrics from raw SQL",
        },
    ]


def recipe_domain_query_warning(sql: str, *, question: str = "") -> dict[str, Any] | None:
    """Return a structured warning for recipe/domain semantic SQL.

    ``question`` is optional because BYO scripts and ad-hoc CLI calls may not
    have it.  Treat it as an advisory hint, not as an enforcement mechanism:
    recipe/domain semantics are not unsafe to inspect as raw supporting facts;
    the unsafe step is presenting them as validated recipe-owned metrics
    without a recipe/domain workflow.
    """

    sql_signal = _explicit_recipe_domain_sql_metric(sql)
    question_signal = bool(question and _asks_recipe_domain_semantic_analysis(question))
    interval_overlap_math = _contains_interval_overlap_math(sql)
    if not (question_signal or (sql_signal and interval_overlap_math)):
        return None
    return {
        "code": _RECIPE_DOMAIN_CODE,
        "message": RECIPE_DOMAIN_SEMANTICS_MESSAGE,
        "sql_signal": sql_signal,
        "question_signal": question_signal,
        "interval_overlap_math": interval_overlap_math,
        "supporting_facts_allowed": True,
        "guidance": (
            "Treat these SQL results as supporting facts only; do not present them "
            "as validated exposed-communication, overlap, straggler, utilization-map, "
            "or pacing metrics without an installed recipe/domain workflow."
        ),
    }


def _explicit_recipe_domain_sql_metric(sql: str) -> str:
    normalized = _sql_identifier_text(sql)
    explicit = _RECIPE_DOMAIN_SQL_ALIAS_RE.search(normalized)
    if explicit:
        return explicit.group(0)
    if _GENERIC_OVERLAP_OR_EXPOSED_RE.search(normalized) and _DOMAIN_SQL_CONTEXT_RE.search(normalized):
        return "overlap/exposed metric alias"
    return ""


def _asks_recipe_domain_semantic_analysis(text: str) -> bool:
    return bool(_RECIPE_DOMAIN_QUESTION_RE.search(text or ""))


def _contains_interval_overlap_math(sql: str) -> bool:
    normalized = _sql_identifier_text(sql)
    return (
        bool(_INTERVAL_OVERLAP_SQL_RE.search(normalized))
        and "start" in normalized.lower()
        and "end" in normalized.lower()
        and bool(_DOMAIN_SQL_CONTEXT_RE.search(normalized))
    )


def _sql_identifier_text(sql: str) -> str:
    """Return SQL with literals stripped and identifier separators normalized."""

    without_literals = _SQL_SINGLE_QUOTED_STRING_RE.sub(" ", sql or "")
    return re.sub(r"[_/.-]+", " ", without_literals)
