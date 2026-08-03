"""Structured evidence helpers for report-facing tool payloads.

The runtime intentionally keeps this smaller than a full wire-format layer:
the CLI and BYO script entry points still return their existing payloads, but
report outputs carry a common evidence block and stable row keys where the
runtime knows the row identity. This gives agents predictable structured
evidence without replacing recipes or forcing every adapter through a new
protocol.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from .schema import (
    CPU_SAMPLING_TABLES,
    CUDA_GRAPH_TABLES,
    GRAPHICS_API_TABLES,
    TABLE_CUDA_KERNEL,
    TABLE_CUDA_MEMCPY,
    TABLE_CUDA_MEMSET,
    TABLE_CUDA_RUNTIME,
    TABLE_CUDA_SYNC,
    TABLE_DIAGNOSTIC_EVENT,
    TABLE_DX11_API,
    TABLE_DX12_API,
    TABLE_DX12_WORKLOAD,
    TABLE_DXGI_API,
    TABLE_ETW_EVENTS,
    TABLE_GPU_METRICS,
    TABLE_NVTX_EVENTS,
    TABLE_OPENGL_API,
    TABLE_TARGET_INFO_GPU,
    TABLE_TARGET_INFO_GPU_METRICS,
    TABLE_VULKAN_API,
    WDDM_TABLE_PREFIX,
    upper_table_names,
)
from .types import ReportSession

EVIDENCE_SCHEMA = "nsys-report-evidence-v1"


def report_evidence(session: ReportSession, *, command: str, intent: str | None = None) -> dict[str, Any]:
    """Return the common evidence header for report tool payloads.

    Absolute paths stay in runtime state. The exposed block identifies the
    report/session by display label and source kind so a model can cite scope
    without seeing local filesystem details.
    """

    payload: dict[str, Any] = {
        "schema": EVIDENCE_SCHEMA,
        "source": "nsight-systems-report",
        "command": command,
        "report_label": session.display_label,
        "source_kind": session.source,
        "paths_hidden": True,
        "cache": report_cache_summary(session),
    }
    count = _session_report_count(session)
    if count:
        payload["report_count"] = int(count)
        payload["multi_report"] = count > 1
    if intent:
        payload["intent"] = intent
    return payload


def report_cache_summary(session: ReportSession) -> dict[str, Any]:
    """Return path-redacted cache/backend state for a loaded report session.

    This is deliberately descriptive, not a cache-control API. It helps agents
    explain first-run latency and confirm that native reports are analyzed
    through the Parquet/DuckDB path without exposing local filesystem paths.
    """

    count = _session_report_count(session)
    payload: dict[str, Any] = {
        "paths_hidden": True,
        "source_kind": session.source,
        "report_count": int(count) if count else 1,
    }
    if session.source in {"native_report", "directory_nsys_reports"}:
        payload.update(
            {
                "input_kind": (
                    "native_report_directory"
                    if session.source == "directory_nsys_reports"
                    else "native_report"
                ),
                "backend": "parquet_duckdb",
                "state": "deferred_until_query_or_context",
            }
        )
        return payload
    if session.source in {"nsys_export_parquet_duckdb", "directory_nsys_reports_duckdb"}:
        payload.update(
            {
                "input_kind": (
                    "native_report_directory"
                    if session.source == "directory_nsys_reports_duckdb"
                    else "native_report"
                ),
                "backend": "parquet_duckdb",
                "state": "ready",
            }
        )
    elif session.sqlite_path:
        payload.update({"input_kind": "advanced_sqlite", "backend": "sqlite", "state": "advanced_input"})
    elif session.duckdb_path:
        payload.update({"input_kind": "advanced_tabular", "backend": "duckdb", "state": "ready"})
    else:
        payload.update({"input_kind": "unknown", "backend": "unknown", "state": "unknown"})
    if session.duckdb_path:
        payload["cache_artifact_label"] = session.duckdb_path.name
        payload["cache_artifact_ready"] = session.duckdb_path.is_file()
    if session.parquet_root:
        payload["parquet_export_label"] = session.parquet_root.name
    if session.cache_events:
        payload["diagnostics"] = [dict(event) for event in session.cache_events]
    return payload


def _session_report_count(session: ReportSession) -> int:
    return int(session.report_count or len(session.multi_reports) or 1)


def capabilities_from_tables(tables: set[str]) -> dict[str, bool]:
    """Map raw table presence to agent-actionable report capabilities."""

    upper = upper_table_names(tables)
    return {
        "has_cuda_kernels": TABLE_CUDA_KERNEL in upper,
        "has_cuda_api": TABLE_CUDA_RUNTIME in upper,
        "has_cuda_memcpy": TABLE_CUDA_MEMCPY in upper,
        "has_cuda_memset": TABLE_CUDA_MEMSET in upper,
        "has_cuda_sync": TABLE_CUDA_SYNC in upper,
        "has_cuda_graphs": bool(CUDA_GRAPH_TABLES & upper),
        "has_nvtx": TABLE_NVTX_EVENTS in upper,
        "has_gpu_metrics": {TABLE_GPU_METRICS, TABLE_TARGET_INFO_GPU_METRICS}.issubset(upper),
        "has_cpu_sampling": bool(CPU_SAMPLING_TABLES & upper),
        "has_cpu_scheduling": "SCHED_EVENTS" in upper,
        "has_nic_metrics": "NET_NIC_METRIC" in upper,
        "has_mpi": any("MPI" in table for table in upper),
        "has_nccl": any("NCCL" in table for table in upper),
        "has_diagnostics": TABLE_DIAGNOSTIC_EVENT in upper,
        "has_gpu_metadata": TABLE_TARGET_INFO_GPU in upper,
        "has_dx12": TABLE_DX12_API in upper,
        "has_dx11": TABLE_DX11_API in upper,
        "has_dxgi": TABLE_DXGI_API in upper,
        "has_vulkan": TABLE_VULKAN_API in upper,
        "has_opengl": TABLE_OPENGL_API in upper,
        "has_dx12_workload": TABLE_DX12_WORKLOAD in upper,
        "has_etw": TABLE_ETW_EVENTS in upper,
        "has_wddm": any(table.startswith(WDDM_TABLE_PREFIX) for table in upper),
        "has_graphics": bool(GRAPHICS_API_TABLES & upper),
    }


def capability_guidance(capabilities: dict[str, bool]) -> list[str]:
    """Short evidence-routing and missing-evidence notes that help the model avoid unsupported claims and use appropriate methods."""

    notes: list[str] = []
    if not capabilities.get("has_gpu_metrics"):
        notes.append("GPU hardware utilization requires GPU_METRICS/TARGET_INFO_GPU_METRICS; do not infer SM utilization from kernels alone.")
    if not capabilities.get("has_nvtx"):
        notes.append("NVTX range/iteration attribution requires NVTX_EVENTS; absence means the capture lacks NVTX evidence.")
    if not capabilities.get("has_cpu_sampling"):
        notes.append("CPU hotspot/callstack analysis requires CPU sampling tables; absence means recapture or another evidence source is needed.")
    if not capabilities.get("has_cuda_kernels") and not capabilities.get("has_cuda_graphs"):
        notes.append("CUDA kernel/graph timing evidence is not present in this report context.")
    if capabilities.get("has_graphics") or capabilities.get("has_etw"):
        notes.append(
            "For graphics frame timing or stutter analysis, use the report-fact intents"
            " 'frame_summary' (locate a frame's window) then 'frame_scan'"
            " (in-window ETW/WDDM evidence), passing --frame <N>,"
            " rather than hand-writing SQL."
        )
    has_sched = capabilities.get("has_cpu_scheduling")
    has_sampling = capabilities.get("has_cpu_sampling")
    note = ""
    if has_sched:
        note += (
            "For per-thread CPU time or blocking, use the report-fact intent"
            " 'thread_scheduling' (on-CPU vs blocked time and dominant block reason,"
            " --frame <N> to scope to a frame)"
        )
        if has_sampling:
            note += (
                ". Then "
            )
        else:
            note += (
                ", rather than hand-writing SCHED_EVENTS SQL."
            )
    if has_sampling:
        note += (
            "use the report-fact intent 'callstack_summary"
            " --metric <globalTid>' (leaf-symbol hotspots and blocked stacks),"
            " rather than hand-writing callchain SQL."
        )
    if note:
        notes.append(note)
    return notes


def stable_row_key(kind: str, *parts: Any) -> str:
    """Build a stable, compact row key from public identity fields.

    The key is deterministic across runs for the same report-derived identity
    but avoids copying long kernel/API names into the key itself.
    """

    cleaned = [str(part) for part in parts if part not in (None, "")]
    if not cleaned:
        return _slug(kind)
    digest = hashlib.sha256("\x1f".join(cleaned).encode("utf-8", errors="replace")).hexdigest()[:12]
    return f"{_slug(kind)}:{digest}"


def add_key(row: dict[str, Any], kind: str, *parts: Any) -> dict[str, Any]:
    """Return a row copy with a stable model-facing ``key`` field."""

    if "key" in row:
        return row
    keyed = dict(row)
    keyed["key"] = stable_row_key(kind, *parts)
    return keyed


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_.:-]+", "-", value.strip().lower()).strip("-")
    return slug or "row"
