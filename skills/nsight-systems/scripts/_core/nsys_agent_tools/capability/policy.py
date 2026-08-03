"""Reviewed unsupported-capability policy for Nsight Systems AI capabilities.

The regexes in this file are product-boundary signals, not answer routes. Keep
this module declarative: add broad reviewed request shapes here, and keep the
planning/execution logic in ``capability.boundaries`` and ``capability.contract``.
"""

from __future__ import annotations

import re

from ..boundary_text import (
    COMPETITOR_COMPARISON_RE,
    DERIVED_ANALYSIS_VERBS_RE,
    LOCAL_PATH_LEAK_ANSWER,
    LOCAL_PATH_LEAK_MESSAGE,
    RECIPE_DOMAIN_SEMANTIC_TERMS_RE,
    RECIPE_DOMAIN_SEMANTICS_ANSWER,
    RECIPE_DOMAIN_SEMANTICS_MESSAGE,
)
from .contract import BoundaryGate, CapabilityBoundarySpec, TextSignal


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


BOUNDARY_KEYWORD_STOPWORDS = frozenset(
    {
        "about",
        "allowed",
        "answer",
        "available",
        "beta",
        "can",
        "cannot",
        "could",
        "current",
        "evidence",
        "from",
        "help",
        "instead",
        "need",
        "not",
        "only",
        "report",
        "reports",
        "request",
        "runtime",
        "scope",
        "should",
        "skill",
        "supported",
        "systems",
        "that",
        "this",
        "tool",
        "tools",
        "user",
        "with",
        "without",
        "would",
    }
)
CUSTOM_RECIPE_FILE_SECTION_RE = _rx(
    r"(?m)^\s*(?:#+\s*)?(?:file|path|filename)\s*[:：]\s*\S+"
    r"|^\s*(?:#+\s*)?\S+\.(?:py|json|yaml|yml)\s*$"
)
ROOT_CAUSE_DEFINITIVE_PHRASES = (
    "root cause is",
    "the cause is",
    "this is caused by",
    "primary factor",
    "smoking gun",
    "confirms",
    "proves",
    "dominated by",
    "therefore stalls",
    "you should change",
    "the fix is",
    "optimal block size is",
)
ROOT_CAUSE_CAUTION_PHRASES = (
    "likely",
    "suggests",
    "consistent with",
    "hypothesis",
    "unverified",
    "not proven",
    "cannot prove",
    "can't prove",
    "requires nsight compute",
    "requires separate nsight compute",
    "needs nsight compute",
)
NCU_NUMERIC_METRIC_CLAIM_RE = _rx(
    r"\b\d+(?:\.\d+)?\s*%?\s*(?:occupancy|sm\s+utili[sz]ation|warp\s+occupancy)\b|"
    r"\b(?:occupancy|sm\s+utili[sz]ation|warp\s+occupancy)\b.{0,40}\b\d+(?:\.\d+)?\s*%"
)
NCU_DEFINITIVE_ROOT_CAUSE_PHRASES = (
    "dominant factor",
    "root-cause breakdown",
    "root cause",
    "memory stalls are",
    "register spill",
    "stall cycles",
)
NCU_ROOT_CAUSE_TERMS = ("occupancy", "stall", "register", "roofline")


_GENERAL_ASSISTANT_OFF_TOPIC = (
    r"\b(weather|news|stock price|nvidia(?:'s)? stock|stock market|earnings call|"
    r"investment advice|financial advice|politics|election|presidential election|"
    r"joke|riddle|poem|novelty translation|role[- ]?play|rewrite this in the style|"
    r"personal advice|dating advice)\b"
)
_CONFIDENTIAL_OR_LICENSE_ABUSE = (
    r"\b(unannounced|confidential|internal data|internal information)\b|"
    r"\b(bypass|disable|crack)\b.{0,60}\b(license|licence|security|check)\b"
)
_UNRELATED_APP_BUILDING = (
    r"\bcors\b|\breact\s+(?:application|app|frontend|component)\b|"
    r"\b(build|write|create)\b.{0,80}\b(web app|dashboard app|react app|frontend|backend api)\b"
)
_NON_NSYS_PROFILING_SCOPE = (
    r"\b(opencl|intel integrated graphics|amd mi300|radeon|omniperf)\b"
)
_DESTRUCTIVE_LOCAL_ACTION = (
    r"\b(rm\s+-rf|mkfs|dd\s+if=|delete\s+my\s+home|format\s+the\s+disk)\b|"
    r"\b(delete|remove|clear|clean|purge)\b.{0,80}"
    r"\b(report\s+cache|cache\s+directory|recipe\s+output|output\s+directory|"
    r"workspace|local\s+files?)\b"
)
_SOURCE_CODE_EDITING_REQUEST = (
    r"\b(edit|patch|modify|update|rewrite|change)\b.{0,80}"
    r"\b(source\s+code|source\s+files?|codebase|application\s+code|files?)\b"
    r".{0,80}\b(nvtx|instrument|ranges?)\b|"
    r"\b(add|insert)\b.{0,40}\bnvtx\b.{0,80}"
    r"\b(?:to|into)\b.{0,40}"
    r"\b(source\s+code|source\s+files?|codebase|application\s+code|files?)\b"
)
_OFF_TOPIC_REQUEST = "|".join(
    (
        _GENERAL_ASSISTANT_OFF_TOPIC,
        _CONFIDENTIAL_OR_LICENSE_ABUSE,
        _UNRELATED_APP_BUILDING,
        _NON_NSYS_PROFILING_SCOPE,
    )
)

