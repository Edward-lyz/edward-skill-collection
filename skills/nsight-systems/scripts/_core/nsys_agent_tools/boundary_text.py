"""Shared text for cross-layer Nsight Systems product boundaries.

Lower-level report tooling cannot import the capability planner, but it
still needs to return the same user-facing boundary text. Keep reusable wording
and broad signal regex fragments here; higher layers decide how to route,
recover, or score those boundaries.
"""

from __future__ import annotations

from .domain_semantics import recipe_domain_question_terms_re

LOCAL_PATH_LEAK_MESSAGE = "Internal cache paths must not be exposed in final answers."
LOCAL_PATH_LEAK_ANSWER = (
    "I can't expose local cache paths or recipe-output root directories. "
    "I can refer to the loaded report label, recipe output handle/label, result file names, schemas, and bounded previews instead."
)

DERIVED_ANALYSIS_VERBS_RE = r"(?:compute|calculate|measure|quantify|report|determine|find|analy[sz]e)"
RECIPE_DOMAIN_SEMANTIC_TERMS_RE = recipe_domain_question_terms_re()
RECIPE_DOMAIN_SEMANTICS_MESSAGE = (
    "Recipe/domain-owned performance semantics should not be reported as "
    "validated results from ad-hoc raw report SQL."
)
RECIPE_DOMAIN_SEMANTICS_ANSWER = (
    "I cannot report exposed communication cost, communication/compute overlap, "
    "straggler attribution, utilization maps, pacing, or similar recipe/domain "
    "semantics as validated results from an ad-hoc DuckDB/raw-table query. "
    "Those metrics require an installed recipe or domain workflow that owns the "
    "interval-union and attribution semantics. I can run an available recipe, or "
    "I can provide clearly labeled supporting facts such as top kernels, NCCL-looking "
    "activity, CUDA API timing, and active GPUs."
)

COMPETITOR_PROFILER_RE = (
    r"(?:"
    r"vtune|intel\s+vtune|intel\s+profiler|"
    r"amd\s+uprof|rocprof(?:iler)?|omniperf|"
    # Require a profiler phrase for TAU so math/profiling questions about
    # lowercase tau values do not trip the product-boundary gate.
    r"tau\s+(?:profiler|performance\s+system)|"
    r"competitor\s+profiler|competing\s+profiler"
    r")"
)
COMPARISON_REQUEST_RE = (
    r"(?:vs|versus|better|worse|faster|slower|compare|compared|comparison|"
    r"diff(?:erence|erent)?)"
)
NVIDIA_PROFILER_REFERENCE_RE = r"(?:visual\s+profiler|nvvp|nsight\s+compute|ncu)"
# The bounded proximity window is intentional: it catches direct profiler
# comparison requests without letting distant, unrelated mentions bridge across
# a long prompt.
COMPETITOR_COMPARISON_RE = (
    rf"\b{COMPARISON_REQUEST_RE}\b.{{0,100}}\b{COMPETITOR_PROFILER_RE}\b|"
    rf"\b{COMPETITOR_PROFILER_RE}\b.{{0,100}}\b{COMPARISON_REQUEST_RE}\b"
)
