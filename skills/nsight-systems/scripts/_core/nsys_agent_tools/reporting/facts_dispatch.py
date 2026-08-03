"""Dispatch model-selected report fact intents to deterministic fact helpers."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .connection import connect_session
from .errors import _safe_error_text
from .evidence import report_evidence
from .facts_callstack import _callstack_summary
from .facts_cuda_activity import _activity_summary
from .facts_cuda_kernel import _kernel_summary, _kernel_variance
from .facts_cuda_memory import _memory_summary
from .facts_cuda_ncu import _nsight_compute_handoff_candidates
from .facts_cuda_runtime import _runtime_summary
from .facts_cuda_timeline import _timeline_summary
from .facts_gpu import _gpu_device_fact
from .facts_graphics_api import (
    _graphics_api_distribution,
    _graphics_api_summary,
    _graphics_api_timeline,
)
from .facts_graphics_frame import _frame_scan, _frame_summary
from .facts_nccl import _nccl_distribution
from .facts_scheduling import _thread_scheduling_summary
from .load import load_native_report_duckdb
from .multi_report import load_multi_report_duckdb
from .schema import (
    NCCL_TABLE_PATTERN,
    TABLE_COMPOSITE_EVENTS,
    TABLE_CUDA_GRAPH_TRACE,
    TABLE_CUDA_KERNEL,
    TABLE_CUDA_MEMCPY,
    TABLE_CUDA_MEMSET,
    TABLE_CUDA_RUNTIME,
    TABLE_DX12_API,
    TABLE_DX12_WORKLOAD,
    TABLE_DXGI_API,
    TABLE_ENUM_CUDA_MEM_KIND,
    TABLE_ENUM_CUDA_MEMCPY_OPER,
    TABLE_ENUM_SCHEDULING_THREAD_BLOCK,
    TABLE_ETW_EVENTS,
    TABLE_GENERIC_EVENT_TYPES,
    TABLE_GPU_CONTEXT_SWITCH,
    TABLE_GPU_METRICS,
    TABLE_META_DATA_EXPORT,
    TABLE_MPI_COLLECTIVES,
    TABLE_NVTX_EVENTS,
    TABLE_OPENGL_API,
    TABLE_OPENGL_WORKLOAD,
    TABLE_OSRT_API,
    TABLE_SAMPLING_CALLCHAINS,
    TABLE_SCHED_EVENTS,
    TABLE_STRING_IDS,
    TABLE_TARGET_INFO_CUDA_DEVICE,
    TABLE_TARGET_INFO_GPU,
    TABLE_TARGET_INFO_GPU_METRICS,
    TABLE_THREAD_NAMES,
    TABLE_VULKAN_API,
    TABLE_VULKAN_WORKLOAD,
    TABLE_WDDM_DMA_PACKET_START,
    TABLE_WDDM_EVICT_ALLOCATION,
    TABLE_WDDM_PAGING_QUEUE_PACKET_INFO,
)
from .sql_utils import _install_query_timeout, _query_dicts
from .table_shape import attach_table_view
from .types import ReportSession

if TYPE_CHECKING:
    from .runtime import ReportRuntime

# Caps how many ranked rows a handler returns (kernels, API calls, threads, hotspots, and so on).
# Values above the max are clamped before dispatch.
_FACT_MAX_ROWS = 50


FactHandler = (
    Callable[[Any, set[str], ReportSession, bool, str, int, str], dict[str, Any]]
    | Callable[
        [Any, set[str], ReportSession, bool, str, int, str, int | None],
        dict[str, Any],
    ]
)


@dataclass(frozen=True)
class FactSpec:
    """Declarative mapping from fact intent aliases to deterministic handlers."""

    intents: tuple[str, ...]
    handler: FactHandler
    evidence_intent: str
    required_table: str | None = None
    guidance: str = ""
    export_tables: tuple[str, ...] = ()
    options: tuple[tuple[str, str], ...] = ()
    availability_groups: tuple[tuple[str, ...], ...] = ()
    availability_patterns: tuple[str, ...] = ()

    @property
    def canonical_intent(self) -> str:
        return self.evidence_intent

    @property
    def aliases(self) -> tuple[str, ...]:
        return tuple(intent for intent in self.intents if intent != self.canonical_intent)

    def is_available(self, tables: set[str]) -> bool:
        if self.required_table and self.required_table not in tables:
            return False
        if not self.availability_groups and not self.availability_patterns:
            return True
        if any(set(group) <= tables for group in self.availability_groups):
            return True
        return any(
            re.fullmatch(pattern, table, flags=re.IGNORECASE)
            for pattern in self.availability_patterns
            for table in tables
        )

    def availability_requirements(
        self,
        tables: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Return declarative table requirements, optionally with confirmed gaps."""

        requirements: list[dict[str, Any]] = []
        if self.required_table and (tables is None or self.required_table not in tables):
            required: dict[str, Any] = {
                "kind": "all_of_tables",
                "tables": [self.required_table],
            }
            if tables is not None:
                required["missing_tables"] = [self.required_table]
            requirements.append(required)
        if self.availability_groups or self.availability_patterns:
            alternatives_available = tables is not None and (
                any(set(group) <= tables for group in self.availability_groups)
                or any(
                    re.fullmatch(pattern, table, flags=re.IGNORECASE)
                    for pattern in self.availability_patterns
                    for table in tables
                )
            )
            if not alternatives_available:
                alternatives: dict[str, Any] = {
                    "kind": "any_complete_group",
                    "table_groups": [list(group) for group in self.availability_groups],
                    "table_patterns": list(self.availability_patterns),
                }
                if tables is not None:
                    alternatives["missing_by_group"] = [
                        [table for table in group if table not in tables]
                        for group in self.availability_groups
                    ]
                requirements.append(alternatives)
        return requirements


