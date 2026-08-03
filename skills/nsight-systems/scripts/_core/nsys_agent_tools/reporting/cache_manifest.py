"""Small sidecar manifests for derived report-cache artifacts.

The manifests are for local debugging and release validation, not model-facing
evidence.  They intentionally avoid absolute input paths while recording enough
identity to explain which report/cache/export produced a DuckDB file.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .cache_keys import _nsys_cache_identity
from .duckdb_backend import _import_duckdb

CACHE_MANIFEST_SCHEMA = "nsys-report-cache-manifest-v1"


def write_duckdb_cache_manifest(
    manifest_path: Path,
    *,
    nsys_path: str,
    inputs: list[Path],
    db_path: Path,
    export_type: str,
) -> None:
    """Write a non-fatal manifest for Parquet-backed DuckDB cache artifacts."""

    _write_manifest(
        manifest_path,
        {
            "schema": CACHE_MANIFEST_SCHEMA,
            "cache_format_version": 1,
            "artifact": manifest_path.with_suffix("").name,
            "export_type": export_type,
            "nsys_identity_hash": _hash_text(_nsys_cache_identity(nsys_path)),
            "created_unix_s": int(time.time()),
            "inputs": [_input_record(path) for path in inputs],
            "report_count": len(inputs),
            "tables": _duckdb_tables(db_path),
        },
    )


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    """Best-effort atomic write; cache metadata must not break report analysis."""

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(path)
    except OSError:
        return


def _input_record(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "label": path.name,
        "suffix": path.suffix,
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "identity_hash": _hash_text(f"{path.name}:{stat.st_mtime_ns}:{stat.st_size}"),
    }


def _duckdb_tables(path: Path) -> list[str]:
    try:
        duckdb = _import_duckdb()
        with duckdb.connect(str(path), read_only=True) as con:
            rows = con.execute("SHOW TABLES").fetchall()
        return [str(row[0]) for row in rows]
    except Exception:  # noqa: BLE001 - cache manifest is advisory only
        return []


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]
