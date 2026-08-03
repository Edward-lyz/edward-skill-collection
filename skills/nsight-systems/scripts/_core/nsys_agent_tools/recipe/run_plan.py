"""Prepare safe, runtime-owned recipe executions."""

from __future__ import annotations

import re
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..cli_tools import NsysCli, nsys_failure_hint
from ..defaults import DEFAULT_AGENT_CACHE_DIR
from ..reporting.cache_keys import multi_report_cache_key
from .args import (
    first_path_control_arg,
    normalize_extra_args,
    sanitize_extra_args,
    value_taking_flags_from_help,
)
from .health import recipe_failure_payload, recipe_preflight
from .input_alias import prepare_recipe_input_alias
from .redaction import redact_error
from .report_inputs import recipe_report_files


@dataclass(frozen=True)
class RecipeRunContext:
    nsys_path: str
    recipe: str
    report_path: Path
    recipe_input_path: Path
    output_root: Path
    output_path: Path
    export_path: Path
    export_lock_path: Path
    export_reports: tuple[Path, ...]
    scratch_dir: tempfile.TemporaryDirectory[str] | None
    recipes: dict[str, str]
    recipe_help: dict[str, Any]
    allowed_flags: set[str]
    preflight: dict[str, Any]
    command: list[str]

    def cleanup(self) -> None:
        if self.scratch_dir is not None:
            self.scratch_dir.cleanup()


def prepare_recipe_run(
    *,
    nsys_path: str,
    recipe: str,
    report: str | Path,
    output_dir: str | Path,
    extra_args: list[str],
    report_cache_dir: str | Path = DEFAULT_AGENT_CACHE_DIR,
) -> RecipeRunContext | dict[str, Any]:
    """Validate recipe inputs and build the exact runtime-owned command."""

    extra_args = normalize_extra_args(extra_args)
    report_path = Path(report).expanduser().resolve()
    out_root = Path(output_dir).expanduser().resolve()
    preflight = recipe_preflight(
        recipe=recipe,
        report_path=report_path,
        output_root=out_root,
        extra_args=extra_args,
    )
    early_failure = _basic_recipe_input_failure(recipe, report_path, preflight)
    if early_failure is not None:
        return early_failure

    cli = NsysCli(nsys_path)
    recipes, catalog_failure = _load_recipe_catalog(cli, nsys_path, recipe, preflight)
    if catalog_failure is not None:
        return catalog_failure
    preflight["recipe_available"] = True
    preflight["display_name"] = recipes.get(recipe)

    if path_control := first_path_control_arg(extra_args):
        return recipe_failure_payload(
            recipe=recipe,
            error=(
                f"Recipe path-control argument {path_control} is not accepted. "
                "Use the supported --report input; the runtime owns recipe input "
                "and output paths for safety and path hygiene."
            ),
            preflight=preflight,
            category="invalid_recipe_args",
        )

    recipe_help = cli.help(f"recipe {recipe}", max_chars=12000)
    preflight["live_help_ok"] = bool(recipe_help.get("ok"))
    allowed_flags = set(recipe_help.get("flags", [])) if recipe_help.get("ok") else set()
    value_taking_flags = value_taking_flags_from_help(str(recipe_help.get("help_text", "")))
    if extra_args and not recipe_help.get("ok"):
        return recipe_failure_payload(
            recipe=recipe,
            error="Recipe-specific live help could not be inspected, so extra recipe arguments were not accepted.",
            preflight=preflight,
            category="recipe_help_unavailable",
        )

    output_failure = _ensure_output_root(recipe, preflight, report_path, out_root)
    if output_failure is not None:
        return output_failure
    recipe_out = _new_recipe_output_path(out_root, recipe)
    input_alias = prepare_recipe_input_alias(
        recipe=recipe,
        report_path=report_path,
        output_root=out_root,
        recipe_out=recipe_out,
        preflight=preflight,
    )
    if isinstance(input_alias, dict):
        return input_alias
    recipe_input_path, scratch_dir = input_alias
    recipe_export, export_lock_path, export_reports = _shared_recipe_export_path(
        nsys_path=nsys_path,
        report_path=report_path,
        report_cache_dir=report_cache_dir,
    )
    command = _base_recipe_command(
        nsys_path=nsys_path,
        recipe=recipe,
        recipe_input_path=recipe_input_path,
        recipe_out=recipe_out,
        recipe_export=recipe_export,
    )
    extra_arg_failure = _append_recipe_extra_args(
        command,
        recipe=recipe,
        report_path=report_path,
        recipe_out=recipe_out,
        extra_args=extra_args,
        allowed_flags=allowed_flags,
        value_taking_flags=value_taking_flags,
        preflight=preflight,
    )
    if extra_arg_failure is not None:
        return extra_arg_failure
    return RecipeRunContext(
        nsys_path=nsys_path,
        recipe=recipe,
        report_path=report_path,
        recipe_input_path=recipe_input_path,
        output_root=out_root,
        output_path=recipe_out,
        export_path=recipe_export,
        export_lock_path=export_lock_path,
        export_reports=export_reports,
        scratch_dir=scratch_dir,
        recipes=recipes,
        recipe_help=recipe_help,
        allowed_flags=allowed_flags,
        preflight=preflight,
        command=command,
    )