_GRAPHICS_API_EXPORT_TABLES = (
    TABLE_DX12_API,
    TABLE_DX12_WORKLOAD,
    TABLE_VULKAN_API,
    TABLE_VULKAN_WORKLOAD,
    TABLE_OPENGL_API,
    TABLE_OPENGL_WORKLOAD,
    TABLE_DXGI_API,
    TABLE_STRING_IDS,
)


def _gpu_devices_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    del metric, intent
    return _gpu_device_fact(
        con,
        tables,
        max_rows,
        multi_report=multi_report,
        report_count=session.report_count or len(session.multi_reports) or 1,
        display_label=session.display_label,
    )


def _activity_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    del session, multi_report, metric, intent
    return _activity_summary(con, tables, max_rows)


def _kernel_summary_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    del session, multi_report, intent
    return _kernel_summary(con, tables, metric or "max_single_duration", max_rows)


def _runtime_summary_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    del session, multi_report, intent
    return _runtime_summary(con, tables, metric, max_rows)


def _nvtx_presence_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    del session, multi_report, metric, max_rows
    if TABLE_NVTX_EVENTS not in tables:
        return {
            "ok": True,
            "intent": intent,
            "event_count": 0,
            "note": f"{TABLE_NVTX_EVENTS} is not present in this report.",
        }
    rows = _query_dicts(
        con,
        f'SELECT COUNT(*) AS event_count FROM "{TABLE_NVTX_EVENTS}"',
        max_rows=1,
    )
    return {"ok": True, "intent": intent, **(rows[0] if rows else {"event_count": 0})}


def _memory_summary_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    del session, multi_report, intent
    return _memory_summary(con, tables, max_rows, metric)


def _timeline_summary_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    del session, metric, max_rows
    return _timeline_summary(con, tables, intent=intent, multi_report=multi_report)


def _kernel_variance_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    del session, multi_report, metric, max_rows, intent
    return _kernel_variance(con, tables)


def _nccl_distribution_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    del session, metric, max_rows, intent
    return _nccl_distribution(con, tables, multi_report=multi_report)


def _ncu_handoff_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    del session, multi_report, metric, intent
    return _nsight_compute_handoff_candidates(con, tables, max_rows)


def _frame_summary_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
    frame: int | None = None,
) -> dict[str, Any]:
    del session, metric
    return _frame_summary(
        con, tables, multi_report=multi_report, frame=frame, max_rows=max_rows, intent=intent
    )