TEXT_SIGNALS: tuple[TextSignal, ...] = (
    TextSignal(
        name="profiling_context",
        pattern=_rx(r"\b(nsight|nsys|profil|timeline|report|optimi[sz]e|analy[sz]e)\b"),
        rationale="Pure code-generation requests become in-scope only when tied to profiling evidence.",
    ),
    TextSignal(
        name="custom_recipe_assist",
        pattern=_rx(
            r"\b(custom|user[- ]defined)\b(?:\s+[a-z][a-z0-9_-]*){0,4}\s+recipe\b|"
            r"\b(dataservice|queue_table|metadata\.json|nsys_recipe_path|"
            r"recipe\s+development|recipe\s+authoring|recipe\s+mapper)\b"
        ),
        rationale="Custom recipe concept/review assistance is supported; full implementation is not.",
    ),
    TextSignal(
        name="custom_recipe_guidance_request",
        pattern=_rx(r"\b(explain|how\s+(?:do|can)\s+i|how\s+to|review|debug|fix|concepts?)\b"),
        rationale="Conceptual or review-oriented custom recipe help is allowed.",
    ),
    TextSignal(
        name="custom_recipe_full_generation",
        pattern=_rx(
            r"\b(write|generate|build|implement|give\s+me)\b.{0,100}"
            r"\b(custom|user[- ]defined)\b(?:\s+[a-z][a-z0-9_-]*){0,4}\s+recipe\b|"
            r"\b(custom|user[- ]defined)\b(?:\s+[a-z][a-z0-9_-]*){0,4}\s+recipe\b.{0,100}"
            r"\b(write|generate|build|implement|give\s+me|source\s+code)\b|"
            r"\b(write|generate|create|build|implement|give\s+me|make)\b.{0,100}"
            r"\b(full|complete|entire|ready[- ]to[- ]run|from\s+scratch|all\s+files?)\b"
            r".{0,100}\b(recipe|mapper|metadata\.json|files?)\b"
            r"|\b(custom|user[- ]defined)\b(?:\s+[a-z][a-z0-9_-]*){0,4}\s+recipe\b.{0,100}"
            r"\b(full|complete|entire|ready[- ]to[- ]run|all\s+files?|source\s+code)\b"
        ),
        rationale="Generating a complete recipe package would be unsupported authoring, not guidance.",
    ),
    TextSignal(
        name="destructive_local_action",
        pattern=_rx(_DESTRUCTIVE_LOCAL_ACTION),
        rationale="Deleting local files, caches, or workspaces is outside the report-evidence tool boundary.",
    ),
    TextSignal(
        name="source_code_editing_request",
        pattern=_rx(_SOURCE_CODE_EDITING_REQUEST),
        rationale="Source patching belongs to a code-editing workflow, not Nsight Systems report analysis.",
    ),
    TextSignal(
        name="off_topic",
        pattern=_rx(_OFF_TOPIC_REQUEST),
        rationale=(
            "General assistant, confidential-data, unrelated app-building, and "
            "non-Nsys profiling requests are out of scope."
        ),
    ),
    TextSignal(
        name="competitor_tool_comparison",
        pattern=_rx(COMPETITOR_COMPARISON_RE),
        rationale="Competitor-profiler comparisons are outside the Nsight Systems product-skill scope.",
    ),
    TextSignal(
        name="cross_report_comparison",
        pattern=_rx(
            r"\b(compare|diff(?:er)?|different|across|between|per)\b"
            r".{0,80}\b(ranks?|reports?|runs?|sources?)\b|"
            r"\b(which|what|slowest|fastest|higher|lower)\b"
            r".{0,80}\b(ranks?|reports|runs|sources)\b|"
            r"\b(ranks?|reports|runs|sources)\b.{0,80}"
            r"\b(slowest|fastest|higher|lower|compare|diff(?:er)?|different)\b"
        ),
        rationale="Cross-report/rank/run comparison requires multiple report sources.",
    ),
    TextSignal(
        name="report_file_compatibility",
        pattern=_rx(r"\b(open|load|read|view|compatible|compatibility|newer|older)\b.{0,80}\b(report|\.nsys-rep)\b"),
        rationale="Compatibility questions mention reports but are not cross-report comparisons.",
    ),
    TextSignal(
        name="sampled_metric_region_ranking",
        pattern=_rx(
            r"\b(sm\s+active|gpu\s+metric|gpu_metrics|metric\s+sample|sampled\s+metric|"
            r"utilization|occupancy)\b.{0,100}\b(nvtx|range|kernel|cuda\s+api|per[- ]event|per[- ]range|top|rank)\b|"
            r"\b(nvtx|range|kernel|cuda\s+api|per[- ]event|per[- ]range|top|rank)\b.{0,100}"
            r"\b(sm\s+active|gpu\s+metric|gpu_metrics|metric\s+sample|sampled\s+metric|utilization|occupancy)\b"
        ),
        rationale="Sampled metrics need time-weighted coverage, not naive event/range ranking.",
    ),
    TextSignal(
        name="kernel_metric_overlap",
        pattern=_rx(
            r"\b(overlap|correlat(?:e|ion)|relationship|compare)\b.{0,100}"
            r"\b(kernels?|kernel\s+intervals?|cuda\s+kernels?)\b.{0,100}"
            r"\b(gpu\s+metrics?|gpu_metrics|sm\s+active|sampled\s+metrics?)\b|"
            r"\b(gpu\s+metrics?|gpu_metrics|sm\s+active|sampled\s+metrics?)\b.{0,100}"
            r"\b(overlap|correlat(?:e|ion)|relationship|compare)\b.{0,100}"
            r"\b(kernels?|kernel\s+intervals?|cuda\s+kernels?)\b"
        ),
        rationale="Exact overlap between sampled metrics and interval events needs a validated workflow.",
    ),
    TextSignal(
        name="recipe_domain_semantic_analysis",
        pattern=_rx(
            rf"\b{DERIVED_ANALYSIS_VERBS_RE}\b.{{0,140}}\b{RECIPE_DOMAIN_SEMANTIC_TERMS_RE}\b|"
            rf"\b{RECIPE_DOMAIN_SEMANTIC_TERMS_RE}\b.{{0,140}}"
            r"\b(?:with|using|from|via|over|query|duckdb|sql|raw\s+tables?|report\s+tables?)\b"
        ),
        rationale="Recipe/domain performance semantics need recipe-owned interval attribution, not ad-hoc raw report SQL.",
    ),
    TextSignal(
        name="workload_fingerprinting",
        pattern=_rx(
            r"\b(what|which)\b.{0,40}\b((?:ml|ai|neural|language|workload)\s+model|workload|algorithm|application)\b"
            r".{0,80}\b(this|the)\b.{0,30}\b(report|profile|run)\b|"
            r"\b(is\s+this|classify|fingerprint)\b.{0,80}"
            r"\b((?:ml|ai|neural|language|workload)\s+model|workload|algorithm|training|inference|collective\s+pattern)\b|"
            r"\bidentify\b.{0,80}\b((?:ml|ai|neural|language|workload)\s+model|workload|algorithm)\b"
        ),
        rationale="Report event signatures do not reliably identify workload/model/algorithm identity.",
    ),
    TextSignal(
        name="application_metric",
        pattern=_rx(
            r"\b(training|validation|eval(?:uation)?|test)\s+"
            r"(accuracy|loss|perplexity|auc|f1|precision|recall)\b|"
            r"\b(accuracy|loss|perplexity|auc|f1|precision|recall)\b.{0,80}\b(profile|report|run)\b"
        ),
        rationale="Model-quality metrics require explicit app annotations/logs, not implicit profiler data.",
    ),
    TextSignal(
        name="interactive_visualization",
        pattern=_rx(
            r"\b(render|draw|show|create|display)\b.{0,80}"
            r"\b(interactive|clickable|zoomable)\b.{0,80}\b(heatmap|chart|plot|visualization|graph)\b|"
            r"\b(interactive|clickable|zoomable)\b.{0,80}"
            r"\b(heatmap|chart|plot|visualization|graph)\b"
        ),
        rationale="The skill returns evidence but does not render interactive UI artifacts.",
    ),
    TextSignal(
        name="pure_cuda_code_generation",
        pattern=_rx(
            r"\b(write|generate|create|implement(?:s|ed|ing)?|give\s+me)\b.{0,80}\b(cuda\s+kernel|__global__)\b|"
            r"\b(write|generate|create|implement(?:s|ed|ing)?|give\s+me)\b.{0,80}\bcuda\b.{0,40}\bkernel\b|"
            r"\b(cuda\s+kernel|__global__)\b.{0,80}\b(write|generate|create|implement(?:s|ed|ing)?)\b|"
            r"\bcuda\b.{0,40}\bkernel\b.{0,80}\b(write|generate|create|implement(?:s|ed|ing)?)\b"
        ),
        rationale="Kernel implementation belongs to CUDA coding assistance, not Nsight Systems profiling.",
    ),
    TextSignal(
        name="multi_hop_correlation",
        pattern=_rx(
            r"\b(python\s+function|call\s*stack|cpu\s+function|source\s+line)\b.{0,120}"
            r"\b(cuda\s+api|kernel)\b.{0,120}\b(kernel|cuda\s+api)\b|"
            r"\b(which|what)\b.{0,80}\b(function|call\s*stack)\b.{0,80}\b(launched|called)\b.{0,80}\b(kernel)\b"
        ),
        rationale="Function/API/kernel chains need explicit correlation keys.",
    ),
    TextSignal(
        name="root_cause_request",
        pattern=_rx(
            r"\b(why|root\s+cause|cause|what\s+should\s+i\s+change|how\s+do\s+i\s+make.*faster|"
            r"optimal\s+(block|grid)|best\s+(block|grid)|tune\s+this)\b"
        ),
        rationale="Open-ended root-cause requests should not be answered as proof from one report.",
    ),
    TextSignal(
        name="os_runtime_request",
        pattern=_rx(r"\b(osrt|os\s*/\s*runtime|os runtime|operating system runtime|syscalls?|system calls?)\b"),
        rationale="OS runtime analysis requires OSRT tables.",
    ),
    TextSignal(
        name="invalid_cli_help_command",
        pattern=_rx(r"\bnsys\s+--help\s+--[a-z0-9][a-z0-9-]*\b"),
        rationale="`nsys --help --flag` is not a valid CLI help shape.",
    ),
    TextSignal(
        name="ncu_execution",
        pattern=_rx(
            r"\b(run|launch|execute|profile|collect)\b.{0,80}\b(ncu|nsight\s+compute)\b|"
            r"\b(ncu|nsight\s+compute)\b.{0,80}\b(run|launch|execute|profile|collect)\b"
        ),
        rationale="The skill can hand off to Nsight Compute but does not execute it.",
    ),
    TextSignal(
        name="application_profile_execution",
        pattern=_rx(
            r"^(?!.*\bhow\b).*\b(profile|run|launch|execute|collect)\b"
            r".{0,100}\b(for\s+me|then\s+analy[sz]e|and\s+analy[sz]e|"
            r"\./|\.py\b|\.sh\b)"
        ),
        rationale="The skill can give capture commands but should not launch arbitrary user workloads.",
    ),
    TextSignal(
        name="ncu_metric_semantics",
        pattern=_rx(
            r"\b(?:exact|per[- ]kernel|kernel[- ]level|tell\s+me|provide|compute|report)\b"
            r".{0,80}\b(?:sm\s+)?occupancy\b|"
            r"\b(?:sm\s+)?occupancy\b.{0,80}\b(?:kernel|nsight\s+systems|nsys)\b|"
            r"\bexact\b.{0,80}\bsm\s+utili[sz]ation\b|"
            r"\b(speed\s+of\s+light|roofline|sass|source\s+counters?|counter\s+metrics?|"
            r"warp\s+sampling|pm\s+sampling|replay\s+modes?|register\s+pressure|"
            r"stall\s+reasons?|occupancy|achieved\s+occupancy)\b.{0,100}"
            r"\b(ncu|nsight\s+compute|metric|counter|meaning|definition|value)\b|"
            r"\b(ncu|nsight\s+compute)\b.{0,100}"
            r"\b(speed\s+of\s+light|roofline|sass|source\s+counters?|counter\s+metrics?|"
            r"warp\s+sampling|pm\s+sampling|replay\s+modes?|register\s+pressure|"
            r"stall\s+reasons?|occupancy|achieved\s+occupancy)\b|"
            r"\b(why|root\s+cause|cause|slow|slowness|bottleneck)\b.{0,100}"
            r"\b(memory\s+stalls?|stall\s+reasons?|occupancy|achieved\s+occupancy|register\s+pressure)\b|"
            r"\b(memory\s+stalls?|stall\s+reasons?|occupancy|achieved\s+occupancy|register\s+pressure)\b.{0,100}"
            r"\b(why|root\s+cause|cause|slow|slowness|bottleneck)\b|"
            r"\b(?:gpc|sm|lts|dram|gpu|smsp)__[a-z0-9_%.]+"
        ),
        rationale="Detailed Nsight Compute metric definitions/values require Nsight Compute evidence, not Nsight Systems report evidence.",
    ),
)


