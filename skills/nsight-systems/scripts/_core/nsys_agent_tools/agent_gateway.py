"""Portable Nsight Systems JSON command layer.

This module owns the command contract shared by the installed ``nsys_skill_cli``
CLI and the skill-local ``scripts/nsys_skill_cli.py`` launcher. It is limited to
local evidence commands. Installation, cleanup, and host setup stay in
``agent_cli.py`` so the skill wrapper can reuse these commands without pulling
in installer behavior.
"""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cli_tools import NsysCli, doctor
from .defaults import (
    DEFAULT_AGENT_CACHE_DIR,
    DEFAULT_AGENT_RECIPE_OUTPUT_DIR,
    NSYS_AGENT_REPORT_ROOTS_ENV,
    configured_report_roots,
)
from .guardrails.claim_checks import (
    check_answer_claims,
    collect_cli_flags,
    recipe_names_from_index,
    trace_tools_from_file,
)
from .json_output import emit_json
from .path_utils import is_relative_to
from .prompt_safety import exception_message, sanitize_text
from .recipe import RecipeOutputStore, run_recipe
from .recipe.paths import safe_recipe_output_label_for_error
from .report import ReportRuntime
from .report_store import ReportSessionStore
from .reporting.dependencies import report_dependency_status
from .reporting.facts_dispatch import fact_catalog, supported_fact_intents
from .skill_pack import SkillPack, SkillPackError
from .skill_pack_paths import SkillPackPathError, resolve_skill_pack_path
from .tool_registry import get_tool_spec
from .tool_service import NsysToolService, NsysToolServiceConfig

RUNTIME_ERROR_EXIT = 2
USAGE_ERROR_EXIT = 3
JSON_SCHEMA_VERSION = "nsys-agent-json-v1"
JSON_SOURCE = {"kind": "nsys-agent", "project": "nsys-agent-tools", "interface": "json-cli"}

GatewayHandler = Callable[[argparse.Namespace, "GatewayConfig"], dict[str, Any]]
GatewayCommandRegistrar = Callable[[Any, "GatewayConfig"], None]


@dataclass(frozen=True)
class GatewayConfig:
    """Runtime knobs for one gateway invocation."""

    prog: str = "nsys_skill_cli"
    default_skill_pack: str | Path | None = None
    cache_dir: str | Path = DEFAULT_AGENT_CACHE_DIR
    recipe_output_dir: str | Path = DEFAULT_AGENT_RECIPE_OUTPUT_DIR
    add_commands: GatewayCommandRegistrar | None = None


class CliUsageError(ValueError):
    """Raised when command-line arguments are invalid.

    argparse normally prints text to stderr and exits. The gateway is an
    agent-facing JSON interface, so usage failures are converted into structured
    JSON on stdout instead.
    """


class CliHelpRequested(ValueError):
    """Raised when argparse help should be returned as successful JSON."""