def _frame_scan_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
    frame: int | None = None,
) -> dict[str, Any]:
    del session, metric
    return _frame_scan(
        con, tables, multi_report=multi_report, frame=frame, max_rows=max_rows, intent=intent
    )


def _graphics_api_summary_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
    frame: int | None = None,
) -> dict[str, Any]:
    del session, metric
    return _graphics_api_summary(
        con, tables, multi_report=multi_report, frame=frame, max_rows=max_rows, intent=intent
    )


def _graphics_api_distribution_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    del session
    return _graphics_api_distribution(
        con, tables, multi_report=multi_report, metric=metric, max_rows=max_rows, intent=intent
    )


def _graphics_api_timeline_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
) -> dict[str, Any]:
    del session
    return _graphics_api_timeline(
        con, tables, multi_report=multi_report, metric=metric, max_rows=max_rows, intent=intent
    )


def _thread_scheduling_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
    frame: int | None = None,
) -> dict[str, Any]:
    del session, metric
    return _thread_scheduling_summary(
        con, tables, multi_report=multi_report, frame=frame, max_rows=max_rows, intent=intent
    )


def _callstack_handler(
    con: Any,
    tables: set[str],
    session: ReportSession,
    multi_report: bool,
    metric: str,
    max_rows: int,
    intent: str,
    frame: int | None = None,
) -> dict[str, Any]:
    del session
    return _callstack_summary(
        con,
        tables,
        multi_report=multi_report,
        metric=metric,
        frame=frame,
        max_rows=max_rows,
        intent=intent,
    )


