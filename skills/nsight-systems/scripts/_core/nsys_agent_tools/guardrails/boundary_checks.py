"""Product-boundary and local-safety guardrail checks."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ..capability.boundaries import (
    acknowledges_boundary,
    asks_ncu_execution,
    issue_message,
    overstates_root_cause,
    preflight_boundary_codes,
    response_boundary_codes,
)
from ..defaults import configured_report_roots
from ..path_utils import is_relative_to
from .common import _successful_tool_names
from .policy import (
    _BOUNDARY_DECLINE_PHRASES,
    _COMPARISON_REQUEST_RE,
    _COMPETITOR_COMPARISON_RE,
    _COMPETITOR_EXCLUSION_RE,
    _COMPETITOR_PROFILER_RE,
    _EXTERNAL_SQL_FUNCTION_RE,
    _GUI_ACTION_RE,
    _GUI_BOUNDARY_PHRASES,
    _HANDOFF_EVIDENCE_MARKERS,
    _HANDOFF_REPORT_ID_RE,
    _HANDOFF_TIMING_WORDS,
    _LOCAL_FILE_BOUNDARY_PHRASES,
    _LOCAL_SENSITIVE_PATH_RE,
    _RECIPE_PATH_OVERRIDE_RE,
    _REPORT_SQL_CONTRADICTION_PHRASES,
)
from .types import GuardrailIssue


def _boundary_issues(
    *,
    question: str,
    answer: str,
    report_loaded: bool,
    report_count: int | None,
    report_table_names: Iterable[str] | None,
) -> list[GuardrailIssue]:
    boundary_codes = (
        response_boundary_codes(
            question,
            answer,
            report_loaded=report_loaded,
            report_count=report_count,
            report_table_names=report_table_names,
        )
        if answer.strip()
        else preflight_boundary_codes(
            question,
            report_loaded=report_loaded,
            report_count=report_count,
            report_table_names=report_table_names,
        )
    )
    issues = [GuardrailIssue(code, issue_message(code)) for code in boundary_codes]
    if answer.strip() and overstates_root_cause(question, answer):
        issues.append(
            GuardrailIssue("open_ended_root_cause", issue_message("open_ended_root_cause"))
        )
    return issues


def _local_boundary_issues(
    question: str,
    answer: str,
    trace: list[dict[str, Any]],
    *,
    tool_evidence_text: str,
    report_loaded: bool,
    report_reference_roots: Iterable[str | Path] | None = None,
) -> list[GuardrailIssue]:
    q = question.lower()
    a = answer.lower()
    issues: list[GuardrailIssue] = []
    if (
        answer.strip()
        and (
            _asks_for_competitor_comparison(q)
            or _answer_makes_competitor_comparison(q, a)
        )
        and not _looks_like_boundary_decline(a)
    ):
        issues.append(
            GuardrailIssue(
                "competitor_comparison",
                "Competitor or 'which profiler is better' comparisons should be declined; offer factual Nsight Systems capabilities instead.",
            )
        )
    if _unsafe_recipe_path_override_request(question):
        issues.append(
            GuardrailIssue(
                "unsafe_recipe_path_override",
                "The recipe tool sets its own input and output paths, so user-supplied override flags are rejected.",
            )
        )
    if _unsafe_local_file_request(
        question,
        answer,
        report_loaded=report_loaded,
        report_reference_roots=report_reference_roots,
    ):
        issues.append(
            GuardrailIssue(
                "unsafe_local_file_guidance",
                "The answer should not provide external-file SQL or local filesystem inspection guidance; use report/recipe handles only.",
            )
        )
    if answer.strip() and _leaks_unrequested_local_path(
        question,
        answer,
        report_reference_roots=report_reference_roots,
    ):
        issues.append(
            GuardrailIssue(
                "local_path_leak",
                "The answer should not expose local cache, temporary, or recipe-output paths; use labels/handles/placeholders instead.",
            )
        )
    if answer.strip() and _asks_for_gui_action(q) and not _states_gui_boundary(a):
        issues.append(
            GuardrailIssue(
                "gui_action_boundary",
                "GUI operation requests should state that the skill cannot operate the GUI directly.",
            )
        )
    if _contradicts_successful_tool(answer, trace):
        issues.append(
            GuardrailIssue(
                "contradicts_successful_tool",
                "The answer says a tool/query failed even though the trace shows the tool succeeded.",
            )
        )
    if _omits_available_nsight_compute_handoff(
        question,
        answer,
        tool_evidence_text,
        report_loaded=report_loaded,
    ):
        issues.append(
            GuardrailIssue(
                "missing_nsight_compute_handoff_details",
                (
                    "The answer acknowledges that Nsight Compute execution is unsupported, "
                    "but should also include available Nsight Systems handoff evidence such "
                    "as candidate kernel, report label, and timing instead of stopping at a generic boundary."
                ),
            )
        )
    return issues


def _asks_for_competitor_comparison(question: str) -> bool:
    if _COMPETITOR_EXCLUSION_RE.search(question):
        return False
    return "competitor" in question or _COMPETITOR_COMPARISON_RE.search(question) is not None


def _answer_makes_competitor_comparison(question: str, answer: str) -> bool:
    """Catch generated competitor comparisons even when the request wording is noisy.

    Preflight should stay conservative and should not grow typo-specific request
    regexes.  After generation, however, the answer itself can show that the
    model crossed the reviewed product boundary: the user mentioned a
    non-NVIDIA profiler, and the final prose compares it against Nsight
    Systems.  This keeps the policy semantic without adding per-eval misspelling
    branches.
    """

    if _COMPETITOR_EXCLUSION_RE.search(question):
        return False
    if not _COMPETITOR_PROFILER_RE.search(question):
        return False
    if _COMPETITOR_COMPARISON_RE.search(answer):
        return True
    mentions_nsys = bool(re.search(r"\b(nsight\s+systems|nsys)\b", answer, flags=re.IGNORECASE))
    mentions_competitor = bool(_COMPETITOR_PROFILER_RE.search(answer))
    if not (mentions_nsys and mentions_competitor):
        return False
    return _COMPARISON_REQUEST_RE.search(question) is not None or _COMPARISON_REQUEST_RE.search(answer) is not None


def _looks_like_boundary_decline(answer: str) -> bool:
    return any(phrase in answer for phrase in _BOUNDARY_DECLINE_PHRASES)


def _unsafe_local_file_request(
    question: str,
    answer: str,
    *,
    report_loaded: bool,
    report_reference_roots: Iterable[str | Path] | None = None,
) -> bool:
    asks_external = bool(_LOCAL_SENSITIVE_PATH_RE.search(question)) or bool(
        _EXTERNAL_SQL_FUNCTION_RE.search(question)
    )
    if not asks_external:
        return False
    if (
        report_loaded
        and _mentions_loaded_report_reference(question, report_reference_roots=report_reference_roots)
        and not _EXTERNAL_SQL_FUNCTION_RE.search(question)
    ):
        answer_requests_external_access = bool(_EXTERNAL_SQL_FUNCTION_RE.search(answer))
        answer_mentions_sensitive_path = bool(_LOCAL_SENSITIVE_PATH_RE.search(answer))
        if not answer.strip() or not (answer_requests_external_access or answer_mentions_sensitive_path):
            return False
        if answer_mentions_sensitive_path and _all_sensitive_paths_are_report_references(
            answer,
            report_reference_roots=report_reference_roots,
        ):
            return False
    # Repeating a user-provided path in a refusal is acceptable. Providing a
    # local DuckDB/file-inspection recipe is not.
    provides_external_sql = bool(_EXTERNAL_SQL_FUNCTION_RE.search(answer)) and (
        "select" in answer.lower() or "create" in answer.lower() or "from" in answer.lower()
    )
    suggests_sensitive_path = bool(_LOCAL_SENSITIVE_PATH_RE.search(answer)) and not _looks_like_boundary_decline(
        answer.lower()
    )
    explicit_boundary = any(phrase in answer.lower() for phrase in _LOCAL_FILE_BOUNDARY_PHRASES)
    return provides_external_sql or suggests_sensitive_path or not explicit_boundary


def _unsafe_recipe_path_override_request(question: str) -> bool:
    lower = question.lower()
    if "recipe" not in lower and "nsys recipe" not in lower:
        return False
    if "override" in lower and ("runtime path" in lower or "runtime paths" in lower):
        return True
    return bool(_RECIPE_PATH_OVERRIDE_RE.search(question))


def _leaks_unrequested_local_path(
    question: str,
    answer: str,
    *,
    report_reference_roots: Iterable[str | Path] | None = None,
) -> bool:
    """Return whether final prose exposes local paths unrelated to report input.

    User-provided report paths may need to appear in command examples. Derived
    cache paths, recipe-output roots, temp directories, and host workspace paths
    should not appear in final prose; the agent should use labels, handles, or
    placeholders instead.
    """

    question_paths = set(_sensitive_path_mentions(question))
    for path in _sensitive_path_mentions(answer):
        if path in question_paths:
            continue
        if _mentions_native_report_path(path) or _is_configured_report_path(
            path,
            report_reference_roots=report_reference_roots,
        ):
            continue
        return True
    return False


def _sensitive_path_mentions(text: str) -> tuple[str, ...]:
    return tuple(
        match.group(0).rstrip(".,;:)`'\"")
        for match in _LOCAL_SENSITIVE_PATH_RE.finditer(text)
    )


def _mentions_native_report_path(text: str) -> bool:
    return bool(re.search(r"\.(?:nsys-rep|qdrep)\b", text, flags=re.IGNORECASE))


def _mentions_loaded_report_reference(
    text: str,
    *,
    report_reference_roots: Iterable[str | Path] | None = None,
) -> bool:
    """Return whether path-like text points at a report input, not arbitrary files.

    Callers may pass the loaded report input as an explicit allowed root. BYO
    hosts and eval harnesses can add broader allowed roots with
    ``NSYS_AGENT_REPORT_ROOTS`` when an LLM controls report paths before any
    report is loaded. This check should not hard-code harness-specific roots
    such as ``/workspace/input``.
    """

    return _mentions_native_report_path(text) or any(
        _is_configured_report_path(
            match.group(0).rstrip(".,;:)"),
            report_reference_roots=report_reference_roots,
        )
        for match in _LOCAL_SENSITIVE_PATH_RE.finditer(text)
    )


def _all_sensitive_paths_are_report_references(
    text: str,
    *,
    report_reference_roots: Iterable[str | Path] | None = None,
) -> bool:
    matches = [
        match.group(0).rstrip(".,;:)")
        for match in _LOCAL_SENSITIVE_PATH_RE.finditer(text)
    ]
    return bool(matches) and all(
        _mentions_native_report_path(path)
        or _is_configured_report_path(path, report_reference_roots=report_reference_roots)
        for path in matches
    )


def _is_configured_report_path(
    path: str,
    *,
    report_reference_roots: Iterable[str | Path] | None = None,
) -> bool:
    roots = _configured_report_roots(report_reference_roots)
    if not roots:
        return False
    candidate = Path(path).expanduser().resolve(strict=False)
    return any(is_relative_to(candidate, root) for root in roots)


def _configured_report_roots(extra_roots: Iterable[str | Path] | None = None) -> tuple[Path, ...]:
    roots = list(configured_report_roots())
    for item in extra_roots or ():
        roots.append(Path(item).expanduser().resolve(strict=False))
    return tuple(roots)


def _asks_for_gui_action(question_lower: str) -> bool:
    return bool(_GUI_ACTION_RE.search(question_lower))


def _states_gui_boundary(answer_lower: str) -> bool:
    return any(phrase in answer_lower for phrase in _GUI_BOUNDARY_PHRASES)


def _omits_available_nsight_compute_handoff(
    question: str,
    answer: str,
    tool_evidence_text: str,
    *,
    report_loaded: bool,
) -> bool:
    """Require useful Nsys handoff details when an Nsight Compute request has report evidence.

    Nsight Systems should not pretend to run Nsight Compute, but a loaded report
    can still provide candidate-kernel metadata for a separate Nsight Compute pass. This is
    a product-quality backstop: it does not choose a kernel or route tools, it
    only prevents an unhelpful generic "I cannot run Nsight Compute" answer when the trace
    already contains kernel evidence.
    """

    if not (report_loaded and asks_ncu_execution(question) and answer.strip()):
        return False
    answer_lower = answer.lower()
    if not acknowledges_boundary(answer_lower, "ncu_execution_unsupported"):
        return False
    if not _has_handoff_candidate_evidence(tool_evidence_text):
        return False
    return not _answer_mentions_specific_handoff_candidate(answer_lower)


def _has_handoff_candidate_evidence(tool_evidence_text: str) -> bool:
    text = tool_evidence_text.lower()
    return '"kernel_name"' in text and any(marker in text for marker in _HANDOFF_EVIDENCE_MARKERS)


def _answer_mentions_specific_handoff_candidate(answer_lower: str) -> bool:
    if not any(token in answer_lower for token in ("kernel", "candidate")):
        return False
    has_report_identity = ".nsys-rep" in answer_lower or _HANDOFF_REPORT_ID_RE.search(answer_lower) is not None
    has_timing = any(unit in answer_lower for unit in _HANDOFF_TIMING_WORDS)
    return has_report_identity and has_timing


def _contradicts_successful_tool(answer: str, trace: list[dict[str, Any]]) -> bool:
    lower = answer.lower().replace("’", "'")
    successful = _successful_tool_names(trace)
    if "nsys_query_report" in successful and any(
        phrase in lower for phrase in _REPORT_SQL_CONTRADICTION_PHRASES
    ):
        return True
    if (
        "nsys_query_recipe_output" in successful
        and "recipe output" in lower
        and any(phrase in lower for phrase in ("querying the parquet", "query the parquet", "nsys_query_recipe_output"))
    ):
        return any(phrase in lower for phrase in ("failed", "blocked", "file-access restriction", "file access restriction"))
    return False