def _base_recipe_command(
    *,
    nsys_path: str,
    recipe: str,
    recipe_input_path: Path,
    recipe_out: Path,
    recipe_export: Path,
) -> list[str]:
    return [
        nsys_path,
        "recipe",
        recipe,
        "--input",
        str(recipe_input_path),
        "--output",
        str(recipe_out),
        "--export-dir",
        str(recipe_export),
    ]


def _append_recipe_extra_args(
    command: list[str],
    *,
    recipe: str,
    report_path: Path,
    recipe_out: Path,
    extra_args: list[str],
    allowed_flags: set[str],
    value_taking_flags: set[str],
    preflight: dict[str, Any],
) -> dict[str, Any] | None:
    if not extra_args:
        return None
    try:
        accepted_extra_args = sanitize_extra_args(
            extra_args,
            allowed_flags=allowed_flags,
            value_taking_flags=value_taking_flags,
        )
    except ValueError as exc:
        return recipe_failure_payload(
            recipe=recipe,
            error=redact_error(exc, report_path=report_path, recipe_out=recipe_out),
            preflight=preflight,
            category="invalid_recipe_args",
        )
    preflight["accepted_extra_args"] = accepted_extra_args
    command.extend(accepted_extra_args)
    return None


def _basic_recipe_input_failure(
    recipe: str,
    report_path: Path,
    preflight: dict[str, Any],
) -> dict[str, Any] | None:
    if not re.fullmatch(r"[a-z0-9_]+", recipe):
        return recipe_failure_payload(
            recipe=recipe,
            error=f"Invalid recipe name: {recipe!r}",
            preflight=preflight,
            category="invalid_recipe_name",
        )
    if not report_path.exists():
        return recipe_failure_payload(
            recipe=recipe,
            error=f"report input not found: {report_path.name}",
            preflight=preflight,
            category="report_missing",
        )
    if not (report_path.is_file() or report_path.is_dir()):
        return recipe_failure_payload(
            recipe=recipe,
            error=f"report input is not a regular file or directory: {report_path.name}",
            preflight=preflight,
            category="invalid_report_input",
        )
    return None


def _load_recipe_catalog(
    cli: NsysCli,
    nsys_path: str,
    recipe: str,
    preflight: dict[str, Any],
) -> tuple[dict[str, str], dict[str, Any] | None]:
    version = cli.version()
    preflight["nsys_version_ok"] = version.ok
    if version.ok:
        preflight["nsys_version"] = version.text.strip().splitlines()[0] if version.text.strip() else ""
    else:
        return {}, recipe_failure_payload(
            recipe=recipe,
            error=nsys_failure_hint(nsys_path, version.error),
            preflight=preflight,
            category="nsys_unavailable",
        )
    recipes = cli.recipes()
    preflight["recipe_catalog_ok"] = bool(recipes)
    if recipe not in recipes:
        return {}, recipe_failure_payload(
            recipe=recipe,
            error=f"Unknown recipe for this nsys installation: {recipe}",
            preflight=preflight,
            category="unknown_recipe",
        )
    return recipes, None


def _ensure_output_root(
    recipe: str,
    preflight: dict[str, Any],
    report_path: Path,
    out_root: Path,
) -> dict[str, Any] | None:
    try:
        out_root.mkdir(parents=True, exist_ok=True)
    except Exception as exc:  # noqa: BLE001 - JSON tool boundary
        return recipe_failure_payload(
            recipe=recipe,
            error=redact_error(exc, report_path=report_path, recipe_out=out_root),
            preflight=preflight,
            category="output_root_unavailable",
        )
    preflight["output_root_writable"] = True
    return None


def _new_recipe_output_path(out_root: Path, recipe: str) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    return out_root / f"{recipe}-{stamp}-{uuid.uuid4().hex[:10]}"


def _shared_recipe_export_path(
    *,
    nsys_path: str,
    report_path: Path,
    report_cache_dir: str | Path,
) -> tuple[Path, Path, tuple[Path, ...]]:
    reports = recipe_report_files(report_path)
    artifact_prefix = "multi" if report_path.is_dir() else "report"
    key = multi_report_cache_key(reports, nsys_path)
    cache_root = Path(report_cache_dir).expanduser().resolve()
    cache_root.mkdir(parents=True, exist_ok=True)
    export_root = cache_root / f"{artifact_prefix}-{key}-parquet"
    return (
        export_root,
        cache_root / f"{artifact_prefix}-{key}.lock",
        reports,
    )