FACT_SPECS: tuple[FactSpec, ...] = (
    FactSpec(
        ("gpu_devices",),
        _gpu_devices_handler,
        "gpu_devices",
        required_table=TABLE_TARGET_INFO_GPU,
        guidance="Use gpu_devices or activity_summary to separate visible GPUs from GPUs with activity.",
        export_tables=(
            TABLE_TARGET_INFO_GPU,
            TABLE_TARGET_INFO_CUDA_DEVICE,
            TABLE_CUDA_KERNEL,
            TABLE_STRING_IDS,
        ),
    ),
    FactSpec(
        ("activity_summary", "report_activity", "per_report_activity"),
        _activity_handler,
        "activity_summary",
        guidance="Use activity_summary for per-report category coverage and active GPU attribution.",
        export_tables=(
            TABLE_CUDA_KERNEL,
            TABLE_CUDA_RUNTIME,
            TABLE_NVTX_EVENTS,
            TABLE_TARGET_INFO_GPU,
            TABLE_TARGET_INFO_CUDA_DEVICE,
            TABLE_STRING_IDS,
            TABLE_MPI_COLLECTIVES,
        ),
        availability_groups=(
            (TABLE_CUDA_KERNEL,),
            (TABLE_CUDA_RUNTIME,),
            (TABLE_NVTX_EVENTS,),
            (TABLE_TARGET_INFO_GPU,),
            (TABLE_MPI_COLLECTIVES,),
        ),
    ),
    FactSpec(
        ("kernel_summary",),
        _kernel_summary_handler,
        "kernel_summary",
        required_table=TABLE_CUDA_KERNEL,
        guidance=(
            "Use kernel_summary for launch counts, unique kernel names, total time, mean time, "
            "and longest single launch; use --metric max_single_duration for the longest launch."
        ),
        export_tables=(TABLE_CUDA_KERNEL, TABLE_STRING_IDS),
        options=(("metric", "optional; use max_single_duration for the longest launch"),),
    ),
    FactSpec(
        ("cuda_api_summary",),
        _runtime_summary_handler,
        "cuda_api_summary",
        required_table=TABLE_CUDA_RUNTIME,
        guidance="Use an unqualified cuda_api_summary for ambiguous API timing so total, mean, and longest-event interpretations stay visible.",
        export_tables=(TABLE_CUDA_RUNTIME, TABLE_STRING_IDS),
        options=(("metric", "optional; omit to preserve total, mean, and maximum interpretations"),),
    ),
    FactSpec(
        ("nvtx_presence",),
        _nvtx_presence_handler,
        "nvtx_presence",
        guidance="Use nvtx_presence for the exact NVTX_EVENTS row count.",
        export_tables=(TABLE_NVTX_EVENTS, TABLE_META_DATA_EXPORT),
    ),
    FactSpec(
        ("memcpy_summary",),
        _memory_summary_handler,
        "memcpy_summary",
        guidance="Use memcpy_summary with metric total_bytes for largest memory operation by byte volume.",
        export_tables=(
            TABLE_CUDA_MEMCPY,
            TABLE_CUDA_MEMSET,
            TABLE_ENUM_CUDA_MEMCPY_OPER,
            TABLE_ENUM_CUDA_MEM_KIND,
        ),
        options=(("metric", "optional; use total_bytes for byte-volume ranking"),),
        availability_groups=((TABLE_CUDA_MEMCPY,), (TABLE_CUDA_MEMSET,)),
    ),
    FactSpec(
        ("timeline_summary", "gpu_timeline", "idle_gaps", "gpu_utilization"),
        _timeline_summary_handler,
        "timeline_summary",
        required_table=TABLE_CUDA_KERNEL,
        guidance="Use timeline_summary for bounded kernel timeline coverage and idle-gap facts.",
        export_tables=(
            TABLE_CUDA_KERNEL,
            TABLE_GPU_METRICS,
            TABLE_TARGET_INFO_GPU_METRICS,
            TABLE_CUDA_GRAPH_TRACE,
        ),
    ),
    FactSpec(
        ("frame_summary", "frame_window", "graphics_frame_summary"),
        _frame_summary_handler,
        "frame_summary",
        guidance=(
            "Use frame_summary to locate a graphics frame's time window and per-frame CPU "
            "frame time (DXGI/Vulkan/OpenGL present rows, else DxgKrnl ETW Present); "
            "stutter is one use, but per-frame timing answers any frame-time question."
        ),
        export_tables=(
            TABLE_DXGI_API,
            TABLE_VULKAN_API,
            TABLE_OPENGL_API,
            TABLE_ETW_EVENTS,
            TABLE_GENERIC_EVENT_TYPES,
            TABLE_STRING_IDS,
        ),
        options=(("frame", "optional frame index"),),
        availability_groups=(
            (TABLE_DXGI_API, TABLE_STRING_IDS),
            (TABLE_VULKAN_API, TABLE_STRING_IDS),
            (TABLE_OPENGL_API, TABLE_STRING_IDS),
            (TABLE_ETW_EVENTS, TABLE_GENERIC_EVENT_TYPES),
        ),
    ),
    FactSpec(
        ("frame_scan", "graphics_frame_scan"),
        _frame_scan_handler,
        "frame_scan",
        guidance=(
            "Use frame_scan --frame <N> to scan a frame's window for ETW and WDDM event evidence "
            "against a baseline neighbor frame; it returns event counts (not a cause verdict)."
        ),
        export_tables=(
            TABLE_DXGI_API,
            TABLE_VULKAN_API,
            TABLE_OPENGL_API,
            TABLE_ETW_EVENTS,
            TABLE_GENERIC_EVENT_TYPES,
            TABLE_STRING_IDS,
            TABLE_WDDM_EVICT_ALLOCATION,
            TABLE_WDDM_PAGING_QUEUE_PACKET_INFO,
            TABLE_WDDM_DMA_PACKET_START,
            TABLE_GPU_CONTEXT_SWITCH,
        ),
        options=(("frame", "required frame index from frame_summary"),),
        availability_groups=((TABLE_ETW_EVENTS, TABLE_GENERIC_EVENT_TYPES, TABLE_STRING_IDS),),
    ),
    FactSpec(
        ("graphics_api_summary", "gfx_api_summary"),
        _graphics_api_summary_handler,
        "graphics_api_summary",
        guidance=(
            "Use graphics_api_summary for per-API DX12/Vulkan/OpenGL call timing (count, total/avg/"
            "max ms) ranked by total time; add --frame <N> to scope to a frame window (no nanosecond "
            "pasting) with each API's pct_of_frame, plus the paired GPU workload table."
        ),
        export_tables=_GRAPHICS_API_EXPORT_TABLES,
        options=(("frame", "optional frame index"),),
        availability_groups=(
            (TABLE_DX12_API, TABLE_STRING_IDS),
            (TABLE_VULKAN_API, TABLE_STRING_IDS),
            (TABLE_OPENGL_API, TABLE_STRING_IDS),
        ),
    ),
    FactSpec(
        ("graphics_api_distribution", "gfx_api_distribution"),
        _graphics_api_distribution_handler,
        "graphics_api_distribution",
        guidance=(
            "Use graphics_api_distribution for session-wide per-API call-duration percentiles "
            "(min/median/p95/p99/max) to separate steady-state cost from the tail; --metric "
            "<api_name> narrows to one API."
        ),
        export_tables=_GRAPHICS_API_EXPORT_TABLES,
        options=(("metric", "optional graphics API name"),),
        availability_groups=(
            (TABLE_DX12_API, TABLE_STRING_IDS),
            (TABLE_VULKAN_API, TABLE_STRING_IDS),
            (TABLE_OPENGL_API, TABLE_STRING_IDS),
        ),
    ),
    FactSpec(
        ("graphics_api_timeline", "gfx_api_timeline"),
        _graphics_api_timeline_handler,
        "graphics_api_timeline",
        guidance=(
            "Use graphics_api_timeline --metric <api_name> to detect back-to-back serialized "
            "chaining of one API's calls (the in-order command-queue pattern behind tiled-resource "
            "stutter)."
        ),
        export_tables=_GRAPHICS_API_EXPORT_TABLES,
        options=(("metric", "required graphics API name"),),
        availability_groups=(
            (TABLE_DX12_API, TABLE_STRING_IDS),
            (TABLE_VULKAN_API, TABLE_STRING_IDS),
            (TABLE_OPENGL_API, TABLE_STRING_IDS),
        ),
    ),
    FactSpec(
        ("thread_scheduling", "blocking_waits", "sched_summary"),
        _thread_scheduling_handler,
        "thread_scheduling",
        required_table=TABLE_SCHED_EVENTS,
        guidance=(
            "Use thread_scheduling for per-thread on-CPU and blocked-time upper bounds, with "
            "`*_confirmed_pct` as confidence in each bound: near 100% means confirmed "
            "sched-in/sched-out pairs, while a low value means missing transitions inflated "
            "the upper bound. It also reports the dominant block reason (the fence-wait / "
            "lock-contention / preemption distinction) and top OSRT_API blocking waits (e.g. "
            "`WaitForSingleObjectEx` on Windows, `pthread_cond_wait` on Linux); add --frame <N> "
            "to scope to one frame window."
        ),
        export_tables=(
            TABLE_SCHED_EVENTS,
            TABLE_ENUM_SCHEDULING_THREAD_BLOCK,
            TABLE_OSRT_API,
            TABLE_THREAD_NAMES,
            TABLE_STRING_IDS,
            TABLE_DXGI_API,
            TABLE_VULKAN_API,
            TABLE_OPENGL_API,
            TABLE_ETW_EVENTS,
            TABLE_GENERIC_EVENT_TYPES,
        ),
        options=(("frame", "optional frame index"),),
    ),
    FactSpec(
        ("callstack_summary", "thread_callstack", "hotspots"),
        _callstack_handler,
        "callstack_summary",
        required_table=TABLE_SAMPLING_CALLCHAINS,
        guidance=(
            "Use callstack_summary for leaf-symbol hotspots (cpuCycles=1 periodic samples = where "
            "time goes) and blocked_stacks (cpuCycles=0 scheduling event callstacks = why a thread "
            "came off CPU, e.g. a fence/wait call). Pass --metric <globalTid> (from thread_scheduling) "
            "to attribute one thread and --frame <N> to restrict samples to that frame window; "
            "without a metric symbols mix across threads."
        ),
        export_tables=(
            TABLE_SAMPLING_CALLCHAINS,
            TABLE_COMPOSITE_EVENTS,
            TABLE_STRING_IDS,
            TABLE_THREAD_NAMES,
        ),
        options=(
            ("metric", "optional globalTid returned by thread_scheduling"),
            ("frame", "optional frame index"),
        ),
        availability_groups=(
            (TABLE_SAMPLING_CALLCHAINS, TABLE_COMPOSITE_EVENTS, TABLE_STRING_IDS),
        ),
    ),
    FactSpec(
        ("kernel_variance", "duration_variance"),
        _kernel_variance_handler,
        "kernel_variance",
        required_table=TABLE_CUDA_KERNEL,
        guidance="Use kernel_variance for kernel-duration spread and outlier evidence.",
        export_tables=(TABLE_CUDA_KERNEL,),
    ),
    FactSpec(
        ("nccl_distribution", "nccl_summary"),
        _nccl_distribution_handler,
        "nccl_distribution",
        guidance="Use nccl_distribution to distinguish NCCL event-table evidence from CUDA kernel names that contain nccl.",
        export_tables=(NCCL_TABLE_PATTERN, TABLE_CUDA_KERNEL, TABLE_STRING_IDS),
        availability_groups=((TABLE_CUDA_KERNEL,),),
        availability_patterns=(NCCL_TABLE_PATTERN,),
    ),
    FactSpec(
        ("nsight_compute_handoff", "nsight_compute_candidates"),
        _ncu_handoff_handler,
        "nsight_compute_handoff",
        required_table=TABLE_CUDA_KERNEL,
        guidance="Use nsight_compute_handoff for candidate kernels for separate Nsight Compute inspection.",
        export_tables=(TABLE_CUDA_KERNEL, TABLE_STRING_IDS),
    ),
)

