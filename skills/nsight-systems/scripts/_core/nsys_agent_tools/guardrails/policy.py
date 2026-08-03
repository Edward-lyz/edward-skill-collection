"""Reviewed lexical signals for response guardrails.

This module intentionally contains only data-like regexes and word sets. The
execution logic lives in sibling check modules and ``guardrails.__init__``. Keeping the
signals here makes reviewer-owned policy changes visible and avoids burying new
natural-language patterns inside control flow.
"""

from __future__ import annotations

import re

from ..boundary_text import (
    COMPARISON_REQUEST_RE,
    COMPETITOR_COMPARISON_RE,
    COMPETITOR_PROFILER_RE,
    NVIDIA_PROFILER_REFERENCE_RE,
)
from ..sql_guard import EXTERNAL_FILE_SQL_BOUNDARY_TERMS
from ..tool_registry import tool_names_in_guardrail_group

_FLAG_RE = re.compile(r"(?<![\w-])--([a-z][a-z0-9-]*)")
_RECIPE_INVOCATION_RE = re.compile(r"\bnsys\s+recipe\s+([a-z][a-z0-9_]{2,60})\b")
_ENV_VAR_RE = re.compile(
    r"\$\{?([A-Z][A-Z0-9_]{2,60})\}?"
    r"|\bexport\s+([A-Z][A-Z0-9_]{2,60})\b"
    r"|\b([A-Z][A-Z0-9_]{2,60})="
)
_EXTERNAL_SQL_FUNCTION_RE = re.compile(r"\b(" + "|".join(EXTERNAL_FILE_SQL_BOUNDARY_TERMS) + r")\b", re.IGNORECASE)
# Broad local-path prefixes are a path-hygiene policy boundary, not report
# routing. Normal report paths are permitted separately through explicit
# report-reference roots; this signal catches accidental cache/workspace leaks
# and arbitrary local-file suggestions in final answers.
_LOCAL_SENSITIVE_PATH_RE = re.compile(
    r"(?<![\w.:-])/(?:etc|proc|sys|dev|root|home|var|Users|Volumes|mnt|opt|workspace|scratch|tmp|srv|data|cluster)"
    r"(?=$|[^A-Za-z0-9_.-])"
    r"(?:/[\w. @%+=:,/_-]*)?"
)
_GUI_ACTION_RE = re.compile(
    r"\b(zoom|highlight|click|open|pan|select)\b.*\b(gui|timeline|view)\b|"
    r"\b(gui|timeline|view)\b.*\b(zoom|highlight|click|open|pan|select)\b",
    re.IGNORECASE,
)
_COMPETITOR_EXCLUSION_RE = re.compile(rf"\b{NVIDIA_PROFILER_REFERENCE_RE}\b", re.IGNORECASE)
_COMPETITOR_PROFILER_RE = re.compile(rf"\b{COMPETITOR_PROFILER_RE}\b", re.IGNORECASE)
_COMPARISON_REQUEST_RE = re.compile(COMPARISON_REQUEST_RE, re.IGNORECASE)
_COMPETITOR_COMPARISON_RE = re.compile(COMPETITOR_COMPARISON_RE, re.IGNORECASE)
_BOUNDARY_DECLINE_PHRASES = (
    "can't compare",
    "cannot compare",
    "won't compare",
    "do not compare",
    "don't compare",
    "outside",
    "instead, i can",
    "i can describe",
)
_LOCAL_FILE_BOUNDARY_PHRASES = (
    "arbitrary local",
    "external file",
    "loaded reports",
    "output handle",
    "output_label",
    "not inspect",
    "can't inspect",
    "cannot inspect",
)
_REPORT_SQL_CONTRADICTION_PHRASES = (
    "can't use the report sql path",
    "cannot use the report sql path",
    "can't run report sql",
    "cannot run report sql",
)
_RECIPE_PATH_OVERRIDE_RE = re.compile(
    r"(?<![\w-])(?:--input|--output|--output-dir|--export-dir)(?:\s|=)"
)
_GUI_BOUNDARY_PHRASES = (
    "can't operate",
    "cannot operate",
    "can't control",
    "cannot control",
    "can't click",
    "cannot click",
    "can't zoom",
    "cannot zoom",
    "can't open the gui",
    "cannot open the gui",
    "i can identify",
)
_HANDOFF_REPORT_ID_RE = re.compile(r"\brank\d+\b")
_HANDOFF_TIMING_WORDS = (" ns", " us", " ms", " s", "duration")
_HANDOFF_EVIDENCE_MARKERS = (
    '"intent": "nsight_compute_handoff"',
    '"metric": "max_single_duration"',
    '"max_duration_ns"',
)
_UNIT_NUMBER_RE = re.compile(
    r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?\s*"
    r"(kernels?|launches?|calls?|events?|rows?|samples?|threads?|processes?|files?|%|percent|ns|us|ms|s)\b",
    re.IGNORECASE,
)
_EXPLICIT_REPORT_WORDS = {
    "my report",
    "loaded report",
    "profiling run",
    "profile run",
    "in this report",
    "in my application",
    "this report",
    "the report",
    "loaded reports",
}
_REPORT_SUBJECT_WORDS = {
    "kernel",
    "kernels",
    "cuda api",
    "cuda runtime",
    "gpu being used",
    "gpu device",
    "nvtx ranges",
    "synchronous memory",
    "memcpy",
    "memory copy",
    "metric samples",
    "gpu metrics",
}
_REPORT_RANK_OR_MEASURE_WORDS = {
    "longest",
    "slowest",
    "highest",
    "most frequently",
    "unique kernels",
    "total time",
    "duration",
    "count",
    "how many",
}
_DOCS_EXPLANATION_RE = re.compile(
    r"\b(?:what\s+(?:is|are|does)|how\s+(?:do|does|can)|where\s+is|describe|"
    r"explain|used\s+for|documentation|document|after\s+opening)\b",
    re.IGNORECASE,
)
_TROUBLESHOOTING_WORDS = {
    "empty report",
    "blank report",
    "no data",
    "missing data",
    "didn't capture",
    "did not capture",
    "not capture",
    "what should i check",
    "why is my report",
    "after profiling",
    "troubleshoot",
    "troubleshooting",
}
_NO_REPORT_BOUNDARY_PHRASES = (
    "no report",
    "report is required",
    "report required",
    "provide a report",
    "load a report",
    "loaded report is required",
    "can't determine",
    "cannot determine",
    "need a loaded",
)
_CLI_WORDS = {"nsys ", "--", "cli", "command", "flag", "option"}
_RECIPE_WORDS = {"recipe", "recipes", "nsys recipe"}
# These broad question words are safe only after explicit-report and
# execution/result-output wording has been excluded by the guardrail logic.
_RECIPE_REFERENCE_QUESTION_WORDS = (
    "which",
    "what",
    "how",
    "explain",
    "help",
    "list",
    "name",
)
_RECIPE_EXECUTION_VERB_RE = re.compile(r"\b(?:run|execute)\b")
_RECIPE_RESULT_OR_OUTPUT_WORDS = (
    "result",
    "results",
    "output",
    "generated",
)
_REPORT_TOOLS = tool_names_in_guardrail_group("report_evidence")
_MEASURED_REPORT_TOOLS = tool_names_in_guardrail_group("measured_report_evidence")
_CLI_TOOLS = tool_names_in_guardrail_group("cli_evidence")
_RECIPE_TOOLS = tool_names_in_guardrail_group("recipe_evidence")
_RECIPE_EXECUTION_TOOLS = tool_names_in_guardrail_group("recipe_execution_evidence")
_RECIPE_OUTPUT_WORDS = {
    "output file",
    "output files",
    "generated file",
    "generated files",
    "what files",
    "which files",
    "file columns",
    "what columns",
    "which columns",
    "output columns",
    "schema",
}
