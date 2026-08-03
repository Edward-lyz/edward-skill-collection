from __future__ import annotations

import re
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..path_utils import is_relative_to
from ..sql_guard import DUCKDB_EXTERNAL_FILE_FUNCTIONS
from .paths import resolve_recipe_output_label
from .preview import inspect_recipe_output

if TYPE_CHECKING:
    from ..report import ReportRuntime

_DUCKDB_EXTERNAL_FILE_FUNCTION_RE = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in DUCKDB_EXTERNAL_FILE_FUNCTIONS) + r")\s*\(",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RecipeOutputRef:
    handle: str
    path: Path
    label: str
    recipe: str | None = None


class RecipeOutputStore:
    """Own recipe output paths and expose opaque handles to model-facing tools.

    The model/user should not be able to ask a tool to inspect arbitrary local
    directories. Recipe execution registers the directory it just created and
    later schema inspection resolves only those handles. Absolute paths remain
    private runtime state.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._outputs: dict[str, RecipeOutputRef] = {}
        self._payloads: dict[str, dict[str, Any]] = {}
        self._reuse_keys: dict[str, str] = {}

    def register_result(
        self,
        payload: dict[str, Any],
        *,
        reuse_key: str | None = None,
    ) -> dict[str, Any]:
        public = dict(payload)
        public.pop("output_dir", None)
        raw_path = public.pop("_local_output_path", None)
        if not raw_path:
            return public
        candidate = Path(raw_path).expanduser()
        if not candidate.is_dir():
            public.setdefault("output_label", candidate.name)
            public["output_available"] = False
            public["output_storage"] = "runtime-local"
            public["output_unavailable_reason"] = "recipe did not create an inspectable output directory"
            return public
        path = self._resolve_existing_dir(raw_path)
        handle = uuid.uuid4().hex[:12]
        ref = RecipeOutputRef(
            handle=handle,
            path=path,
            label=path.name,
            recipe=str(public.get("recipe") or "") or None,
        )
        public.pop("output_dir", None)
        public["output_handle"] = handle
        public["output_label"] = ref.label
        public["output_storage"] = "runtime-local"
        public["output_available"] = True
        with self._lock:
            self._outputs[handle] = ref
            self._payloads[handle] = dict(public)
            if reuse_key and public.get("ok") and public.get("data_available"):
                self._reuse_keys[reuse_key] = handle
        return public

    def reuse_result(self, reuse_key: str) -> dict[str, Any] | None:
        """Return a previous successful recipe result for this process."""

        with self._lock:
            handle = self._reuse_keys.get(reuse_key)
            ref = self._outputs.get(handle or "")
            payload = dict(self._payloads.get(handle or "", {}))
        if handle is None or ref is None or not payload:
            return None
        try:
            self._resolve_existing_dir(ref.path)
        except Exception:  # noqa: BLE001 - stale runtime cache entry
            with self._lock:
                self._reuse_keys.pop(reuse_key, None)
                self._outputs.pop(handle, None)
                self._payloads.pop(handle, None)
            return None
        payload["recipe_result_cache"] = "hit"
        payload["recipe_result_reused"] = True
        return payload

    def inspect(self, handle: str) -> dict[str, Any]:
        ref = self.resolve(handle)
        return self._inspect_ref(ref)

    def inspect_label(
        self,
        label: str,
        *,
        output_storage: str = "cli-local",
        output_note: str | None = None,
    ) -> dict[str, Any]:
        """Inspect a stateless CLI output label under this store root."""

        path = resolve_recipe_output_label(self.root, label)
        ref = RecipeOutputRef(handle="", path=path, label=path.name)
        return self._inspect_ref(
            ref,
            output_storage=output_storage,
            output_note=output_note
            if output_note is not None
            else (
                "The CLI inspected the output label under the configured output root; "
                "absolute paths are hidden."
            ),
        )

    def _inspect_ref(
        self,
        ref: RecipeOutputRef,
        *,
        output_storage: str = "runtime-local",
        output_note: str | None = None,
    ) -> dict[str, Any]:
        schemas = inspect_recipe_output(ref.path)
        payload = {
            "ok": True,
            "output_label": ref.label,
            "recipe": ref.recipe,
            "output_storage": output_storage,
            "schemas": schemas,
            "query_tables": recipe_output_query_tables_from_schemas(schemas),
        }
        if ref.handle:
            payload["output_handle"] = ref.handle
        if output_note:
            payload["output_note"] = output_note
        return payload

    def query(
        self,
        handle: str,
        *,
        report_runtime: ReportRuntime,
        sql: str,
        max_rows: int = 100,
        max_chars: int = 40000,
    ) -> dict[str, Any]:
        """Run bounded SQL against a registered recipe output directory."""

        ref = self.resolve(handle)
        return self._query_ref(
            ref,
            report_runtime=report_runtime,
            sql=sql,
            max_rows=max_rows,
            max_chars=max_chars,
        )

    def query_label(
        self,
        label: str,
        *,
        report_runtime: ReportRuntime,
        sql: str,
        max_rows: int = 100,
        max_chars: int = 40000,
        output_storage: str = "cli-local",
        output_note: str | None = None,
    ) -> dict[str, Any]:
        """Run bounded SQL against a stateless CLI output label."""

        path = resolve_recipe_output_label(self.root, label)
        ref = RecipeOutputRef(handle="", path=path, label=path.name)
        return self._query_ref(
            ref,
            report_runtime=report_runtime,
            sql=sql,
            max_rows=max_rows,
            max_chars=max_chars,
            output_storage=output_storage,
            output_note=output_note
            if output_note is not None
            else (
                "The CLI queried the output label under the configured output root; "
                "absolute paths are hidden."
            ),
        )

    def _query_ref(
        self,
        ref: RecipeOutputRef,
        *,
        report_runtime: ReportRuntime,
        sql: str,
        max_rows: int = 100,
        max_chars: int = 40000,
        output_storage: str = "runtime-local",
        output_note: str | None = None,
    ) -> dict[str, Any]:
        schemas = inspect_recipe_output(ref.path)
        query_tables = recipe_output_query_tables_from_schemas(schemas)
        file_sql_error = recipe_output_file_sql_error(sql, query_tables=query_tables)
        if file_sql_error:
            payload = {
                "ok": False,
                "error": file_sql_error,
                "output_label": ref.label,
                "recipe": ref.recipe,
                "output_storage": output_storage,
                "query_tables": query_tables,
            }
            if ref.handle:
                payload["output_handle"] = ref.handle
            if output_note:
                payload["output_note"] = output_note
            return payload
        session = report_runtime.load(ref.path)
        payload = report_runtime.query(session, sql, max_rows=max_rows, max_chars=max_chars)
        payload["output_label"] = ref.label
        payload["recipe"] = ref.recipe
        payload["output_storage"] = output_storage
        payload["query_tables"] = query_tables
        if ref.handle:
            payload["output_handle"] = ref.handle
        if output_note:
            payload["output_note"] = output_note
        if not payload.get("ok") and _looks_like_file_access_error(str(payload.get("error", ""))):
            payload["error"] = recipe_output_file_sql_error("", query_tables=query_tables)
        return payload

    def resolve(self, handle: str) -> RecipeOutputRef:
        if not re.fullmatch(r"[a-f0-9]{12,32}", handle.strip()):
            raise ValueError("Invalid recipe output handle.")
        with self._lock:
            ref = self._outputs.get(handle)
        if ref is None:
            raise KeyError("Unknown recipe output handle. Use the output_handle returned by nsys_run_recipe.")
        self._resolve_existing_dir(ref.path)
        return ref

    def _resolve_existing_dir(self, value: str | Path) -> Path:
        path = Path(value).expanduser().resolve()
        if not path.is_dir():
            raise FileNotFoundError(path.name)
        if not is_relative_to(path, self.root):
            raise ValueError("Recipe output is outside the configured recipe output root.")
        return path


def recipe_output_query_tables_from_schemas(schemas: list[dict[str, Any]]) -> list[dict[str, str]]:
    tables: list[dict[str, str]] = []
    for item in schemas:
        table = item.get("query_table")
        file = item.get("file")
        if table and file:
            tables.append({"file": str(file), "table": str(table)})
    return tables


def recipe_output_file_sql_error(sql: str, *, query_tables: list[dict[str, str]]) -> str:
    uses_file_reader = bool(_DUCKDB_EXTERNAL_FILE_FUNCTION_RE.search(sql))
    uses_file_literal = bool(re.search(r"""['"][^'"]+\.(?:csv|parquet)['"]""", sql, re.IGNORECASE))
    if sql and not (uses_file_reader or uses_file_literal):
        return ""
    table_names = ", ".join(item["table"] for item in query_tables[:8]) or "the query_table values from schema"
    return (
        "Recipe output SQL must query the runtime-created table names, not local "
        f"CSV/Parquet file paths or DuckDB file-reader functions. Use tables such as: {table_names}."
    )


def _looks_like_file_access_error(error: str) -> bool:
    lower = error.lower()
    return "external file" in lower or "file system operations are disabled" in lower