_FACT_BY_INTENT = {intent: spec for spec in FACT_SPECS for intent in spec.intents}

_GRAPHICS_WORKFLOW_SCHEMA = "nsys-graphics-convergence-v1"
_GRAPHICS_WORKFLOW_ID = "graphics_frame_root_cause"
_GRAPHICS_CONVERGENCE_REQUIREMENTS = (
    "magnitude_match",
    "temporal_order",
    "entity_attribution",
)
_GRAPHICS_WORKFLOW_ROLES = {
    "frame_summary": "frame_selection",
    "frame_scan": "corroborating",
    "graphics_api_summary": "magnitude_evidence",
    "thread_scheduling": "thread_mechanism",
    "callstack_summary": "entity_attribution",
}
_GRAPHICS_WORKFLOW_REMAINDER = {
    "frame_summary": ("graphics_api_summary", "thread_scheduling", "callstack_summary"),
    "frame_scan": ("graphics_api_summary", "thread_scheduling", "callstack_summary"),
    "graphics_api_summary": ("thread_scheduling", "callstack_summary"),
    "thread_scheduling": ("callstack_summary",),
    "callstack_summary": (),
}
def supported_fact_intents() -> tuple[str, ...]:
    """Return stable fact intents accepted by report-fact adapters."""

    return ("report_inventory", *sorted(_FACT_BY_INTENT))


