"""Declarative recipe/domain-owned performance semantic metadata.

These concepts are product-boundary metadata, not eval examples.  They describe
high-level analysis outputs whose validated meaning is owned by recipes or
domain workflows rather than ad-hoc raw report SQL.  Keep the concept list
small and reviewed; derive regex fragments and answer/evidence markers from
this table instead of copying phrase lists across guardrails and report tools.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecipeDomainSemantic:
    name: str
    question_patterns: tuple[str, ...]
    answer_markers: tuple[str, ...]
    sql_alias_patterns: tuple[str, ...]
    evidence_markers: tuple[str, ...] = ()
    high_confidence_answer_marker: bool = True


COMMUNICATION_OVERLAP_EVIDENCE_MARKERS = (
    "nccl_gpu_overlap_trace",
    "nccl_gpu_time_util_map",
    "mpi_gpu_time_util_map",
    "communication/compute overlap",
    "communication compute overlap",
    "communication-compute overlap",
    "exposed communication",
)


RECIPE_DOMAIN_SEMANTICS: tuple[RecipeDomainSemantic, ...] = (
    RecipeDomainSemantic(
        name="exposed_communication",
        question_patterns=(r"exposed\s+communication(?:\s+(?:cost|time))?",),
        answer_markers=("exposed communication",),
        sql_alias_patterns=(r"exposed[_\s-]*(?:comm|communication)(?:[_\s-]*(?:cost|time))?",),
        evidence_markers=COMMUNICATION_OVERLAP_EVIDENCE_MARKERS,
    ),
    RecipeDomainSemantic(
        name="communication_compute_overlap",
        question_patterns=(
            r"communication\s*/\s*compute\s+overlap",
            r"communication[-\s]+compute\s+overlap",
            r"compute\s*/\s*communication\s+overlap",
            r"mpi\s*/\s*gpu\s+overlap",
            r"comm(?:unication)?\s*/\s*compute\s+overlap",
        ),
        answer_markers=(
            "communication/compute overlap",
            "communication compute overlap",
            "communication-compute overlap",
            "compute/communication overlap",
            "mpi/gpu overlap",
            "comm/compute overlap",
        ),
        sql_alias_patterns=(
            r"(?:comm|communication)[_\s/-]*compute[_\s-]*overlap",
            r"compute[_\s/-]*(?:comm|communication)[_\s-]*overlap",
            r"mpi[_\s/-]*gpu[_\s-]*overlap",
        ),
        evidence_markers=COMMUNICATION_OVERLAP_EVIDENCE_MARKERS,
    ),
    RecipeDomainSemantic(
        name="straggler",
        question_patterns=(r"straggler\s+(?:detection|attribution|analysis)",),
        answer_markers=("straggler",),
        sql_alias_patterns=(r"straggler[_\s-]*(?:detection|attribution|analysis)",),
        evidence_markers=("straggler", "rank_stats", "rank_stats_by_device"),
    ),
    RecipeDomainSemantic(
        name="layer_attribution",
        question_patterns=(r"layer[-\s]+level\s+attribution",),
        answer_markers=("layer-level attribution", "layer level attribution"),
        sql_alias_patterns=(),
    ),
    RecipeDomainSemantic(
        name="per_iteration_jitter",
        question_patterns=(r"per[-\s]+iteration\s+jitter",),
        answer_markers=("per-iteration jitter", "per iteration jitter"),
        sql_alias_patterns=(),
        evidence_markers=("jitter",),
    ),
    RecipeDomainSemantic(
        name="utilization_map",
        question_patterns=(r"utili[sz]ation\s+(?:map|heatmap)",),
        answer_markers=("utilization map", "utilization heatmap", "time utilization"),
        sql_alias_patterns=(r"utili[sz]ation[_\s-]*(?:map|heatmap)",),
        evidence_markers=(
            "cuda_gpu_time_util_map",
            "nccl_gpu_time_util_map",
            "gpu_metric_util_map",
            "utilization map",
            "utilization heatmap",
            "time utilization",
        ),
    ),
    RecipeDomainSemantic(
        name="kernel_pacing",
        question_patterns=(r"kernel\s+(?:pace|pacing)",),
        answer_markers=("kernel pace", "kernel pacing"),
        sql_alias_patterns=(r"kernel[_\s-]*pacing?",),
        evidence_markers=("cuda_gpu_kern_pace", "kernel pace", "kernel pacing", "jitter"),
    ),
)
GENERIC_LOW_CONFIDENCE_ANSWER_MARKERS = ("overlap",)


def recipe_domain_question_terms_re() -> str:
    return "(?:" + "|".join(
        pattern
        for semantic in RECIPE_DOMAIN_SEMANTICS
        for pattern in semantic.question_patterns
    ) + ")"


def recipe_domain_sql_alias_terms_re() -> str:
    return "(?:" + "|".join(
        pattern
        for semantic in RECIPE_DOMAIN_SEMANTICS
        for pattern in semantic.sql_alias_patterns
    ) + ")"


def recipe_domain_answer_markers(*, high_confidence_only: bool = False) -> tuple[str, ...]:
    markers = [
        marker
        for semantic in RECIPE_DOMAIN_SEMANTICS
        if semantic.high_confidence_answer_marker
        for marker in semantic.answer_markers
    ]
    if not high_confidence_only:
        markers.extend(GENERIC_LOW_CONFIDENCE_ANSWER_MARKERS)
    return tuple(dict.fromkeys(markers))


def recipe_domain_evidence_markers(semantic_text: str, markers: tuple[str, ...]) -> tuple[str, ...]:
    generic_markers = set(GENERIC_LOW_CONFIDENCE_ANSWER_MARKERS)
    evidence_markers = {marker for marker in markers if marker not in generic_markers}
    for semantic in RECIPE_DOMAIN_SEMANTICS:
        if any(marker in semantic_text for marker in semantic.answer_markers):
            evidence_markers.update(semantic.evidence_markers)
    if (
        bool(generic_markers & set(markers))
        and any(
            token in semantic_text
            for token in ("communication", "comm/", "mpi/gpu", "exposed communication")
        )
    ):
        evidence_markers.update(COMMUNICATION_OVERLAP_EVIDENCE_MARKERS)
    return tuple(sorted(evidence_markers))
