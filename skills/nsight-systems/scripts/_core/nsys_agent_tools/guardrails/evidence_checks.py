"""Evidence-backed claim guardrail checks.

This module checks exact report/CLI/recipe/env claims after a model answer is
available. It verifies that the answer has the right evidence class; it does not
choose tools or infer product behavior from eval questions.
"""

from __future__ import annotations

import re

from ..capability.boundaries import (
    acknowledges_boundary,
    asks_custom_recipe_full_implementation,
    asks_recipe_domain_semantic_analysis,
)
from ..domain_semantics import (
    recipe_domain_answer_markers,
    recipe_domain_evidence_markers,
)
from .common import _mentions_any
from .policy import (
    _CLI_TOOLS,
    _DOCS_EXPLANATION_RE,
    _ENV_VAR_RE,
    _EXPLICIT_REPORT_WORDS,
    _FLAG_RE,
    _MEASURED_REPORT_TOOLS,
    _NO_REPORT_BOUNDARY_PHRASES,
    _RECIPE_EXECUTION_TOOLS,
    _RECIPE_EXECUTION_VERB_RE,
    _RECIPE_INVOCATION_RE,
    _RECIPE_OUTPUT_WORDS,
    _RECIPE_REFERENCE_QUESTION_WORDS,
    _RECIPE_RESULT_OR_OUTPUT_WORDS,
    _RECIPE_TOOLS,
    _RECIPE_WORDS,
    _REPORT_RANK_OR_MEASURE_WORDS,
    _REPORT_SUBJECT_WORDS,
    _REPORT_TOOLS,
    _TROUBLESHOOTING_WORDS,
    _UNIT_NUMBER_RE,
)
from .types import EntityIndex, GuardrailIssue