def fact_catalog(tables: set[str] | None = None) -> list[dict[str, Any]]:
    """Return canonical, model-facing fact routes generated from ``FACT_SPECS``."""

    catalog: list[dict[str, Any]] = [
        {
            "intent": "report_inventory",
            "aliases": [],
            "options": {},
            "guidance": "Use report_inventory for report labels, tables, and available capabilities.",
        }
    ]
    for spec in FACT_SPECS:
        if tables is not None and not spec.is_available(tables):
            continue
        catalog.append(
            {
                "intent": spec.canonical_intent,
                "aliases": list(spec.aliases),
                "options": dict(spec.options),
                "guidance": spec.guidance,
            }
        )
    return catalog


def available_fact_intents(tables: set[str]) -> list[str]:
    """Return canonical fact intents supported by the loaded report tables."""

    return [entry["intent"] for entry in fact_catalog(tables)]


def fact_prompt_guidance() -> str:
    """Return compact model-facing guidance generated from fact specs."""

    return " ".join(spec.guidance for spec in FACT_SPECS if spec.guidance)


def fact(
    runtime: ReportRuntime,
    session: ReportSession,
    *,
    intent: str,
    metric: str = "",
    max_rows: int = 10,
    frame: int | None = None,
) -> dict[str, Any]:
    """Return deterministic common report facts."""

    max_rows = max(1, min(int(max_rows or 10), _FACT_MAX_ROWS))
    intent = intent.strip().lower()
    metric = metric.strip().lower()
    multi_report_input = bool(session.multi_reports)
    evidence_session = session
    if intent == "report_inventory":
        payload = {"ok": True, "intent": intent, **runtime.context(session)}
        payload.setdefault(
            "evidence",
            report_evidence(evidence_session, command="nsys_report_fact", intent=intent),
        )
        return payload
    spec = _FACT_BY_INTENT.get(intent)
    if spec is None:
        return {"ok": False, "intent": intent, "metric": metric, "error": "Unsupported report fact intent."}
    if session.multi_reports:
        session = load_multi_report_duckdb(runtime, session, table_patterns=spec.export_tables)
        evidence_session = session
    elif session.source == "native_report":
        session = load_native_report_duckdb(
            runtime,
            session.input_path,
            table_patterns=spec.export_tables,
        )
        evidence_session = session
    tables = set(runtime.tables(session))
    if spec.required_table and spec.required_table not in tables:
        return {"ok": False, "intent": intent, "error": f"{spec.required_table} is not present in this report."}
    try:
        with connect_session(session) as con:
            _install_query_timeout(con, 10.0)
            handler_args = (
                con,
                tables,
                session,
                multi_report_input or session.report_count > 1,
                metric,
                max_rows,
                intent,
            )
            handles_frame = any(name == "frame" for name, _ in spec.options)
            if frame is None or not handles_frame:
                payload = spec.handler(*handler_args)
            else:
                payload = spec.handler(*handler_args, frame=frame)
            return _with_fact_evidence(
                payload,
                evidence_session,
                intent=spec.evidence_intent,
                requested_frame=frame,
                available_tables=tables,
                inventory_complete=_table_inventory_complete(evidence_session),
            )
    except Exception as exc:  # noqa: BLE001 - return to model for repair/fallback
        return {"ok": False, "intent": intent, "metric": metric, "error": _safe_error_text(exc)}