BOUNDARY_SPECS: tuple[CapabilityBoundarySpec, ...] = (
    CapabilityBoundarySpec(
        code="custom_recipe_full_generation",
        category="unsupported_authoring",
        status="future_feature",
        rationale="Generating a complete custom recipe is unsupported. Helping design or review one is still allowed.",
        required_signals=("custom_recipe_full_generation",),
        excluded_signals=("custom_recipe_guidance_request",),
        message=(
            "Custom recipe assistance is allowed, but generating a complete ready-to-run "
            "custom recipe for the user is outside the supported scope of this skill."
        ),
        answer=(
            "I can help you design, understand, or review a custom Nsight Systems recipe, "
            "but I should not generate a complete ready-to-run custom recipe implementation for you. "
            "Share your existing recipe code, metadata, or error, and I can review it; or I can explain the relevant concepts and point to the official recipe-authoring docs."
        ),
        allowed_examples=("Explain what DataService.queue_table does in a custom recipe.",),
        blocked_examples=("Generate a complete ready-to-run custom recipe with metadata.json and Python files.",),
    ),
    CapabilityBoundarySpec(
        code="destructive_local_action_unsupported",
        category="scope",
        status="unsupported",
        rationale="Report-analysis tools must not become local filesystem cleanup or destructive shell tools.",
        required_signals=("destructive_local_action",),
        message="Destructive local filesystem actions are outside the Nsight Systems skill scope.",
        answer=(
            "I cannot delete local files, clear caches, remove recipe outputs, or run destructive shell commands from this Nsight Systems skill. "
            "I can continue with read-only report analysis, explain what generated artifacts mean, or suggest safe cleanup steps for you to review and run yourself."
        ),
        allowed_examples=("Explain what the report cache is used for.",),
        blocked_examples=("Run rm -rf on the report cache and then analyze the report.",),
    ),
    CapabilityBoundarySpec(
        code="source_code_editing_unsupported",
        category="scope",
        status="unsupported_in_byo_skill",
        rationale="The Nsight Systems skill can guide instrumentation but should not patch application source files.",
        required_signals=("source_code_editing_request",),
        message="Source-code editing is outside the Nsight Systems skill action surface.",
        answer=(
            "I cannot edit, patch, or create application source files from this Nsight Systems skill. "
            "I can suggest where NVTX annotations would help and show a small illustrative pattern, but source edits should happen in a separate code-editing workflow with the user's source tree and permissions."
        ),
        allowed_examples=("How do I add NVTX ranges around a CUDA workload?",),
        blocked_examples=("Edit my source code to add NVTX ranges based on this report.",),
    ),
    CapabilityBoundarySpec(
        code="off_topic",
        category="scope",
        status="unsupported",
        rationale="The skill is scoped to Nsight Systems profiling/help, not general assistant tasks.",
        required_signals=("off_topic",),
        message="The request is outside Nsight Systems, CUDA profiling, or GPU performance-analysis scope.",
        answer=(
            "That request is outside my Nsight Systems profiling scope. "
            "I can help with Nsight Systems reports, `nsys` commands, CUDA/NVTX profiling workflows, recipes, and report evidence."
        ),
        allowed_examples=("What is Nsight Systems?",),
        blocked_examples=(
            "Tell me a joke about the weather.",
            "Write a poem about Nsight Systems.",
        ),
    ),
    CapabilityBoundarySpec(
        code="single_report_cross_report",
        category="evidence_shape",
        status="unsupported_without_evidence",
        rationale="Comparing ranks/runs/reports from one loaded report would mislead.",
        required_signals=("cross_report_comparison",),
        excluded_signals=("report_file_compatibility",),
        gate=BoundaryGate(report_loaded=True, report_count=1),
        message="Rank/run/report comparisons require multiple loaded reports; a single report would mislead.",
        answer=(
            "I cannot compare ranks, runs, or report sources from a single-report session. "
            "The loaded data contains only one report, so a cross-report comparison would be misleading. "
            "Load the directory of reports or multiple rank reports, then group by report label or use a multi-report recipe."
        ),
        allowed_examples=("Which GPU was this single report captured on?",),
        blocked_examples=("Which rank is slower in this loaded report?",),
    ),
    CapabilityBoundarySpec(
        code="sampled_metric_region_ranking",
        category="unsafe_metric_math",
        status="unsupported_without_validated_workflow",
        rationale="Naive joins between sampled metrics and tiny event regions can rank sample coverage rather than utilization.",
        required_signals=("sampled_metric_region_ranking",),
        excluded_signals=("ncu_execution", "ncu_metric_semantics", "root_cause_request"),
        message="Sampled GPU metrics should not be ranked over tiny per-event regions by naive timestamp joins.",
        answer=(
            "I cannot rank sampled GPU metrics over short NVTX ranges, kernels, or API calls with a naive timestamp join. "
            "The sampling interval can be longer than the event duration, so top rows may reflect sample count rather than utilization. "
            "Use a recipe or a time-weighted aggregation with minimum sample coverage instead."
        ),
        allowed_examples=("Are GPU metrics present in this report?",),
        blocked_examples=("Rank NVTX ranges by average SM Active from GPU metric samples.",),
    ),
    CapabilityBoundarySpec(
        code="gpu_metrics_absent_for_overlap",
        category="missing_report_evidence",
        status="unsupported_without_required_tables",
        rationale="Kernel/metric overlap requires sampled GPU metric rows; kernel timelines alone are not GPU metrics.",
        required_signals=("kernel_metric_overlap",),
        gate=BoundaryGate(report_loaded=True, missing_table_family="gpu_metrics"),
        message="The user asked for kernel/GPU-metric overlap, but GPU metric sample tables are absent.",
        answer=(
            "The loaded report does not contain sampled GPU metric rows, so I cannot compute kernel-vs-GPU-metric overlap from it. "
            "I can analyze kernel intervals/timing from the CUDA activity tables, or you can recollect with GPU metrics enabled for metric-overlap analysis."
        ),
        allowed_examples=("Are GPU metrics present in this report?",),
        blocked_examples=("What is the overlap between kernels and GPU metrics when GPU_METRICS is absent?",),
    ),
    CapabilityBoundarySpec(
        code="kernel_metric_overlap_unvalidated",
        category="unsafe_metric_math",
        status="unsupported_without_validated_workflow",
        rationale="Exact kernel/metric overlap requires a validated time-weighted workflow, not a prompt-level claim.",
        required_signals=("kernel_metric_overlap",),
        message=(
            "Exact overlap between sampled GPU metrics and kernel intervals is not a "
            "validated deterministic fact."
        ),
        answer=(
            "I cannot report an exact overlap between kernel intervals and GPU metric samples as a validated fact. "
            "GPU metrics are sampled signals, while kernels are interval events; naive timestamp joins can overstate precision or bias short intervals. "
            "I can safely report whether kernel activity and GPU metrics are present, or use a time-weighted recipe/workflow such as a GPU metric utilization map when available."
        ),
        allowed_examples=("Are kernels and GPU metrics both present in this report?",),
        blocked_examples=("What is the exact overlap between kernels and GPU metrics?",),
    ),
    CapabilityBoundarySpec(
        code="recipe_domain_semantics_unvalidated",
        category="unsafe_metric_math",
        status="unsupported_without_validated_workflow",
        rationale=(
            "Higher-level recipe or domain metrics require installed recipe/domain "
            "workflow semantics for interval union, attribution, and correlation."
        ),
        required_signals=("recipe_domain_semantic_analysis",),
        preflight=False,
        message=RECIPE_DOMAIN_SEMANTICS_MESSAGE,
        answer=RECIPE_DOMAIN_SEMANTICS_ANSWER,
        allowed_examples=("Which NCCL overlap recipes are available for this report?",),
        blocked_examples=("Compute exposed communication cost from raw CUPTI kernel rows with DuckDB.",),
    ),
    CapabilityBoundarySpec(
        code="workload_fingerprinting",
        category="missing_application_evidence",
        status="unsupported_without_user_context",
        rationale="A report can show activity signatures but not reliably identify model/workload class by itself.",
        required_signals=("workload_fingerprinting",),
        message="The report does not encode workload/model/algorithm identity as a reliable fact.",
        answer=(
            "I cannot identify the workload, model, or algorithm class from the report alone. "
            "The data can show event mix and names, but not a reliable workload label. "
            "Tell me the suspected pattern and I can check whether expected signatures are present."
        ),
        allowed_examples=("What GPU model is used in this report?",),
        blocked_examples=("What model or workload is this report from?",),
    ),
    CapabilityBoundarySpec(
        code="application_metric_absent",
        category="missing_application_evidence",
        status="unsupported_without_user_annotations",
        rationale="Training accuracy/loss and similar metrics are not implicit Nsight Systems report facts.",
        required_signals=("application_metric",),
        message="Application metrics such as training accuracy/loss require explicit app-provided evidence.",
        answer=(
            "Nsight Systems reports do not automatically contain application metrics such as training accuracy, loss, perplexity, or validation scores. "
            "I can answer only if the application recorded that value in report-visible evidence such as NVTX text, a captured log, or another explicit annotation. "
            "Otherwise, the report can show timing and activity, not model-quality metrics."
        ),
        allowed_examples=("What CUDA API time is visible in this report?",),
        blocked_examples=("What was the training accuracy in this profile?",),
    ),
    CapabilityBoundarySpec(
        code="interactive_visualization_unsupported",
        category="unsupported_ui_action",
        status="unsupported_in_byo_skill",
        rationale="The skill can return evidence but does not render interactive UI artifacts directly.",
        required_signals=("interactive_visualization",),
        message="The skill cannot render interactive visualizations directly.",
        answer=(
            "I cannot render an interactive chart or heatmap directly. "
            "I can provide a text/table summary from report evidence, or point you to an Nsight Systems recipe/notebook output when a recipe supports that visualization."
        ),
        allowed_examples=("Summarize CUDA API activity in a table.",),
        blocked_examples=("Create an interactive zoomable heatmap.",),
    ),
    CapabilityBoundarySpec(
        code="pure_cuda_code_generation",
        category="scope",
        status="unsupported",
        rationale="Pure CUDA implementation requests are outside Nsight Systems profiling scope unless tied to profiling evidence.",
        required_signals=("pure_cuda_code_generation",),
        excluded_signals=("profiling_context",),
        message="Pure CUDA kernel implementation is outside the Nsight Systems profiling scope.",
        answer=(
            "Writing CUDA kernel implementation code is outside this Nsight Systems profiling scope. "
            "I can help profile an existing kernel, identify timeline bottlenecks, choose Nsight Systems capture flags, or explain when to hand a specific kernel to Nsight Compute."
        ),
        allowed_examples=("How do I profile an existing CUDA kernel with Nsight Systems?",),
        blocked_examples=("Write a CUDA kernel for matrix multiplication.",),
    ),
    CapabilityBoundarySpec(
        code="ncu_execution_unsupported",
        category="unsupported_execution",
        status="unsupported_in_byo_skill",
        rationale="The skill can hand off to Nsight Compute, but it does not execute it.",
        required_signals=("ncu_execution",),
        exclude_when="ncu_conceptual_handoff_without_execution",
        message="Nsight Compute execution is outside the scope of this Nsight Systems skill.",
        answer=(
            "I cannot run Nsight Compute (`ncu`) from this Nsight Systems skill. "
            "I can identify candidate kernels from the loaded Nsight Systems report and provide handoff guidance for a separate Nsight Compute run."
        ),
        allowed_examples=("Which kernel should I inspect with Nsight Compute next?",),
        blocked_examples=("Run ncu on the hottest kernel.",),
    ),
    CapabilityBoundarySpec(
        code="application_profile_execution_unsupported",
        category="unsupported_execution",
        status="unsupported_in_byo_skill",
        rationale="Launching arbitrary user workloads is outside the BYO skill/tool evidence path.",
        required_signals=("application_profile_execution",),
        excluded_signals=(
            "custom_recipe_assist",
            "custom_recipe_full_generation",
            "destructive_local_action",
        ),
        message="This skill does not launch or profile arbitrary user programs on your behalf.",
        answer=(
            "I cannot launch or profile the application for you from this skill path. "
            "I can provide an `nsys profile ...` command and the evidence to collect. "
            "Run the command locally, then provide the resulting native `.nsys-rep` report for analysis."
        ),
        allowed_examples=("How do I profile ./train.py with Nsight Systems?",),
        blocked_examples=("Profile ./train.py for me, then analyze the result.",),
    ),
    CapabilityBoundarySpec(
        code="ncu_metric_semantics_unsupported",
        category="unsupported_metric_semantics",
        status="unsupported_without_nsight_compute_evidence",
        rationale="Nsight Compute metric/counter semantics should come from Nsight Compute docs/tools, not memory or Nsys-only evidence.",
        required_signals=("ncu_metric_semantics",),
        excluded_signals=("ncu_execution",),
        message="Detailed Nsight Compute metric definitions or values require Nsight Compute evidence.",
        answer=(
            "I cannot provide authoritative Nsight Compute metric definitions, counter values, or occupancy/stall interpretations from Nsight Systems evidence alone. "
            "Nsight Systems can identify candidate kernels and launch context for a separate Nsight Compute investigation; use Nsight Compute documentation or tools for the metric definitions and values."
        ),
        allowed_examples=("Which kernel should I inspect with Nsight Compute next?",),
        blocked_examples=("What does the Nsight Compute gpc__cycles_elapsed metric mean?",),
    ),
    CapabilityBoundarySpec(
        code="multi_hop_correlation",
        category="missing_correlation_evidence",
        status="unsupported_without_correlation_keys",
        rationale="Function/API/kernel chains need explicit correlation keys such as NVTX or CUPTI correlation ids.",
        required_signals=("multi_hop_correlation",),
        message="The requested call-stack/function/API/kernel chain needs correlation evidence that may not exist.",
        answer=(
            "I cannot reliably chain Python or CPU functions to CUDA API calls to kernels unless the report contains correlation evidence such as NVTX or shared correlation IDs across the hops. "
            "Without that, the SQL shape can produce guesses dressed as facts. "
            "Enable NVTX around the relevant code or ask for a two-table slice that has a verified correlation key."
        ),
        allowed_examples=("Which NVTX ranges are present in this report?",),
        blocked_examples=("Which Python function launched this CUDA kernel?",),
    ),
    CapabilityBoundarySpec(
        code="osrt_absent",
        category="missing_report_evidence",
        status="unsupported_without_required_tables",
        rationale="OS runtime claims require OSRT tables; profiler overhead or CUDA runtime tables are not substitutes.",
        required_signals=("os_runtime_request",),
        gate=BoundaryGate(report_loaded=True, missing_table_family="osrt"),
        message="The user asked for OS runtime data, but OS runtime tables are absent from the loaded report.",
        answer=(
            "This report does not contain OS runtime data, so I cannot produce OS runtime recipe results or summarize OS runtime calls/syscall overhead from it. "
            "Profiler/CUPTI overhead is a different signal and should not be used as OS runtime evidence. "
            "Recollect with OS runtime tracing enabled if you need syscall or OS runtime analysis."
        ),
        allowed_examples=("Summarize OS runtime calls when OSRT tables are present.",),
        blocked_examples=("Summarize OS runtime calls when only CUDA runtime tables are present.",),
    ),
    CapabilityBoundarySpec(
        code="invalid_cli_help_command",
        category="invalid_cli_shape",
        status="response_repair",
        rationale="The answer used an invalid Nsight Systems help command shape.",
        required_signals=("invalid_cli_help_command",),
        preflight=False,
        message="The answer used an invalid Nsight Systems help command shape.",
        answer=(
            "`nsys --help --flag` is not a valid way to inspect a flag. "
            "Use `nsys <command> --help` for a known subcommand, such as `nsys profile --help`, or search live help for the exact flag."
        ),
    ),
    CapabilityBoundarySpec(
        code="open_ended_root_cause",
        category="causal_claim_boundary",
        status="response_repair",
        rationale="A single report can describe symptoms but cannot prove open-ended root cause or optimal tuning changes.",
        required_signals=("root_cause_request",),
        preflight=False,
        message="A single report can describe symptoms but cannot prove open-ended root cause or optimal tuning changes.",
        answer=(
            "I cannot prove an open-ended root cause or optimal tuning change from this report alone. "
            "The report can describe timing, gaps, API waits, copies, and utilization symptoms, but causal fixes need corroborating evidence or experiments. "
            "Tell me the suspected bottleneck and I can check the relevant report signatures."
        ),
    ),
    CapabilityBoundarySpec(
        code="unsafe_recipe_path_override",
        category="scope",
        status="response_repair",
        rationale="The recipe tool sets its own input and output paths so runs stay safe and repeatable.",
        required_signals=(),
        preflight=False,
        message="The recipe tool sets its own input and output paths.",
        answer=(
            "I can't run a recipe with `--input`, `--output`, or `--export-dir` overrides. "
            "The recipe tool decides where it reads and writes files so runs stay safe and repeatable. "
            "Choose the report with the report input or session argument, and the tool returns a recipe output handle or label for the results."
        ),
    ),
    CapabilityBoundarySpec(
        code="unsafe_local_file_guidance",
        category="scope",
        status="response_repair",
        rationale="Nsight Systems report tools must not become arbitrary local file access or mutation tools.",
        required_signals=(),
        preflight=False,
        message="Local file access is limited to loaded reports and tool-owned outputs.",
        answer=(
            "I can't read, delete, attach, mutate, or expose arbitrary local files, local caches, or recipe-output directories through Nsight Systems report tools. "
            "For Nsight Systems analysis, use bounded read-only `SELECT`/`WITH` queries over the loaded `.nsys-rep` report tables, "
            "the loaded report directory, or tool-owned recipe output handles and labels."
        ),
    ),
    CapabilityBoundarySpec(
        code="local_path_leak",
        category="scope",
        status="response_repair",
        rationale="Runtime cache and recipe-output root paths are local implementation details, not user-facing evidence.",
        required_signals=(),
        preflight=False,
        message=LOCAL_PATH_LEAK_MESSAGE,
        answer=LOCAL_PATH_LEAK_ANSWER,
    ),
    CapabilityBoundarySpec(
        code="competitor_comparison",
        category="scope",
        status="unsupported",
        rationale="The product skill should explain Nsight Systems capabilities, not rank competing profilers.",
        required_signals=("competitor_tool_comparison",),
        message="Competitor ranking claims are outside the Nsight Systems skill scope.",
        answer=(
            "I can't make a competitor-comparison or claim which profiler is better. "
            "I can describe Nsight Systems capabilities and help decide whether it fits a specific profiling workflow."
        ),
        allowed_examples=(
            "Compare these two Nsight Systems reports by kernel duration.",
            "Should I use Nsight Systems before Nsight Compute for this CUDA application?",
            "Is Nsight Systems the replacement for NVIDIA Visual Profiler?",
        ),
        blocked_examples=(
            "Compare Nsight Systems with Intel VTune.",
            "How does nsys compare to VTune?",
            "Compare with TAU profiler.",
        ),
    ),
    CapabilityBoundarySpec(
        code="gui_action_boundary",
        category="unsupported_ui_action",
        status="response_repair",
        rationale="The skill works in text. It can point at what to inspect in the GUI but cannot operate the GUI itself.",
        required_signals=(),
        preflight=False,
        message="The skill cannot operate the Nsight Systems GUI directly.",
        answer=(
            "I can't operate the Nsight Systems GUI directly. "
            "I can use report evidence to identify timeline objects or time ranges, then tell you what to search for or inspect in the GUI."
        ),
    ),
    CapabilityBoundarySpec(
        code="unknown_cli_flags",
        category="invalid_cli_shape",
        status="response_repair",
        rationale="Exact CLI syntax must come from installed help or tool evidence, not model memory.",
        required_signals=(),
        preflight=False,
        message="Unverified Nsight Systems CLI flags must not be invented.",
        answer=(
            "I can't provide exact `nsys` CLI syntax, commands, flags, accepted values, or defaults from model memory alone. "
            "I should use live installed help such as `nsys <command> --help`; if a specific flag is not listed in installed help or tool evidence, I should say it is unverified instead of inventing behavior."
        ),
    ),
    CapabilityBoundarySpec(
        code="missing_report_input",
        category="missing_report_evidence",
        status="response_repair",
        rationale="Report-specific questions require a loaded native Nsight Systems report or report directory.",
        required_signals=(),
        preflight=False,
        message="Report-specific analysis requires a loaded Nsight Systems report.",
        answer=(
            "I can't answer report-specific questions such as GPU device, longest kernel, CUDA API timing, NVTX ranges, or recipe results until a Nsight Systems report is loaded. "
            "Provide a `.nsys-rep` report or configure a report path, then I can answer from report evidence."
        ),
    ),
)
