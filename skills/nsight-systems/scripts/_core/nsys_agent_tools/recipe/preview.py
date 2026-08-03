from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from ..path_utils import is_relative_to
from ..prompt_safety import exception_message, sanitize_text, sanitize_value
from ..tabular_tables import tabular_table_names
from .paths import iter_regular_output_files
from .result_contract import magnitude_sort_column, recipe_preview_priority

MAX_RECIPE_OUTPUT_FILES = 500


def inspect_recipe_output(output_dir: str | Path, *, files: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Return schemas for CSV/Parquet files in a recipe output directory.

    The caller is responsible for passing only runtime-owned output directories.
    This helper still rejects symlinks and files outside the resolved output root
    because BYO scripts may call it directly.
    """

    root = Path(output_dir).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(root.name)
    if files is None:
        files = []
        for path in iter_regular_output_files(root):
            files.append({"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size})
            if len(files) >= MAX_RECIPE_OUTPUT_FILES:
                break
    schemas: list[dict[str, Any]] = []
    query_tables = _query_table_map(root, files)
    for item in files:
        rel = str(item.get("path", ""))
        path = root / rel
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if path.is_symlink() or not is_relative_to(resolved, root):
            continue
        suffix = path.suffix.lower()
        if suffix == ".parquet":
            schemas.append({"file": rel, "query_table": query_tables.get(rel), **_parquet_schema(resolved)})
        elif suffix == ".csv":
            schemas.append({"file": rel, "query_table": query_tables.get(rel), **_csv_schema(resolved)})
    return schemas[:50]


def _query_table_map(root: Path, files: list[dict[str, Any]]) -> dict[str, str]:
    """Return the table names ``ReportRuntime.load`` will create for outputs."""

    rel_paths = [str(item.get("path") or "") for item in files]
    tabular = [
        root / rel
        for suffix in (".parquet", ".csv")
        for rel in sorted(rel_paths)
        if rel.lower().endswith(suffix)
    ]
    absolute_names = tabular_table_names(tabular)
    return {
        path.relative_to(root).as_posix(): table
        for path_key, table in absolute_names.items()
        for path in (Path(path_key),)
    }


def preview_outputs(recipe_out: Path, files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    previews: list[dict[str, Any]] = []
    total_chars = 0
    max_previews = 4
    max_total = 16000
    candidates = [
        f
        for f in files
        if Path(str(f.get("path", ""))).suffix.lower()
        in {".csv", ".parquet", ".json", ".txt", ".log", ".md"}
    ]
    # Prefer tabular result files over notebooks/metadata.
    candidates.sort(key=lambda item: recipe_preview_priority(str(item.get("path", ""))))
    previewed_stems: set[str] = set()
    for item in candidates:
        if len(previews) >= max_previews or total_chars >= max_total:
            break
        rel = str(item.get("path", ""))
        stem_key = Path(rel).with_suffix("").as_posix()
        if stem_key in previewed_stems:
            continue
        path = recipe_out / rel
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if path.is_symlink() or not is_relative_to(resolved, recipe_out):
            continue
        preview = _preview_file(resolved, max_chars=max_total - total_chars)
        if not preview:
            continue
        total_chars += len(json.dumps(sanitize_value(preview, max_string_chars=max_total)))
        previews.append({"file": rel, **preview})
        previewed_stems.add(stem_key)
    return previews

def _preview_file(path: Path, *, max_chars: int) -> dict[str, Any] | None:
    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            return _preview_csv(path, max_chars=max_chars)
        if suffix == ".parquet":
            return _preview_parquet(path, max_rows=20, max_chars=max_chars)
        if suffix in {".json", ".txt", ".log", ".md"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            return {"kind": suffix.lstrip("."), "text": _safe_preview_text(text, max_chars=max_chars)}
    except Exception as exc:  # noqa: BLE001 - preview is best effort; recipe result still matters
        return {"kind": suffix.lstrip(".") or "file", "error": _safe_file_error(exc)}
    return None


def _preview_csv(path: Path, *, max_chars: int) -> dict[str, Any]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        sample = handle.read(min(max_chars + 1, 12000))
    rows = list(csv.reader(sample.splitlines()))
    return {
        "kind": "csv",
        "text": _safe_preview_text(sample, max_chars=max_chars),
        "sample_rows": [[sanitize_text(str(cell), max_chars=1000) for cell in row] for row in rows[:12]],
        "truncated": len(sample) > max_chars,
    }


def _preview_parquet(path: Path, *, max_rows: int, max_chars: int) -> dict[str, Any]:
    try:
        import pyarrow.parquet as pq

        pf = pq.ParquetFile(path)
        row_count = pf.metadata.num_rows if pf.metadata else None
        batch = next(pf.iter_batches(batch_size=max_rows), None)
        if batch is None:
            return {"kind": "parquet", "row_count": row_count, "text": "(empty parquet file)"}
        df = batch.to_pandas()
    except ImportError:
        import pandas as pd

        df = pd.read_parquet(path).head(max_rows)
        row_count = None
    # Recipe outputs usually do not include internal columns, but DuckDB-backed
    # output queries can add `__*` fields; avoid showing those implementation
    # columns as analysis evidence.
    df = df.drop(columns=[c for c in df.columns if str(c).startswith("__")], errors="ignore")
    df, preview_sort = _sort_preview_dataframe(df)
    include_index = _include_dataframe_index(df)
    try:
        table = df.to_markdown(index=include_index)
    except ImportError:
        table = df.to_string(index=include_index)
    payload: dict[str, Any] = {"kind": "parquet", "row_count": row_count, "text": _safe_preview_text(table, max_chars=max_chars)}
    if preview_sort:
        payload["preview_sort"] = preview_sort
    return payload


def _parquet_schema(path: Path) -> dict[str, Any]:
    try:
        import pyarrow.parquet as pq

        pf = pq.ParquetFile(path)
        schema = pf.schema_arrow
        columns = [{"name": sanitize_text(str(field.name), max_chars=1000), "type": str(field.type)} for field in schema]
        return {
            "kind": "parquet",
            "row_count": pf.metadata.num_rows if pf.metadata else None,
            "columns": columns,
        }
    except Exception as exc:  # noqa: BLE001 - schema is best effort
        return {"kind": "parquet", "error": _safe_file_error(exc)}


def _csv_schema(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            row_count = sum(1 for _ in reader)
        return {
            "kind": "csv",
            "row_count": row_count,
            "columns": [{"name": sanitize_text(str(h), max_chars=1000), "type": "string"} for h in header],
        }
    except Exception as exc:  # noqa: BLE001 - schema is best effort
        return {"kind": "csv", "error": _safe_file_error(exc)}


def _safe_file_error(exc: BaseException) -> str:
    """Sanitize and cap preview/schema errors before model exposure."""

    return exception_message(exc)


def _cap(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 18)] + "\n... (truncated)"


def _safe_preview_text(text: str, *, max_chars: int) -> str:
    """Sanitize recipe preview text at the source for BYO script mode.

    The shipped CLI/script surfaces can print this payload directly. Preview
    content can come from customer report data, command lines, NVTX labels, or
    recipe logs, so the source helper must hide local paths and control
    characters before it is printed or returned.
    """

    return sanitize_text(_cap(text, max_chars), max_chars=max_chars)


def _include_dataframe_index(df: Any) -> bool:
    index = getattr(df, "index", None)
    if index is None:
        return False
    if getattr(index, "name", None):
        return True
    try:
        return list(index[: min(len(index), 50)]) != list(range(min(len(index), 50)))
    except Exception:
        return False


def _sort_preview_dataframe(df: Any) -> tuple[Any, str]:
    """Sort common statistics previews by their primary magnitude column.

    Recipe previews are model-facing evidence. Many stats recipes emit tables
    with columns such as `Sum` or `Total`, and users naturally ask for the
    "top" or "most expensive" rows. Sorting the preview by a standard numeric
    magnitude column reduces answer mistakes without adding a question router
    or hardcoding one recipe.
    """

    column = magnitude_sort_column(getattr(df, "columns", []))
    if column is None:
        return df, ""
    try:
        sorted_df = df.sort_values(by=column, ascending=False, kind="mergesort")
    except Exception:
        return df, ""
    return sorted_df, f"{column} descending"