def _table_inventory_complete(session: ReportSession) -> bool:
    return not any(bool(event.get("scoped")) for event in session.cache_events)


def _with_fact_evidence(
    payload: dict[str, Any],
    session: ReportSession,
    *,
    intent: str,
    requested_frame: int | None = None,
    available_tables: set[str] | None = None,
    inventory_complete: bool = True,
) -> dict[str, Any]:
    """Attach the common report-evidence block without changing failure text."""

    if payload.get("ok"):
        attach_table_view(payload)
        payload.setdefault("evidence", report_evidence(session, command="nsys_report_fact", intent=intent))
        workflow = _graphics_convergence_metadata(
            payload,
            intent=intent,
            requested_frame=requested_frame,
            available_tables=available_tables or set(),
            inventory_complete=inventory_complete,
        )
        if workflow is not None:
            payload.setdefault("analysis_workflow", workflow)
        elif capability := _fact_evidence_capability(payload, intent=intent):
            payload.setdefault("evidence_capability", capability)
    return payload


def _graphics_convergence_metadata(
    payload: dict[str, Any],
    *,
    intent: str,
    requested_frame: int | None,
    available_tables: set[str],
    inventory_complete: bool,
) -> dict[str, Any] | None:
    """Describe how one fact contributes to a graphics-frame root-cause chain."""

    role = _GRAPHICS_WORKFLOW_ROLES.get(intent)
    if role is None or not _graphics_workflow_active(
        intent,
        payload,
        requested_frame=requested_frame,
    ):
        return None
    frame = _workflow_frame(payload, requested_frame)
    followups = [
        _graphics_followup(
            next_intent,
            frame=frame,
            payload=payload,
            available_tables=available_tables,
            inventory_complete=inventory_complete,
        )
        for next_intent in _GRAPHICS_WORKFLOW_REMAINDER[intent]
    ]
    inputs: dict[str, int] = {}
    if frame is not None:
        inputs["frame"] = frame
    workflow = {
        "schema": _GRAPHICS_WORKFLOW_SCHEMA,
        "workflow_id": _GRAPHICS_WORKFLOW_ID,
        "stage": intent,
        "evidence_role": role,
        "causal_verdict": "insufficient",
        "inputs": inputs,
        "required_followups": followups,
        "convergence_requirements": list(_GRAPHICS_CONVERGENCE_REQUIREMENTS),
    }
    return workflow