_COUNT_LIKE_UNITS = frozenset(
    {
        "kernel",
        "kernels",
        "launch",
        "launches",
        "call",
        "calls",
        "event",
        "events",
        "row",
        "rows",
        "sample",
        "samples",
        "thread",
        "threads",
        "process",
        "processes",
        "file",
        "files",
    }
)
_RECIPE_DOMAIN_SEMANTIC_MARKERS = recipe_domain_answer_markers()
_HIGH_CONFIDENCE_RECIPE_DOMAIN_SEMANTIC_MARKERS = recipe_domain_answer_markers(
    high_confidence_only=True,
)
_RECIPE_DOMAIN_METRIC_UNITS = frozenset({"%", "percent", "ns", "us", "ms", "s"})
_RECIPE_DOMAIN_VALUE_RE = re.compile(
    r"(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\s*"
    r"(?P<unit>%|percent|ns|us|ms|s)(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
_AMBIGUOUS_REPORT_REFERENCE_RE = re.compile(
    r"\b(?:the|this)\s+report\b(?!\s+(?:tab|view|pane|panel|selector)\b)",
    re.IGNORECASE,
)
def _report_evidence_issues(
    *,
    question_lower: str,
    answer: str,
    answer_lower: str,
    tool_evidence_text: str,
    tool_names: set[str],
    successful_tool_names: set[str],
    report_loaded: bool,
    entity_index: EntityIndex,
) -> list[GuardrailIssue]:
    issues: list[GuardrailIssue] = []
    report_intent = report_loaded and _asks_report_specific_question(
        question_lower,
        report_loaded=True,
        successful_tool_names=successful_tool_names,
    )
    unloaded_report_intent = (
        not report_loaded
        and _asks_report_specific_question(
            question_lower,
            report_loaded=False,
            successful_tool_names=successful_tool_names,
        )
        and not _asks_no_report_troubleshooting(question_lower)
        and not _allows_recipe_reference_without_loaded_report(question_lower, entity_index)
    )
    if answer.strip() and unloaded_report_intent and not _states_no_report_boundary(answer_lower):
        issues.append(
            GuardrailIssue(
                "missing_report_input",
                "The user asked for report-specific data, but no report is loaded; the answer must ask for/load a report instead of guessing.",
            )
        )
    numeric_report_claim = report_loaded and bool(_UNIT_NUMBER_RE.search(answer))
    if (report_intent or numeric_report_claim) and not (tool_names & _REPORT_TOOLS):
        issues.append(
            GuardrailIssue(
                "missing_report_evidence",
                "The answer appears to make a measured/report-specific claim without report-tool evidence.",
            )
        )
    elif (report_intent or numeric_report_claim) and not (successful_tool_names & _REPORT_TOOLS):
        issues.append(
            GuardrailIssue(
                "failed_report_evidence",
                "The answer appears to rely on report-tool evidence, but the relevant report tool call failed.",
            )
        )
    if (
        numeric_report_claim
        and not (successful_tool_names & _MEASURED_REPORT_TOOLS)
        and not _context_supports_numeric_claim(answer, successful_tool_names)
    ):
        issues.append(
            GuardrailIssue(
                "missing_numeric_evidence",
                "The answer contains unit-bearing numeric report claims without measured report/query/fact/recipe evidence.",
            )
        )
    recipe_domain_semantic_intent = asks_recipe_domain_semantic_analysis(question_lower)
    recipe_owned_semantic_intent = _asks_recipe_owned_semantic_question(question_lower, entity_index)
    recipe_domain_metric_asserted = _asserts_recipe_domain_metric(answer_lower)
    high_confidence_recipe_domain_metric_asserted = _asserts_recipe_domain_metric(
        answer_lower,
        high_confidence_only=True,
    )
    if (
        answer.strip()
        and report_loaded
        and (recipe_domain_semantic_intent or high_confidence_recipe_domain_metric_asserted)
        and recipe_domain_metric_asserted
        and not _recipe_domain_workflow_satisfied(
            question_lower,
            answer_lower,
            successful_tool_names,
            tool_evidence_text=tool_evidence_text,
        )
        and not _asks_recipe_reference_only_question(question_lower, entity_index)
    ):
        issues.append(
            GuardrailIssue(
                "recipe_domain_semantics_unvalidated",
                "The answer appears to present recipe/domain-owned performance semantics without recipe/domain workflow evidence or an explicit unsupported boundary.",
            )
        )
    elif (
        answer.strip()
        and report_loaded
        and recipe_owned_semantic_intent
        and not _recipe_semantic_workflow_satisfied(successful_tool_names)
    ):
        issues.append(
            GuardrailIssue(
                "missing_recipe_semantic_evidence",
                "The answer appears to classify a recipe-defined report concept without running the matching recipe.",
            )
        )
    if (
        report_loaded
        and "recipe" in question_lower
        and _mentions_any(question_lower, _RECIPE_OUTPUT_WORDS)
        and not (
            "nsys_run_recipe" in successful_tool_names
            and successful_tool_names & {"nsys_recipe_output_schema", "nsys_query_recipe_output"}
        )
    ):
        issues.append(
            GuardrailIssue(
                "missing_recipe_output_evidence",
                "Concrete recipe output files or columns for a loaded report require recipe execution and output-schema evidence.",
            )
        )
    return issues


def _context_supports_numeric_claim(answer: str, successful_tool_names: set[str]) -> bool:
    """Allow report-context evidence for count-like inventory numbers only.

    ``nsys_get_report_context`` exposes deterministic table row counts and
    inventory counts. It is enough for answers such as "1003 MPI event rows" or
    "65 tables", but not enough for durations, percentages, or performance
    measurements.
    """

    if "nsys_get_report_context" not in successful_tool_names:
        return False
    matches = list(_UNIT_NUMBER_RE.finditer(answer))
    return bool(matches) and all(match.group(3).lower() in _COUNT_LIKE_UNITS for match in matches)


def _cli_claim_issues(
    *,
    question: str,
    question_lower: str,
    answer: str,
    successful_tool_names: set[str],
    tool_evidence_text: str,
    entity_index: EntityIndex,
) -> list[GuardrailIssue]:
    issues: list[GuardrailIssue] = []

    flags = {m.group(1) for m in _FLAG_RE.finditer(answer)}
    # Ignore common markdown option placeholders that are not asserted as nsys flags.
    evidence_flags = _flags_in_evidence(tool_evidence_text)
    unknown_flags = sorted(
        flag
        for flag in flags
        if flag not in entity_index.flags
        and flag not in evidence_flags
        and not (f"--{flag}" in question and (successful_tool_names & _CLI_TOOLS or _negative_flag_context(answer, flag)))
    )
    if unknown_flags:
        issues.append(GuardrailIssue("unknown_cli_flags", "Unverified CLI flags: " + ", ".join(f"--{f}" for f in unknown_flags[:12])))
    if (
        flags
        and ("nsys" in answer.lower() or "flag" in question_lower or "option" in question_lower or "command" in question_lower)
        and not (successful_tool_names & _CLI_TOOLS)
        and not flags.issubset(evidence_flags)
    ):
        issues.append(GuardrailIssue("missing_cli_help", "CLI flags or exact nsys syntax were asserted without live CLI-help evidence."))
    return issues


def _recipe_claim_issues(
    *,
    question: str,
    question_lower: str,
    answer: str,
    successful_tool_names: set[str],
    tool_evidence_text: str,
    entity_index: EntityIndex,
    existing_issue_codes: set[str],
) -> list[GuardrailIssue]:
    issues: list[GuardrailIssue] = []
    recipes = {m.group(1) for m in _RECIPE_INVOCATION_RE.finditer(answer)}
    unknown_recipes = sorted(recipe for recipe in recipes if recipe not in entity_index.recipes and recipe not in tool_evidence_text)
    if unknown_recipes:
        issues.append(GuardrailIssue("unknown_recipes", "Unverified recipe invocations: " + ", ".join(unknown_recipes[:12])))
    named_recipes = _known_recipe_names_in_text(answer, entity_index)
    if (
        named_recipes
        and not (successful_tool_names & _RECIPE_TOOLS)
        and "missing_recipe_evidence" not in existing_issue_codes
    ):
        issues.append(GuardrailIssue("missing_recipe_evidence", "The answer names recipe(s) without recipe lookup/help/execution evidence."))
    if (
        _mentions_recipe_topic(question_lower, entity_index)
        and not (successful_tool_names & _RECIPE_TOOLS)
        and "custom_recipe_full_generation" not in existing_issue_codes
        and not (
            asks_custom_recipe_full_implementation(question)
            and acknowledges_boundary(answer, "custom_recipe_full_generation")
        )
    ):
        issues.append(GuardrailIssue("missing_recipe_evidence", "Recipe-specific answer was produced without recipe lookup/help/execution evidence."))
    return issues


def _known_recipe_names_in_text(answer: str, entity_index: EntityIndex) -> set[str]:
    """Return recipe names from the reviewed recipe index that appear in text."""

    tokens = set(re.findall(r"\b[a-z][a-z0-9_]{2,60}\b", answer))
    return {token for token in tokens if token in entity_index.recipes}


def _env_claim_issues(
    answer: str,
    *,
    tool_evidence_text: str,
    entity_index: EntityIndex,
) -> list[GuardrailIssue]:
    issues: list[GuardrailIssue] = []
    env_vars = _env_vars_in_text(answer)
    unknown_env = sorted(
        env
        for env in env_vars
        if env not in entity_index.env_vars and env not in tool_evidence_text
    )
    if unknown_env:
        issues.append(
            GuardrailIssue(
                "unknown_env_vars",
                "Unverified environment variables: " + ", ".join(unknown_env[:12]),
            )
        )
    return issues


def _env_vars_in_text(text: str) -> set[str]:
    """Return env vars from shell-like mentions without flagging every acronym."""

    return {
        group
        for match in _ENV_VAR_RE.finditer(text or "")
        for group in match.groups()
        if group
    }


def _asks_report_specific_question(
    question_lower: str,
    *,
    report_loaded: bool,
    successful_tool_names: set[str],
) -> bool:
    """Detect report-data requests without treating generic words as report-only.

    A word like "highest" is not enough by itself: "highest supported CUDA
    version" is a documentation question, while "highest CUDA API duration" is
    report data. When a report is already loaded, subject-only follow-ups such
    as "what GPU is being used" should still count as report-specific.
    """

    if _docs_evidence_supports_conceptual_report_wording(question_lower, successful_tool_names):
        return False
    if _mentions_any(question_lower, _EXPLICIT_REPORT_WORDS):
        return True
    has_subject = _mentions_any(question_lower, _REPORT_SUBJECT_WORDS)
    if not has_subject:
        return False
    if report_loaded:
        return True
    return _mentions_any(question_lower, _REPORT_RANK_OR_MEASURE_WORDS)


def _docs_evidence_supports_conceptual_report_wording(
    question_lower: str,
    successful_tool_names: set[str],
) -> bool:
    """Allow docs-grounded concept answers that mention opening a report.

    Do not maintain a hardcoded UI taxonomy here. The guardrail only verifies
    that a successful docs lookup answered a conceptual/explanatory question,
    while measured or user-specific report questions remain on the report path.
    """

    if "nsys_search_docs" not in successful_tool_names:
        return False
    if _mentions_specific_report_reference(question_lower):
        return False
    if not _DOCS_EXPLANATION_RE.search(question_lower):
        return False
    return not (
        _mentions_any(question_lower, _REPORT_SUBJECT_WORDS)
        or _mentions_any(question_lower, _REPORT_RANK_OR_MEASURE_WORDS)
    )


def _mentions_specific_report_reference(question_lower: str) -> bool:
    unambiguous_phrases = _EXPLICIT_REPORT_WORDS - {"the report", "this report"}
    return _mentions_any(question_lower, unambiguous_phrases) or bool(
        _AMBIGUOUS_REPORT_REFERENCE_RE.search(question_lower)
    )


def _mentions_recipe_topic(question_lower: str, entity_index: EntityIndex) -> bool:
    """Detect recipe-specific answers from generic terms or known recipe names."""

    if _mentions_any(question_lower, _RECIPE_WORDS):
        return True
    tokens = set(re.findall(r"\b[a-z][a-z0-9_]{2,80}\b", question_lower))
    return bool(tokens & set(entity_index.recipes))


def _flags_in_evidence(text: str) -> set[str]:
    return {m.group(1) for m in _FLAG_RE.finditer(text or "")}


def _asks_recipe_owned_semantic_question(question_lower: str, entity_index: EntityIndex) -> bool:
    """Detect questions whose answer depends on recipe-owned classification.

    This is a guardrail category, not a recipe router. Recovery uses recipe
    lookup metadata to choose a recipe rather than mapping phrases to recipe
    names in Python.
    """

    return any(
        all(any(token in question_lower for token in group) for group in concept)
        for concept in entity_index.recipe_owned_concepts
    )


def _recipe_semantic_workflow_satisfied(
    successful_tool_names: set[str],
) -> bool:
    return bool(successful_tool_names & _RECIPE_EXECUTION_TOOLS)


def _recipe_domain_workflow_satisfied(
    question_lower: str,
    answer_lower: str,
    successful_tool_names: set[str],
    *,
    tool_evidence_text: str,
) -> bool:
    """Require recipe execution evidence that is tied to the semantic being asserted."""

    if not _recipe_semantic_workflow_satisfied(successful_tool_names):
        return False
    semantic_text = "\n".join((question_lower, answer_lower))
    evidence_lower = (tool_evidence_text or "").lower()
    markers = _semantic_markers_in_text(semantic_text)
    if not markers:
        return False
    return any(marker in evidence_lower for marker in _evidence_markers_for_semantic(semantic_text, markers))


def _asserts_recipe_domain_metric(answer_lower: str, *, high_confidence_only: bool = False) -> bool:
    markers = _semantic_markers_in_text(answer_lower, high_confidence_only=high_confidence_only)
    if not markers:
        return False
    for match in _RECIPE_DOMAIN_VALUE_RE.finditer(answer_lower):
        unit = match.group("unit").lower()
        if unit not in _RECIPE_DOMAIN_METRIC_UNITS:
            continue
        window = answer_lower[max(0, match.start() - 100) : match.end() + 100]
        if any(marker in window for marker in markers):
            return True
    return False


def _semantic_markers_in_text(text: str, *, high_confidence_only: bool = False) -> tuple[str, ...]:
    markers = (
        _HIGH_CONFIDENCE_RECIPE_DOMAIN_SEMANTIC_MARKERS
        if high_confidence_only
        else _RECIPE_DOMAIN_SEMANTIC_MARKERS
    )
    return tuple(marker for marker in markers if marker in text)


def _evidence_markers_for_semantic(semantic_text: str, markers: tuple[str, ...]) -> tuple[str, ...]:
    return recipe_domain_evidence_markers(semantic_text, markers)


def _asks_recipe_reference_only_question(question_lower: str, entity_index: EntityIndex) -> bool:
    """Allow recipe-selection/syntax answers without forcing recipe execution.

    A user can ask "which recipe should I use for overlap?" without asking this
    runtime to compute the metric now.  Those answers still need recipe lookup
    evidence through the normal recipe-claim checks; they should not be blocked
    by the recipe-domain metric guardrail.
    """

    if not _mentions_recipe_topic(question_lower, entity_index):
        return False
    if _RECIPE_EXECUTION_VERB_RE.search(question_lower):
        return False
    return any(
        phrase in question_lower
        for phrase in (
            "which recipe",
            "what recipe",
            "what recipes",
            "list recipe",
            "list recipes",
            "available recipe",
            "available recipes",
            "recipe should",
            "recipe can",
            "recipes can",
            "how do i run",
            "how to run",
            "what command",
        )
    )


def _states_no_report_boundary(answer_lower: str) -> bool:
    return any(phrase in answer_lower for phrase in _NO_REPORT_BOUNDARY_PHRASES)


def _asks_no_report_troubleshooting(question_lower: str) -> bool:
    return _mentions_any(question_lower, _TROUBLESHOOTING_WORDS)


def _allows_recipe_reference_without_loaded_report(question_lower: str, entity_index: EntityIndex) -> bool:
    """Let recipe reference questions use recipe docs without a report.

    Recipe-selection and recipe-syntax questions often mention report-schema
    subjects such as CUDA API time, kernel duration, or memory copies. Those
    words should not force the missing-report boundary unless the user also
    asks about a concrete report or asks to run/evaluate recipe output.
    """

    if not _mentions_recipe_topic(question_lower, entity_index):
        return False
    if _mentions_any(question_lower, _EXPLICIT_REPORT_WORDS):
        return False
    if _RECIPE_EXECUTION_VERB_RE.search(question_lower) or _mentions_any(
        question_lower,
        _RECIPE_RESULT_OR_OUTPUT_WORDS,
    ):
        return False
    return _mentions_any(question_lower, _RECIPE_REFERENCE_QUESTION_WORDS)


def _negative_flag_context(answer: str, flag: str) -> bool:
    negative_words = r"(not|no|absent|unsupported|does not|doesn't|isn't|not found|unverified)"
    escaped_flag = re.escape(flag)
    pattern = re.compile(
        rf"(?i){negative_words}.{{0,120}}--{escaped_flag}"
        rf"|--{escaped_flag}.{{0,120}}{negative_words}"
    )
    return pattern.search(answer) is not None
