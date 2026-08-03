"""Shared Nsight Systems tool implementation service.

Agent-facing CLIs and BYO scripts should call this service instead of
duplicating product behavior. The service is deliberately transport-neutral:
it returns JSON-like dictionaries and owns no CLI parser or host integration
imports.
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cli_tools import NsysCli, doctor, inspect_cli_help
from .docs import lookup_docs_and_recipes
from .prompt_safety import exception_message
from .recipe import RecipeOutputStore, lookup_recipes, recipe_match_summary, run_recipe
from .recipe.capabilities import recipe_capability_summary
from .report import ReportRuntime, ReportSession
from .report_store import ReportSessionStore
from .reporting.cache_keys import multi_report_cache_key
from .schema_reference import lookup_schema
from .skill_pack import SkillPack


@dataclass(frozen=True)
class NsysToolServiceConfig:
    """Dependencies and policy knobs for the shared tool service."""

    pack: SkillPack | None
    cli: NsysCli
    report_runtime: ReportRuntime
    report_store: ReportSessionStore
    recipe_outputs: RecipeOutputStore
    nsys_path: str
    default_report_session_id: str | None = None


class NsysToolService:
    """Single implementation authority for Nsight Systems tool behavior."""

    def __init__(self, config: NsysToolServiceConfig) -> None:
        self.config = config

    def search_docs(self, query: str, *, limit: int = 5) -> dict[str, Any]:
        if self.config.pack is None:
            return {"ok": False, "error": "A built skill pack is required for document search."}
        limit = _bounded_limit(limit, default=5, maximum=10)
        return {
            "ok": True,
            **lookup_docs_and_recipes(
                self.config.pack,
                query,
                nsys_path=self.config.nsys_path,
                limit=limit,
            ),
        }

    def lookup_recipes(self, query: str, *, limit: int = 8) -> dict[str, Any]:
        if self.config.pack is None:
            return {"ok": False, "error": "A built skill pack is required for recipe lookup."}
        limit = _bounded_limit(limit, default=8, maximum=20)
        matches = lookup_recipes(
            self.config.pack,
            query,
            self.config.nsys_path,
            limit=limit,
            live_recipes=self.config.cli.recipes(),
        )
        return {
            "ok": True,
            "query": query,
            "best_match": recipe_match_summary(matches[0] if matches else None),
            "recipe_matches": matches,
        }

    def inspect_cli(self, target: str = "", *, max_chars: int = 18000) -> dict[str, Any]:
        return inspect_cli_help(self.config.cli, target, pack=self.config.pack, max_chars=max_chars)

    def check_environment(self) -> dict[str, Any]:
        return doctor(self.config.nsys_path)

    def get_report_context(self, session_id: str = "") -> dict[str, Any]:
        session = self._resolve_report(session_id)
        if session is None:
            return _no_report()
        return {"ok": True, **self.config.report_runtime.context(session)}

    def describe_tables(self, tables: list[str], session_id: str = "") -> dict[str, Any]:
        session = self._resolve_report(session_id)
        if session is None:
            return _no_report()
        return {"ok": True, **self.config.report_runtime.describe_tables(session, tables)}

    def query_report(
        self,
        sql: str,
        session_id: str = "",
        *,
        max_rows: int = 100,
        max_chars: int = 40000,
        question: str = "",
    ) -> dict[str, Any]:
        session = self._resolve_report(session_id)
        if session is None:
            return _no_report()
        return self.config.report_runtime.query(
            session, sql, max_rows=max_rows, max_chars=max_chars, question=question
        )

    def report_fact(
        self,
        intent: str,
        metric: str = "",
        max_rows: int = 10,
        session_id: str = "",
        frame: int | None = None,
    ) -> dict[str, Any]:
        session = self._resolve_report(session_id)
        if session is None:
            return _no_report()
        return self.config.report_runtime.fact(
            session,
            intent=intent,
            metric=metric,
            max_rows=max_rows,
            frame=frame,
        )

    def report_doctor(self, session_id: str = "") -> dict[str, Any]:
        session = self._resolve_report(session_id)
        if session is None:
            return _no_report()
        return self.config.report_runtime.doctor(session)

    def lookup_schema(self, query: str, *, limit: int = 5) -> dict[str, Any]:
        if self.config.pack is None:
            return {"ok": False, "error": "A built skill pack is required for schema lookup."}
        limit = _bounded_limit(limit, default=5, maximum=10)
        return {
            "ok": True,
            "matches": [m.__dict__ for m in lookup_schema(self.config.pack, query, limit=limit)],
        }

    def list_recipes(self) -> dict[str, Any]:
        return {"ok": True, "recipes": self.config.cli.recipes()}

    def explain_recipe(self, recipe_name: str) -> dict[str, Any]:
        if self.config.pack is None:
            return {"ok": False, "error": "A built skill pack is required for recipe help lookup."}
        if not recipe_name:
            return {"ok": False, "error": "recipe_name is required"}
        live_help = self.config.cli.help(f"recipe {recipe_name}", max_chars=18000)
        matches = lookup_recipes(
            self.config.pack,
            recipe_name,
            self.config.nsys_path,
            limit=3,
            live_recipes=self.config.cli.recipes(),
        )
        capability_entry = dict(matches[0]) if matches else {"name": recipe_name}
        live_options = set(live_help.get("flags", [])) if live_help.get("ok") else None
        return {
            "ok": bool(live_help.get("ok") or matches),
            "recipe": recipe_name,
            "live_help": live_help,
            "capability_summary": recipe_capability_summary(
                capability_entry,
                live_options=live_options,
            ),
            "matches": matches,
        }

    def run_recipe(
        self, recipe_name: str, extra_args: str | list[str] = "", session_id: str = ""
    ) -> dict[str, Any]:
        session = self._resolve_report(session_id)
        if session is None:
            return _no_report()
        try:
            tokens = (
                shlex.split(extra_args)
                if isinstance(extra_args, str) and extra_args
                else list(extra_args or [])
            )
        except ValueError as exc:
            return {"ok": False, "error": f"invalid extra_args: {exc}"}
        reuse_key = _recipe_reuse_key(
            session=session,
            nsys_path=self.config.nsys_path,
            recipe_name=recipe_name,
            tokens=tokens,
        )
        reused = self.config.recipe_outputs.reuse_result(reuse_key)
        if reused is not None:
            return reused
        payload = run_recipe(
            nsys_path=self.config.nsys_path,
            recipe=recipe_name,
            report=session.input_path,
            output_dir=self.config.recipe_outputs.root,
            report_cache_dir=self.config.report_runtime.cache_dir,
            extra_args=tokens,
        )
        return self.config.recipe_outputs.register_result(payload, reuse_key=reuse_key)

    def recipe_output_schema(self, output_handle: str) -> dict[str, Any]:
        if not output_handle:
            return {"ok": False, "error": "output_handle is required"}
        try:
            return self.config.recipe_outputs.inspect(output_handle)
        except Exception as exc:  # noqa: BLE001 - tool surface returns JSON
            return {"ok": False, "error": _safe_tool_error(exc)}

    def query_recipe_output(self, output_handle: str, sql: str) -> dict[str, Any]:
        if not output_handle:
            return {"ok": False, "error": "output_handle is required"}
        try:
            return self.config.recipe_outputs.query(
                output_handle,
                report_runtime=self.config.report_runtime,
                sql=sql,
                max_rows=100,
                max_chars=40000,
            )
        except Exception as exc:  # noqa: BLE001 - tool surface returns JSON
            return {"ok": False, "error": _safe_tool_error(exc)}

    def _resolve_report(self, session_id: str = "") -> ReportSession | None:
        effective_id = session_id or self.config.default_report_session_id or ""
        resolved = self.config.report_store.resolve(effective_id)
        return resolved[1] if resolved else None


def _bounded_limit(value: int, *, default: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(parsed, maximum))


def _no_report() -> dict[str, Any]:
    return {"ok": False, "error": "No report is currently loaded."}


def _safe_tool_error(exc: BaseException) -> str:
    return exception_message(exc)


def _recipe_reuse_key(
    *,
    session: ReportSession,
    nsys_path: str,
    recipe_name: str,
    tokens: list[str],
) -> str:
    report_inputs = session.multi_reports or (session.input_path,)
    try:
        report_key = multi_report_cache_key(tuple(Path(path).resolve() for path in report_inputs), nsys_path)
    except OSError:
        report_key = hashlib.sha256(
            "|".join(str(path) for path in report_inputs).encode("utf-8", errors="replace")
        ).hexdigest()[:16]
    payload = {
        "schema": "nsys-recipe-result-reuse-key-v1",
        "recipe": recipe_name,
        "args": list(tokens),
        "report_key": report_key,
        "nsys_recipe_path": os.environ.get("NSYS_RECIPE_PATH", ""),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