class CliInputError(ValueError):
    """Raised when syntactically valid CLI input points at unsupported data."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliUsageError(message)

    def print_help(self, file: Any | None = None) -> None:
        raise CliHelpRequested(self.format_help().strip())

    def exit(self, status: int = 0, message: str | None = None) -> None:
        if status:
            raise CliUsageError((message or "").strip() or f"argparse exited with status {status}")
        raise CliHelpRequested((message or self.format_help()).strip())


def main(
    argv: list[str] | None = None,
    *,
    prog: str = "nsys_skill_cli",
    default_skill_pack: str | Path | None = None,
    cache_dir: str | Path = DEFAULT_AGENT_CACHE_DIR,
    recipe_output_dir: str | Path = DEFAULT_AGENT_RECIPE_OUTPUT_DIR,
    add_commands: GatewayCommandRegistrar | None = None,
) -> int:
    """Run the portable JSON command layer and print one JSON object."""

    config = GatewayConfig(
        prog=prog,
        default_skill_pack=default_skill_pack,
        cache_dir=cache_dir,
        recipe_output_dir=recipe_output_dir,
        add_commands=add_commands,
    )
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        parser = build_parser(config)
        parsed = parser.parse_args(args)
        payload = parsed.handler(parsed, config)
        exit_code = 0 if payload.get("ok") else RUNTIME_ERROR_EXIT
    except CliHelpRequested as exc:
        help_data: dict[str, Any] = {"help": str(exc)}
        if args[:1] == ["report-fact"]:
            help_data["intents"] = fact_catalog()
        payload = command_payload("help", help_data)
        exit_code = 0
    except CliUsageError as exc:
        payload = _error("usage_error", str(exc))
        exit_code = USAGE_ERROR_EXIT
    except CliInputError as exc:
        payload = _error("input_error", str(exc))
        exit_code = USAGE_ERROR_EXIT
    except SkillPackError as exc:
        payload = _error("skill_pack_error", str(exc))
        exit_code = USAGE_ERROR_EXIT
    except Exception as exc:  # noqa: BLE001 - command boundary must return JSON failures
        payload = _error("unexpected_error", exception_message(exc))
        exit_code = RUNTIME_ERROR_EXIT
    print_json(payload)
    return exit_code


def build_parser(config: GatewayConfig | None = None) -> argparse.ArgumentParser:
    active = config or GatewayConfig()
    parser = JsonArgumentParser(
        prog=active.prog,
        description=(
            "Agent-facing JSON CLI for Nsight Systems docs, live nsys help, "
            "recipes, and report analysis."
        ),
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, parser_class=JsonArgumentParser
    )
    if active.add_commands is not None:
        active.add_commands(subparsers, active)
    _add_doctor_command(subparsers)
    _add_discovery_commands(subparsers)
    _add_recipe_commands(subparsers)
    _add_report_commands(subparsers)
    _add_claim_check_command(subparsers)
    return parser


def _add_doctor_command(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    doctor_command = add_command(subparsers, "doctor", _doctor, help_text=_tool_help("nsys_doctor"))
    _add_nsys_path_arg(doctor_command)
    _add_skill_pack_arg(doctor_command)


def _add_discovery_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    docs = add_command(subparsers, "search-docs", _search_docs, help_text=_tool_help("nsys_search_docs"))
    _add_skill_pack_arg(docs)
    docs.add_argument("--query", required=True)
    docs.add_argument("--limit", type=int, default=5)

    schema = add_command(
        subparsers, "lookup-schema", _lookup_schema, help_text=_tool_help("nsys_lookup_schema")
    )
    _add_skill_pack_arg(schema)
    schema.add_argument("--query", required=True)
    schema.add_argument("--limit", type=int, default=5)

    cli = add_command(subparsers, "inspect-cli", _inspect_cli, help_text=_tool_help("nsys_inspect_cli"))
    _add_skill_pack_arg(cli)
    cli.add_argument("--target", default="")
    _add_nsys_path_arg(cli)
    cli.add_argument("--max-chars", type=int, default=18000)


def _add_recipe_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    recipes = add_command(
        subparsers, "lookup-recipes", _lookup_recipes, help_text=_tool_help("nsys_lookup_recipes")
    )
    _add_skill_pack_arg(recipes)
    recipes.add_argument("--query", required=True)
    recipes.add_argument("--limit", type=int, default=8)
    _add_nsys_path_arg(recipes)

    list_recipes = add_command(
        subparsers, "list-recipes", _list_recipes, help_text=_tool_help("nsys_list_recipes")
    )
    _add_nsys_path_arg(list_recipes)

    explain = add_command(
        subparsers, "explain-recipe", _explain_recipe, help_text=_tool_help("nsys_explain_recipe")
    )
    _add_skill_pack_arg(explain)
    explain.add_argument("--recipe", required=True)
    _add_nsys_path_arg(explain)

    run = add_command(subparsers, "run-recipe", _run_recipe, help_text=_tool_help("nsys_run_recipe"))
    run.add_argument("--report", required=True)
    run.add_argument("--recipe", required=True)
    _add_nsys_path_arg(run)
    run.add_argument("--timeout", type=int, default=300)
    run.add_argument(
        "recipe_args",
        nargs=argparse.REMAINDER,
        help="Optional recipe flags after `--`. Path flags like --input/--output are rejected.",
    )

    output_schema = add_command(
        subparsers,
        "recipe-output-schema",
        _recipe_output_schema,
        help_text=_tool_help("nsys_recipe_output_schema"),
    )
    output_schema.add_argument("--output-label", required=True)

    output_query = add_command(
        subparsers,
        "recipe-output-query",
        _recipe_output_query,
        help_text=_tool_help("nsys_query_recipe_output"),
    )
    output_query.add_argument("--output-label", required=True)
    output_query.add_argument("--sql", required=True)
    output_query.add_argument("--max-rows", type=int, default=100)
    output_query.add_argument("--max-chars", type=int, default=40000)


def _add_report_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    _report_command(
        subparsers,
        "report-cache-status",
        _report_cache_status,
        _tool_help("nsys_report_cache_status"),
    )
    _report_command(
        subparsers, "report-context", _report_context, _tool_help("nsys_get_report_context")
    )

    describe = _report_command(
        subparsers, "report-describe", _report_describe, _tool_help("nsys_describe_tables")
    )
    describe.add_argument("--table", dest="tables", action="append", default=[], required=True)

    query = _report_command(
        subparsers, "report-query", _report_query, _tool_help("nsys_query_report")
    )
    query.add_argument("--sql", required=True)
    query.add_argument("--question", default="")
    query.add_argument("--max-rows", type=int, default=100)
    query.add_argument("--max-chars", type=int, default=40000)

    fact = _report_command(
        subparsers,
        "report-fact",
        _report_fact,
        "Return deterministic report facts selected by canonical intent. Help JSON includes intent routing metadata.",
    )
    fact.add_argument(
        "--intent",
        required=True,
        choices=supported_fact_intents(),
        metavar="<intent>",
    )
    fact.add_argument("--metric", default="")
    fact.add_argument(
        "--frame",
        type=int,
        default=None,
        help="Frame index for frame-scoped fact intents.",
    )
    fact.add_argument(
        "--max-rows",
        type=int,
        default=10,
        help="Maximum ranked result rows per fact (default 10, maximum 50).",
    )

    _report_command(subparsers, "report-doctor", _report_doctor, _tool_help("nsys_report_doctor"))


def _add_claim_check_command(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    claims = add_command(
        subparsers,
        "check-claims",
        _check_claims,
        help_text=(
            "Check a drafted Nsight Systems answer for unsupported exact claims "
            "(CLI flags, recipe names, environment variables, or report numbers) "
            "given the evidence gathered for it."
        ),
    )
    _add_skill_pack_arg(claims)
    _add_nsys_path_arg(claims)
    claims.add_argument("--question", default="")
    claims.add_argument("--answer", help="Answer text. Prefer --answer-file for multiline answers.")
    claims.add_argument("--answer-file", help="File containing the answer. Use '-' for stdin.")
    claims.add_argument(
        "--evidence-file",
        action="append",
        default=[],
        help="JSON/text evidence gathered for the answer. May be repeated.",
    )
    claims.add_argument("--trace-file", help="Optional trace JSON/JSONL file.")


def _tool_help(tool_name: str) -> str:
    spec = get_tool_spec(tool_name)
    return spec.description if spec is not None else tool_name


def add_command(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    handler: GatewayHandler,
    *,
    help_text: str,
) -> argparse.ArgumentParser:
    """Register one gateway-compatible command parser."""

    parser = subparsers.add_parser(name, help=help_text, description=help_text)
    parser.set_defaults(handler=handler)
    return parser


def _report_command(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    handler: GatewayHandler,
    help_text: str,
) -> argparse.ArgumentParser:
    parser = add_command(subparsers, name, handler, help_text=help_text)
    parser.add_argument("--report", required=True)
    _add_nsys_path_arg(parser)
    return parser


def _add_skill_pack_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--skill-pack",
        help=skill_pack_help(),
    )


def _add_nsys_path_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--nsys-path", default=os.environ.get("NSYS_PATH", "nsys"))


def skill_pack_help() -> str:
    return (
        "Built nsight-systems skill pack. Release installs use the bundled "
        "default; source checkouts should pass --skill-pack."
    )


def resolve_skill_pack_arg(args: argparse.Namespace, config: GatewayConfig) -> Path:
    configured = getattr(args, "skill_pack", None) or config.default_skill_pack
    try:
        return resolve_skill_pack_path(configured)
    except SkillPackPathError as exc:
        raise CliInputError(str(exc)) from exc


def _optional_skill_pack(args: argparse.Namespace, config: GatewayConfig) -> SkillPack | None:
    try:
        return SkillPack.load(resolve_skill_pack_arg(args, config))
    except (CliInputError, SkillPackError):
        return None


def _service(
    args: argparse.Namespace,
    config: GatewayConfig,
    *,
    report: Path | None = None,
    require_skill_pack: bool = True,
) -> NsysToolService:
    """Build the shared tool service for one stateless gateway command."""

    pack = (
        SkillPack.load(resolve_skill_pack_arg(args, config))
        if require_skill_pack
        else _optional_skill_pack(args, config)
    )
    nsys_path = getattr(args, "nsys_path", os.environ.get("NSYS_PATH", "nsys"))
    runtime = ReportRuntime(nsys_path=nsys_path, cache_dir=config.cache_dir)
    report_store = ReportSessionStore(runtime)
    default_report_session_id = None
    if report is not None:
        default_report_session_id = report_store.load_path(report, session_id="report").session_id
    return NsysToolService(
        NsysToolServiceConfig(
            pack=pack,
            cli=NsysCli(nsys_path),
            report_runtime=runtime,
            report_store=report_store,
            recipe_outputs=RecipeOutputStore(config.recipe_output_dir),
            nsys_path=nsys_path,
            default_report_session_id=default_report_session_id,
        )
    )


def _report_service(args: argparse.Namespace, config: GatewayConfig) -> NsysToolService:
    """Build a service for a stateless report command."""

    return _service(
        args,
        config,
        report=_resolve_report_input(args.report),
        require_skill_pack=False,
    )


def _doctor(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    payload = doctor(args.nsys_path)
    payload["skill_pack"] = _skill_pack_status(args, config)
    payload["report_dependencies"] = report_dependency_status()
    payload["status"] = _combine_status(
        payload.get("status"),
        payload["skill_pack"]["status"],
        _dependency_status_for_doctor(payload["report_dependencies"]),
    )
    return command_payload("doctor", payload, ok=payload.get("status") in {"pass", "warn"})


def _skill_pack_status(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    try:
        path = resolve_skill_pack_arg(args, config)
        manifest = SkillPack.load(path).manifest
    except Exception as exc:  # noqa: BLE001 - doctor returns diagnostics, not stack traces.
        return {
            "status": "fail",
            "name": "bundled skill pack",
            "detail": sanitize_text(str(exc), max_chars=1200),
        }
    return {
        "status": "pass",
        "name": "bundled skill pack",
        "detail": str(manifest.get("name", "nsight-systems")),
        "package_version": str(manifest.get("package_version", "")),
    }


def _dependency_status_for_doctor(payload: dict[str, Any]) -> str:
    return "pass" if payload.get("ready") else "warn"


def _combine_status(*statuses: object) -> str:
    status_set = {str(status) for status in statuses}
    if "fail" in status_set:
        return "fail"
    if "warn" in status_set:
        return "warn"
    return "pass"


def _search_docs(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    payload = _service(args, config).search_docs(args.query, limit=_limit(args.limit, 10))
    return command_payload("search-docs", payload, ok=bool(payload.get("ok")))


def _lookup_schema(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    payload = _service(args, config).lookup_schema(args.query, limit=_limit(args.limit, 10))
    if payload.get("ok"):
        payload["query"] = args.query
    return command_payload("lookup-schema", payload, ok=bool(payload.get("ok")))


def _inspect_cli(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    payload = _service(args, config, require_skill_pack=False).inspect_cli(
        args.target, max_chars=args.max_chars
    )
    return command_payload("inspect-cli", payload, ok=bool(payload.get("ok", True)))


def _lookup_recipes(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    payload = _service(args, config).lookup_recipes(args.query, limit=_limit(args.limit, 20))
    return command_payload("lookup-recipes", payload, ok=bool(payload.get("ok")))


def _list_recipes(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    payload = _service(args, config, require_skill_pack=False).list_recipes()
    return command_payload(
        "list-recipes",
        payload,
        ok=bool(payload.get("ok")) and bool(payload.get("recipes")),
    )


def _explain_recipe(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    payload = _service(args, config).explain_recipe(args.recipe)
    return command_payload("explain-recipe", payload, ok=bool(payload.get("ok")))


def _run_recipe(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    extra_args = _recipe_args_after_separator(args.recipe_args)
    report = _resolve_report_input(args.report)
    payload = run_recipe(
        nsys_path=args.nsys_path,
        recipe=args.recipe,
        report=report,
        output_dir=config.recipe_output_dir,
        report_cache_dir=config.cache_dir,
        extra_args=extra_args,
        timeout_s=args.timeout,
    )
    payload.pop("_local_output_path", None)
    if payload.get("output_available"):
        payload["output_storage"] = "cli-local"
        payload["schema_command"] = recipe_output_command(
            "recipe-output-schema",
            output_label=str(payload["output_label"]),
            prog=config.prog,
        )
        payload["query_command_template"] = recipe_output_command(
            "recipe-output-query",
            output_label=str(payload["output_label"]),
            sql="SELECT ... LIMIT 10",
            prog=config.prog,
        )
    return command_payload("run-recipe", payload, ok=bool(payload.get("ok")))


def _recipe_output_schema(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    try:
        payload = RecipeOutputStore(config.recipe_output_dir).inspect_label(args.output_label)
    except Exception as exc:  # noqa: BLE001 - command boundary returns JSON failures
        payload = _recipe_output_error(exc, args.output_label)
    return command_payload("recipe-output-schema", payload)


def _recipe_output_query(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    try:
        payload = RecipeOutputStore(config.recipe_output_dir).query_label(
            args.output_label,
            report_runtime=ReportRuntime(cache_dir=config.cache_dir),
            sql=args.sql,
            max_rows=args.max_rows,
            max_chars=args.max_chars,
        )
    except Exception as exc:  # noqa: BLE001 - command boundary returns JSON failures
        payload = _recipe_output_error(exc, args.output_label)
    return command_payload("recipe-output-query", payload)


def _report_cache_status(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    runtime = ReportRuntime(nsys_path=args.nsys_path, cache_dir=config.cache_dir)
    payload = runtime.cache_status(_resolve_report_status_input(args.report))
    return command_payload("report-cache-status", payload, ok=bool(payload.get("ok")))


def _report_context(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    payload = _report_service(args, config).get_report_context()
    return command_payload("report-context", payload, ok=bool(payload.get("ok")))


def _report_describe(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    payload = _report_service(args, config).describe_tables(args.tables)
    return command_payload("report-describe", payload, ok=bool(payload.get("ok")))


def _report_query(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    payload = _report_service(args, config).query_report(
        args.sql,
        question=args.question,
        max_rows=args.max_rows,
        max_chars=args.max_chars,
    )
    return command_payload("report-query", payload, ok=bool(payload.get("ok")))


def _report_fact(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    payload = _report_service(args, config).report_fact(
        intent=args.intent,
        metric=args.metric,
        max_rows=args.max_rows,
        frame=args.frame,
    )
    return command_payload("report-fact", payload, ok=bool(payload.get("ok")))


def _report_doctor(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    payload = _report_service(args, config).report_doctor()
    return command_payload(
        "report-doctor",
        payload,
        ok=str(payload.get("status")) in {"pass", "warn", "info"},
    )


def _check_claims(args: argparse.Namespace, config: GatewayConfig) -> dict[str, Any]:
    pack = SkillPack.load(resolve_skill_pack_arg(args, config))
    if args.trace_file and not Path(args.trace_file).is_file():
        raise CliInputError(f"--trace-file is not a file: {Path(args.trace_file).name}")
    answer = _read_claim_answer(args.answer, args.answer_file)
    evidence_text = _read_claim_evidence(args.evidence_file)
    result = check_answer_claims(
        question=args.question,
        answer=answer,
        evidence_text=evidence_text,
        trace_tools=trace_tools_from_file(args.trace_file),
        flags=collect_cli_flags(args.nsys_path, pack.recipes_index),
        recipes=recipe_names_from_index(pack.recipes_index),
    )
    return command_payload("check-claims", result, ok=bool(result.get("ok")))


def _read_claim_answer(answer: str | None, answer_file: str | None) -> str:
    if answer_file == "-":
        return sys.stdin.read()
    if answer_file:
        path = Path(answer_file)
        if not path.is_file():
            raise CliInputError(f"--answer-file is not a file: {path.name}")
        return path.read_text(encoding="utf-8", errors="replace")
    return answer or ""


def _read_claim_evidence(paths: list[str]) -> str:
    pieces: list[str] = []
    for raw in paths:
        path = Path(raw)
        if not path.is_file():
            raise CliInputError(f"--evidence-file is not a file: {path.name}")
        pieces.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(pieces)


def _resolve_report_input(report: str | Path) -> Path:
    """Resolve report input and optionally enforce user-configured roots."""

    path = _resolve_report_path_arg(report)
    if not path.exists():
        raise CliInputError(f"Report path does not exist: {path.name}")
    if not (path.is_file() or path.is_dir()):
        raise CliInputError(f"Report path is not a regular file or directory: {path.name}")
    return path


def _resolve_report_status_input(report: str | Path) -> Path:
    """Resolve a report-status path without requiring that it already exists."""

    return _resolve_report_path_arg(report)


def _resolve_report_path_arg(report: str | Path) -> Path:
    path = Path(report).expanduser().resolve()
    roots = configured_report_roots()
    if roots and not any(is_relative_to(path, root) for root in roots):
        raise CliInputError(f"Report path is outside {NSYS_AGENT_REPORT_ROOTS_ENV}.")
    return path


def _recipe_output_error(exc: Exception, output_label: str) -> dict[str, Any]:
    return {
        "ok": False,
        "error": exception_message(exc),
        "output_label": safe_recipe_output_label_for_error(output_label),
    }


def _recipe_args_after_separator(tokens: list[str]) -> list[str]:
    return tokens[1:] if tokens and tokens[0] == "--" else tokens


def recipe_output_command(
    command: str,
    *,
    output_label: str,
    prog: str = "nsys_skill_cli",
    sql: str | None = None,
) -> str:
    """Return a shell-safe recipe-output follow-up command."""

    argv = [prog, command, "--output-label", output_label]
    if sql is not None:
        argv.extend(["--sql", sql])
    return shlex.join(argv)


def _limit(value: int, maximum: int) -> int:
    return max(1, min(int(value), maximum))


def command_payload(
    command: str,
    data: dict[str, Any],
    *,
    ok: bool | None = None,
) -> dict[str, Any]:
    """Return the standard gateway JSON envelope."""

    payload_ok = bool(data.get("ok", True)) if ok is None else ok
    return {
        "schema_version": JSON_SCHEMA_VERSION,
        "source": dict(JSON_SOURCE),
        "ok": payload_ok,
        "command": command,
        "data": data,
        "paths_hidden": True,
    }


def _error(kind: str, message: str) -> dict[str, Any]:
    return {
        "schema_version": JSON_SCHEMA_VERSION,
        "source": dict(JSON_SOURCE),
        "ok": False,
        "error": {"kind": kind, "message": sanitize_text(message, max_chars=1200)},
        "paths_hidden": True,
    }


def print_json(payload: dict[str, Any]) -> None:
    """Print a gateway JSON payload after JSON-value sanitization."""

    emit_json(payload)
