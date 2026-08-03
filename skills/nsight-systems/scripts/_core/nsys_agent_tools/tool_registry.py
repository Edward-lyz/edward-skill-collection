"""Shared Nsight Systems tool metadata registry.

Tool implementations live in `NsysToolService` or the shared report/recipe
runtime helpers used by `nsys_skill_cli`. This registry owns stable names, public
labels, support categories, and short descriptions used by prompts, traces, and
tests. Keep descriptions concise and transport-neutral.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

REQUIRED_ARG = object()


@dataclass(frozen=True)
class ToolArgSpec:
    """Transport-neutral argument contract for adapter-generated tools."""

    name: str
    kind: str = "str"
    default: Any = REQUIRED_ARG
    description: str = ""


@dataclass(frozen=True)
class ToolSpec:
    name: str
    public_label: str
    category: str
    description: str
    requires_report: bool = False
    service_method: str = ""
    cli_command: str = ""
    adapters: tuple[str, ...] = ("cli",)
    guardrail_groups: tuple[str, ...] = ()
    args: tuple[ToolArgSpec, ...] = ()


def _report_fact_description() -> str:
    from .reporting.facts_dispatch import fact_prompt_guidance

    return "Return common measured facts with stable metric semantics. " + fact_prompt_guidance()


TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="nsys_search_docs",
        public_label="packaged documentation search",
        category="docs",
        description="Search packaged release docs, curated references, and recipe references.",
        service_method="search_docs",
        cli_command="search-docs",
        guardrail_groups=("recipe_evidence",),
        args=(ToolArgSpec("query", description="Question or topic to search for."),),
    ),
    ToolSpec(
        name="nsys_lookup_recipes",
        public_label="recipe lookup",
        category="recipe",
        description="Find installed recipes relevant to a task without running them.",
        service_method="lookup_recipes",
        cli_command="lookup-recipes",
        guardrail_groups=("recipe_evidence",),
        args=(ToolArgSpec("query", description="Task or recipe concept to search for."),),
    ),
    ToolSpec(
        name="nsys_inspect_cli",
        public_label="live nsys help",
        category="cli",
        description="Inspect live nsys command, recipe-command, or flag help.",
        service_method="inspect_cli",
        cli_command="inspect-cli",
        guardrail_groups=("cli_evidence", "recipe_evidence"),
        args=(
            ToolArgSpec(
                "target", default="", description="Command, recipe command, or flag to inspect."
            ),
        ),
    ),
    ToolSpec(
        name="nsys_doctor",
        public_label="local nsys environment check",
        category="cli",
        description="Check that the configured nsys CLI and recipe directory are usable.",
        service_method="check_environment",
        cli_command="doctor",
        guardrail_groups=("cli_evidence",),
    ),
    ToolSpec(
        name="nsys_report_cache_status",
        public_label="report cache status",
        category="report",
        description="Check whether native report Parquet/DuckDB cache artifacts already exist without exporting.",
        cli_command="report-cache-status",
        guardrail_groups=("report_evidence",),
    ),
    ToolSpec(
        name="nsys_get_report_context",
        public_label="report context",
        category="report",
        description=(
            "Return full report overview and table inventory. Prefer nsys_report_fact "
            "for common questions because full context can be expensive on large native reports."
        ),
        requires_report=True,
        service_method="get_report_context",
        cli_command="report-context",
        guardrail_groups=("report_evidence",),
    ),
    ToolSpec(
        name="nsys_describe_tables",
        public_label="report table description",
        category="report",
        description="Describe report table columns, row counts, and samples before SQL.",
        requires_report=True,
        service_method="describe_tables",
        cli_command="report-describe",
        guardrail_groups=("report_evidence",),
        args=(ToolArgSpec("tables", kind="list[str]", description="Report tables to describe."),),
    ),
    ToolSpec(
        name="nsys_query_report",
        public_label="report SQL query",
        category="report",
        description=(
            "Run bounded read-only SQL for supporting report facts. Do not use raw SQL "
            "to validate recipe/domain semantics such as exposed communication or "
            "communication/compute overlap."
        ),
        requires_report=True,
        service_method="query_report",
        cli_command="report-query",
        guardrail_groups=("report_evidence", "measured_report_evidence"),
        args=(
            ToolArgSpec("sql", description="Bounded read-only SQL query."),
            ToolArgSpec(
                "question",
                default="",
                description="Optional original user question for boundary guidance.",
            ),
        ),
    ),
    ToolSpec(
        name="nsys_report_fact",
        public_label="deterministic report fact",
        category="report",
        description=_report_fact_description(),
        requires_report=True,
        service_method="report_fact",
        cli_command="report-fact",
        guardrail_groups=("report_evidence", "measured_report_evidence"),
        args=(
            ToolArgSpec("intent", description="Stable report fact intent."),
            ToolArgSpec("metric", default="", description="Optional metric within the intent."),
            ToolArgSpec(
                "frame",
                kind="int",
                default=None,
                description="Optional graphics frame index for frame-scoped fact intents.",
            ),
            ToolArgSpec(
                "max_rows",
                kind="int",
                default=10,
                description="Maximum ranked result rows per fact (default 10, maximum 50).",
            ),
        ),
    ),
    ToolSpec(
        name="nsys_report_doctor",
        public_label="report health check",
        category="report",
        description="Run deterministic checks for empty/incomplete/inconsistent report data.",
        requires_report=True,
        service_method="report_doctor",
        cli_command="report-doctor",
        guardrail_groups=("report_evidence", "measured_report_evidence"),
    ),
    ToolSpec(
        name="nsys_lookup_schema",
        public_label="SQLite schema reference lookup",
        category="docs",
        description="Search packaged SQLite Schema Reference documentation.",
        service_method="lookup_schema",
        cli_command="lookup-schema",
        args=(ToolArgSpec("query", description="Schema concept, table, or column to search for."),),
    ),
    ToolSpec(
        name="nsys_list_recipes",
        public_label="installed recipe list",
        category="recipe",
        description="List installed recipes from live nsys recipe help.",
        service_method="list_recipes",
        cli_command="list-recipes",
        guardrail_groups=("cli_evidence", "recipe_evidence"),
    ),
    ToolSpec(
        name="nsys_explain_recipe",
        public_label="recipe help lookup",
        category="recipe",
        description="Return live help and packaged references for one recipe.",
        service_method="explain_recipe",
        cli_command="explain-recipe",
        guardrail_groups=("cli_evidence", "recipe_evidence"),
        args=(ToolArgSpec("recipe_name", description="Installed recipe name."),),
    ),
    ToolSpec(
        name="nsys_run_recipe",
        public_label="recipe execution",
        category="recipe",
        description=(
            "Run an installed recipe with tool-owned paths. Recipes can be long-running; "
            "prefer deterministic report facts for simple timing, device, or presence questions."
        ),
        requires_report=True,
        service_method="run_recipe",
        cli_command="run-recipe",
        guardrail_groups=(
            "report_evidence",
            "measured_report_evidence",
            "recipe_evidence",
            "recipe_execution_evidence",
        ),
        args=(
            ToolArgSpec("recipe_name", description="Installed recipe name."),
            ToolArgSpec(
                "extra_args",
                default="",
                description="Optional recipe flags after tool-owned input/output.",
            ),
        ),
    ),
    ToolSpec(
        name="nsys_recipe_output_schema",
        public_label="recipe output schema inspection",
        category="recipe",
        description="Inspect CSV/parquet schemas from a previous recipe output handle.",
        service_method="recipe_output_schema",
        cli_command="recipe-output-schema",
        guardrail_groups=("recipe_evidence",),
        args=(
            ToolArgSpec(
                "output_handle", description="Recipe output handle returned by nsys_run_recipe."
            ),
        ),
    ),
    ToolSpec(
        name="nsys_query_recipe_output",
        public_label="recipe output SQL query",
        category="recipe",
        description="Run bounded read-only SQL against a previous recipe output handle.",
        service_method="query_recipe_output",
        cli_command="recipe-output-query",
        guardrail_groups=(
            "report_evidence",
            "measured_report_evidence",
            "recipe_evidence",
            "recipe_execution_evidence",
        ),
        args=(
            ToolArgSpec(
                "output_handle", description="Recipe output handle returned by nsys_run_recipe."
            ),
            ToolArgSpec("sql", description="Bounded read-only SQL query over recipe outputs."),
        ),
    ),
)

_BY_NAME = {spec.name: spec for spec in TOOL_SPECS}


def get_tool_spec(name: str) -> ToolSpec | None:
    return _BY_NAME.get(name)


def tool_contract() -> list[dict[str, object]]:
    """Return a stable metadata view for docs/eval without a manual JSON copy."""

    return [
        {
            **spec.__dict__,
            "adapters": list(spec.adapters),
            "guardrail_groups": list(spec.guardrail_groups),
            "args": [
                {
                    "name": arg.name,
                    "kind": arg.kind,
                    "required": arg.default is REQUIRED_ARG,
                    "default": None if arg.default is REQUIRED_ARG else arg.default,
                    "description": arg.description,
                }
                for arg in spec.args
            ],
        }
        for spec in TOOL_SPECS
    ]


def tool_names_in_category(*categories: str) -> set[str]:
    """Return registered tool names for one or more product categories."""

    wanted = set(categories)
    return {spec.name for spec in TOOL_SPECS if spec.category in wanted}


def tool_names_requiring_report() -> set[str]:
    """Return tools whose contract requires a loaded report/session."""

    return {spec.name for spec in TOOL_SPECS if spec.requires_report}


def tool_names_in_guardrail_group(group: str) -> set[str]:
    """Return tool names that satisfy a reviewed guardrail evidence group."""

    return {spec.name for spec in TOOL_SPECS if group in spec.guardrail_groups}


def cli_command_by_tool() -> dict[str, str]:
    """Return the nsys_skill_cli command name for every CLI-backed tool spec."""

    return {
        spec.name: spec.cli_command
        for spec in TOOL_SPECS
        if "cli" in spec.adapters and spec.cli_command
    }