def _graphics_workflow_active(
    intent: str,
    payload: dict[str, Any],
    *,
    requested_frame: int | None,
) -> bool:
    if intent in {"frame_summary", "frame_scan"}:
        return True
    if intent in {"graphics_api_summary", "thread_scheduling"}:
        return requested_frame is not None or isinstance(payload.get("window"), dict)
    return False


def _fact_evidence_capability(
    payload: dict[str, Any],
    *,
    intent: str,
) -> dict[str, Any] | None:
    role = _GRAPHICS_WORKFLOW_ROLES.get(intent)
    if role is None:
        return None
    capability: dict[str, Any] = {
        "schema": "nsys-fact-evidence-capability-v1",
        "role": role,
        "scope": payload.get("scope", "session"),
        "causal_verdict": "insufficient",
    }
    if intent == "callstack_summary" and payload.get("scope") != "frame":
        capability["limitations"] = [
            "does_not_establish_frame_local_temporal_order",
        ]
    return capability


def _workflow_frame(payload: dict[str, Any], requested_frame: int | None) -> int | None:
    if requested_frame is not None and "requested_frame_error" not in payload:
        return requested_frame
    for key in ("requested_frame", "frame", "window"):
        value = payload.get(key)
        if isinstance(value, dict) and isinstance(value.get("frame_num"), int):
            return int(value["frame_num"])
    return None


def _graphics_followup(
    intent: str,
    *,
    frame: int | None,
    payload: dict[str, Any],
    available_tables: set[str],
    inventory_complete: bool,
) -> dict[str, Any]:
    followup: dict[str, Any] = {"intent": intent}
    if intent in {"graphics_api_summary", "thread_scheduling"}:
        if frame is not None:
            followup["args"] = {"frame": frame}
        else:
            followup["arg_sources"] = {
                "frame": "frame_summary.slowest_frames[].frame_num"
            }
    elif intent == "callstack_summary":
        followup["arg_sources"] = {
            "metric": (
                "thread_scheduling.threads_by_on_cpu_ms_upper_bound[].global_tid or "
                "thread_scheduling.threads_by_blocked_ms_upper_bound[].global_tid"
            ),
        }
        selected_threads: list[dict[str, Any]] = []
        seen_global_tids: set[int] = set()
        candidate_lists = (
            payload.get("threads_by_on_cpu_ms_upper_bound", []),
            payload.get("threads_by_blocked_ms_upper_bound", []),
        )
        for index in range(2):
            for threads in candidate_lists:
                if index >= len(threads):
                    continue
                thread = threads[index]
                if not isinstance(thread, dict):
                    continue
                global_tid = thread.get("global_tid")
                if not isinstance(global_tid, int) or global_tid in seen_global_tids:
                    continue
                seen_global_tids.add(global_tid)
                selected_threads.append(thread)
        candidates = [
            {
                "global_tid": int(thread["global_tid"]),
                "thread_name": thread.get("thread_name"),
                "args": {
                    "metric": str(thread["global_tid"]),
                    **({"frame": frame} if frame is not None else {}),
                },
            }
            for thread in selected_threads
            if isinstance(thread, dict) and isinstance(thread.get("global_tid"), int)
        ]
        if candidates:
            followup["candidate_args"] = candidates
    availability, requirements = _graphics_followup_availability(
        intent,
        available_tables,
        inventory_complete=inventory_complete,
    )
    followup["availability"] = availability
    if availability == "unavailable":
        followup["missing_requirements"] = requirements
        followup["on_unavailable"] = {
            "action": "state_missing_capture_data",
            "allow_ad_hoc_sql_fallback": False,
        }
    elif availability == "unknown":
        followup["availability_requirements"] = requirements
        followup["on_unknown"] = {
            "action": "run_followup_fact_directly",
        }
    return followup


def _graphics_followup_availability(
    intent: str,
    available_tables: set[str],
    *,
    inventory_complete: bool,
) -> tuple[str, list[dict[str, Any]]]:
    spec = _FACT_BY_INTENT[intent]
    if spec.is_available(available_tables):
        return "available", []
    if not inventory_complete:
        return "unknown", spec.availability_requirements()
    return "unavailable", spec.availability_requirements(available_tables)
