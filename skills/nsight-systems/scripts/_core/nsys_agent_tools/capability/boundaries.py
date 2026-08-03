"""Runtime helpers for the structured unsupported-capability contract.

The contract data lives in :mod:`nsys_agent_tools.capability.contract` so product policy can be
reviewed separately from helper logic.  This module evaluates that contract and
keeps the small public helper functions used by guardrails and tests.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from .contract import (
    BoundaryContext,
    CapabilityBoundary,
    CapabilityBoundarySpec,
    CapabilityPlan,
    EvidenceRequirement,
)
from .policy import (
    BOUNDARY_KEYWORD_STOPWORDS,
    BOUNDARY_SPECS,
    CUSTOM_RECIPE_FILE_SECTION_RE,
    NCU_DEFINITIVE_ROOT_CAUSE_PHRASES,
    NCU_NUMERIC_METRIC_CLAIM_RE,
    NCU_ROOT_CAUSE_TERMS,
    ROOT_CAUSE_CAUTION_PHRASES,
    ROOT_CAUSE_DEFINITIVE_PHRASES,
    TEXT_SIGNALS,
)

_BOUNDARIES = {spec.code: spec.boundary() for spec in BOUNDARY_SPECS}
_SPECS_BY_CODE = {spec.code: spec for spec in BOUNDARY_SPECS}
_SIGNALS = {signal.name: signal for signal in TEXT_SIGNALS}
_REPORT_EVIDENCE_SIGNALS = frozenset(
    {
        "cross_report_comparison",
        "sampled_metric_region_ranking",
        "kernel_metric_overlap",
        "workload_fingerprinting",
        "application_metric",
        "os_runtime_request",
        "multi_hop_correlation",
    }
)
_RECIPE_REFERENCE_SIGNALS = frozenset(
    {"custom_recipe_assist", "custom_recipe_full_generation"}
)
_HANDOFF_GUIDANCE_SIGNALS = frozenset({"ncu_execution", "ncu_metric_semantics"})
_RECIPE_DOMAIN_ANALYSIS_SIGNALS = frozenset({"recipe_domain_semantic_analysis"})
_BOUNDARY_ACKNOWLEDGEMENT_RE = re.compile(
    r"\b("
    r"cannot|can't|can’t|unable|unsupported|not\s+supported|outside|not\s+available|"
    r"should\s+not|must\s+not|do\s+not|don't|won't|invalid|not\s+(?:a\s+)?valid|not\s+enough|"
    r"cannot\s+reliably|can't\s+reliably|can’t\s+reliably"
    r")\b",
    re.IGNORECASE,
)
_FENCED_BLOCK_RE = re.compile(r"```(?P<lang>[A-Za-z0-9_+-]*)\s*\n(?P<body>.*?)```", re.DOTALL)
_CUSTOM_RECIPE_METADATA_BLOCK_RE = re.compile(
    r'"(?:module_name|display_name|description)"|\bmetadata\.json\b',
    re.IGNORECASE,
)
_CUSTOM_RECIPE_PYTHON_BLOCK_RE = re.compile(
    r"\bDataService\.queue_table\b|\bclass\s+\w+.*\b(?:Recipe|Mapper)\b|"
    r"\brecipe\.Recipe\b|\bdef\s+(?:run|mapper|map)\b|\badd_recipe_argument\b",
    re.IGNORECASE | re.DOTALL,
)


def _matched_signal_names(text: str) -> frozenset[str]:
    return frozenset(signal.name for signal in TEXT_SIGNALS if signal.matches(text))


def signal_matches(name: str, text: str) -> bool:
    signal = _SIGNALS[name]
    return signal.matches(text)


def plan_capabilities(
    question: str,
    *,
    report_loaded: bool,
    report_count: int | None = None,
    report_table_names: Iterable[str] | None = None,
) -> CapabilityPlan:
    """Plan capability boundaries and evidence expectations for a turn."""

    ctx = BoundaryContext(
        question=question or "",
        report_loaded=report_loaded,
        report_count=report_count,
        report_table_names=tuple(str(name) for name in report_table_names) if report_table_names is not None else None,
    )
    signals = _matched_signal_names(ctx.question)
    boundary_codes = tuple(
        spec.code
        for spec in BOUNDARY_SPECS
        if spec.preflight and spec.matches(ctx, signals)
    )
    return CapabilityPlan(
        boundary_codes=tuple(dict.fromkeys(boundary_codes)),
        evidence_requirements=_evidence_requirements(signals, report_loaded=report_loaded),
        matched_signals=tuple(sorted(signals)),
    )


def _evidence_requirements(signals: frozenset[str], *, report_loaded: bool) -> tuple[EvidenceRequirement, ...]:
    requirements: list[EvidenceRequirement] = []
    if report_loaded and signals & _REPORT_EVIDENCE_SIGNALS:
        requirements.append(
            EvidenceRequirement(
                kind="report_evidence",
                reason="Report-specific answers require deterministic report facts, bounded SQL, recipe output, or report-doctor evidence.",
            )
        )
    if signals & _RECIPE_REFERENCE_SIGNALS:
        requirements.append(
            EvidenceRequirement(
                kind="recipe_framework_reference",
                reason="Custom recipe guidance should be grounded in installed recipe docs or curated recipe-framework references.",
            )
        )
    if signals & _HANDOFF_GUIDANCE_SIGNALS:
        requirements.append(
            EvidenceRequirement(
                kind="handoff_guidance",
                reason="Nsight Compute is a handoff target; the skill does not execute it or define its metrics.",
            )
        )
    if report_loaded and signals & _RECIPE_DOMAIN_ANALYSIS_SIGNALS:
        requirements.append(
            EvidenceRequirement(
                kind="recipe_or_domain_workflow",
                reason=(
                    "Recipe/domain-owned performance semantics require recipe execution "
                    "or an explicit unsupported boundary; raw report SQL is only supporting evidence."
                ),
            )
        )
    return tuple(requirements)


def boundary_for_code(code: str) -> CapabilityBoundary | None:
    return _BOUNDARIES.get(code)


def boundary_answer(codes: Iterable[str]) -> str:
    for code in codes:
        boundary = boundary_for_code(code)
        if boundary is not None:
            return boundary.answer
    return ""


def custom_recipe_assist_request(text: str) -> bool:
    return signal_matches("custom_recipe_assist", text)


def preflight_boundary_codes(
    question: str,
    *,
    report_loaded: bool,
    report_count: int | None = None,
    report_table_names: Iterable[str] | None = None,
) -> tuple[str, ...]:
    return plan_capabilities(
        question,
        report_loaded=report_loaded,
        report_count=report_count,
        report_table_names=report_table_names,
    ).boundary_codes


def response_boundary_codes(
    question: str,
    answer: str,
    *,
    report_loaded: bool,
    report_count: int | None = None,
    report_table_names: Iterable[str] | None = None,
) -> tuple[str, ...]:
    if not answer.strip():
        return ()
    codes = list(
        preflight_boundary_codes(
            question,
            report_loaded=report_loaded,
            report_count=report_count,
            report_table_names=report_table_names,
        )
    )
    if custom_recipe_assist_request(question) and overproduces_custom_recipe(answer):
        codes.append("custom_recipe_full_generation")
    if invalid_cli_help_command(answer) and not acknowledges_invalid_help(answer):
        codes.append("invalid_cli_help_command")
    return tuple(code for code in dict.fromkeys(codes) if not acknowledges_boundary(answer, code))


def issue_message(code: str) -> str:
    boundary = boundary_for_code(code)
    return boundary.message if boundary is not None else code


def asks_custom_recipe_full_implementation(text: str) -> bool:
    return signal_matches("custom_recipe_full_generation", text)


def overproduces_custom_recipe(answer: str) -> bool:
    """Return True when an answer crosses from guidance into code-package generation.

    Conceptual help may include a directory sketch, a command, or a focused
    snippet.  The unsupported shape is a complete package: metadata plus Python
    implementation presented as multiple recipe files.
    """

    if not answer:
        return False
    has_metadata_block = False
    has_python_impl_block = False
    for match in _FENCED_BLOCK_RE.finditer(answer):
        lang = (match.group("lang") or "").lower()
        body = match.group("body") or ""
        if (lang == "json" or "metadata.json" in body.lower()) and _CUSTOM_RECIPE_METADATA_BLOCK_RE.search(
            body
        ):
            has_metadata_block = True
        if (
            lang in {"python", "py"} or re.search(r"\b(class|def|DataService)\b", body)
        ) and _CUSTOM_RECIPE_PYTHON_BLOCK_RE.search(body):
            has_python_impl_block = True
    file_sections = len(CUSTOM_RECIPE_FILE_SECTION_RE.findall(answer))
    return has_metadata_block and has_python_impl_block and file_sections >= 2


def asks_recipe_domain_semantic_analysis(text: str) -> bool:
    return signal_matches("recipe_domain_semantic_analysis", text)


def asks_open_ended_root_cause(text: str) -> bool:
    return signal_matches("root_cause_request", text)


def invalid_cli_help_command(text: str) -> bool:
    return signal_matches("invalid_cli_help_command", text)


def asks_ncu_execution(text: str) -> bool:
    return signal_matches("ncu_execution", text)


def asks_ncu_metric_semantics(text: str) -> bool:
    return signal_matches("ncu_metric_semantics", text)


def boundary_rule_codes() -> tuple[str, ...]:
    """Return configured preflight boundary codes for tests/release review."""

    return tuple(spec.code for spec in BOUNDARY_SPECS if spec.preflight)


def evidence_signal_names() -> frozenset[str]:
    """Return non-boundary signals that still drive evidence policy."""

    return (
        _REPORT_EVIDENCE_SIGNALS
        | _RECIPE_REFERENCE_SIGNALS
        | _HANDOFF_GUIDANCE_SIGNALS
        | _RECIPE_DOMAIN_ANALYSIS_SIGNALS
    )


def capability_specs() -> tuple[CapabilityBoundarySpec, ...]:
    """Return the reviewed capability contract for release/test inspection."""

    return BOUNDARY_SPECS


def acknowledges_invalid_help(answer: str) -> bool:
    return acknowledges_boundary(answer, "invalid_cli_help_command")


def acknowledges_boundary(answer: str, code: str) -> bool:
    """Return whether prose acknowledges a product boundary.

    This deliberately avoids per-boundary phrase tables.  A valid
    acknowledgement should contain a generic unsupported/unsafe/invalid
    boundary cue plus vocabulary from the reviewed boundary message/answer.
    This keeps response validation from becoming a hidden list of exact
    eval-answer substrings.
    """

    spec = _SPECS_BY_CODE.get(code)
    boundary = boundary_for_code(code)
    if spec is None or boundary is None:
        return False
    lower = (answer or "").lower()
    if not _BOUNDARY_ACKNOWLEDGEMENT_RE.search(lower):
        return False
    keywords = _boundary_keywords(spec)
    if not keywords:
        return True
    matches = sum(1 for keyword in keywords if keyword in lower)
    return matches >= min(2, len(keywords))


def _boundary_keywords(spec: CapabilityBoundarySpec) -> tuple[str, ...]:
    boundary = spec.boundary()
    text = " ".join((spec.code.replace("_", " "), spec.category, boundary.message, boundary.answer))
    tokens = {
        token
        for token in re.findall(r"[a-z][a-z0-9+-]{3,}", text.lower())
        if token not in BOUNDARY_KEYWORD_STOPWORDS
    }
    return tuple(sorted(tokens))


def overstates_root_cause(question: str, answer: str) -> bool:
    """Return True when a root-cause answer is too definitive for one report."""

    if not asks_open_ended_root_cause(question):
        return False
    lower = answer.lower()
    definitive = any(phrase in lower for phrase in ROOT_CAUSE_DEFINITIVE_PHRASES)
    cautious = any(phrase in lower for phrase in ROOT_CAUSE_CAUTION_PHRASES)
    ncu_metric_request = signal_matches("ncu_metric_semantics", question)
    numeric_ncu_claim = NCU_NUMERIC_METRIC_CLAIM_RE.search(lower)
    definitive_ncu_root_cause = ncu_metric_request and any(
        phrase in lower for phrase in NCU_DEFINITIVE_ROOT_CAUSE_PHRASES
    ) and any(term in lower for term in NCU_ROOT_CAUSE_TERMS)
    if ncu_metric_request and (numeric_ncu_claim or definitive_ncu_root_cause):
        return True
    return definitive and not cautious
