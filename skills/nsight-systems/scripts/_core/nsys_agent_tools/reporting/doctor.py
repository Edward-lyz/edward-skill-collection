"""Deterministic report health checks used before diagnostic answers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .gpu_mapping import active_gpu_rows as _active_gpu_rows
from .schema import (
    SYNTHETIC_REPORT_LABEL,
    TABLE_CUDA_KERNEL,
    TABLE_CUDA_RUNTIME,
    TABLE_DIAGNOSTIC_EVENT,
    TABLE_GPU_METRICS,
    TABLE_NVTX_EVENTS,
    TABLE_OSRT_API,
    TABLE_TARGET_INFO_GPU,
    TABLE_TARGET_INFO_GPU_METRICS,
    TABLE_TARGET_INFO_PROCESS,
)
from .sql_utils import _existing_columns, _query_dicts, _quote_identifier, _scalar

FLAT_METRIC_SERIES_LIMIT = 512
COMMON_ACTIVITY_TABLES = (
    TABLE_CUDA_RUNTIME,
    TABLE_CUDA_KERNEL,
    TABLE_NVTX_EVENTS,
    TABLE_OSRT_API,
)
IMPORTANT_TABLES = (
    TABLE_TARGET_INFO_GPU,
    TABLE_CUDA_RUNTIME,
    TABLE_CUDA_KERNEL,
    TABLE_NVTX_EVENTS,
    TABLE_GPU_METRICS,
    TABLE_TARGET_INFO_GPU_METRICS,
    TABLE_DIAGNOSTIC_EVENT,
)

DOCTOR_STATUS_ORDER = {"pass": 0, "info": 1, "warn": 2, "fail": 3}
DOCTOR_STATUS_BY_SCORE = {score: status for status, score in DOCTOR_STATUS_ORDER.items()}


@dataclass(frozen=True)
class DoctorThresholds:
    """Small set of configurable thresholds for generic report-health checks.

    These defaults are deliberately conservative and product-generic.  Domain
    workflows such as DLB/NIM can layer stricter thresholds in companion skills
    without changing official Nsight Systems report semantics.
    """

    runtime_kernel_match_pass: float = 0.99
    runtime_kernel_match_warn: float = 0.90
    flat_metric_warn_ratio: float = 0.80
    min_metric_samples_for_flatness: int = 3
    short_timeline_ns: int = 100_000_000
    large_kernel_gap_ns: int = 1_000_000_000


@dataclass(frozen=True)
class DoctorCheckSpec:
    """Registry entry for one deterministic report-health check."""

    name: str
    required_tables: tuple[str, ...]
    run: Callable[[Any, set[str], DoctorThresholds], dict[str, Any]]


def _doctor_check(name: str, status: str, summary: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "status": status, "summary": summary, "details": details or {}}


def run_doctor_checks(
    con: Any,
    tables: set[str],
    thresholds: DoctorThresholds | None = None,
) -> list[dict[str, Any]]:
    """Run the supported generic report doctor checks.

    The registry keeps the doctor extensible without turning it into a large
    branching function.  Each check still returns plain JSON so the CLI and
    BYO script entry points share one contract.
    """

    active_thresholds = thresholds or DoctorThresholds()
    checks: list[dict[str, Any]] = []
    for spec in DOCTOR_CHECKS:
        check = spec.run(con, tables, active_thresholds)
        _annotate_required_tables(check, spec.required_tables, tables)
        checks.append(check)
    return checks


def doctor_worst_status(checks: list[dict[str, Any]]) -> str:
    """Return the worst status from a list of doctor check payloads."""

    score = max(
        (
            DOCTOR_STATUS_ORDER.get(str(check.get("status")), DOCTOR_STATUS_ORDER["info"])
            for check in checks
        ),
        default=DOCTOR_STATUS_ORDER["info"],
    )
    return DOCTOR_STATUS_BY_SCORE[score]


def _annotate_required_tables(
    check: dict[str, Any],
    required_tables: tuple[str, ...],
    available_tables: set[str],
) -> None:
    """Attach missing required-table metadata without changing check semantics."""

    if not required_tables:
        return
    missing = [table for table in required_tables if table not in available_tables]
    if not missing:
        return
    details = dict(check.get("details") or {})
    details["missing_required_tables"] = missing
    check["details"] = details


def _doctor_table_inventory(con: Any, tables: set[str], _thresholds: DoctorThresholds) -> dict[str, Any]:
    important = {}
    for table in IMPORTANT_TABLES:
        if table in tables:
            important[table] = _scalar(con, "SELECT COUNT(*) FROM " + _quote_identifier(table))
    if not tables:
        return _doctor_check("table_inventory", "fail", "No tables were found in the report export.")
    if not any(name in tables for name in COMMON_ACTIVITY_TABLES):
        return _doctor_check(
            "table_inventory",
            "warn",
            f"Found {len(tables)} tables, but no common activity tables were present.",
            {"important_tables": important},
        )
    empty = [name for name, count in important.items() if count == 0]
    status = "warn" if empty else "pass"
    summary = f"Found {len(tables)} tables."
    if empty:
        summary += " Some important tables are empty: " + ", ".join(empty) + "."
    return _doctor_check("table_inventory", status, summary, {"important_tables": important})


def _doctor_gpu_consistency(con: Any, tables: set[str], _thresholds: DoctorThresholds) -> dict[str, Any]:
    if TABLE_TARGET_INFO_GPU not in tables:
        return _doctor_check("gpu_device_consistency", "warn", f"{TABLE_TARGET_INFO_GPU} is not present.")
    gpu_columns = _existing_columns(con, TABLE_TARGET_INFO_GPU)
    id_column = "id" if "id" in gpu_columns else None
    if not id_column:
        return _doctor_check("gpu_device_consistency", "warn", "TARGET_INFO_GPU has no id column.")
    gpus = _gpu_mapping(con, gpu_columns)
    registered = {int(row["id"]) for row in gpus if row.get("id") is not None}
    active_rows: list[dict[str, Any]] = []
    if TABLE_CUDA_KERNEL in tables and "deviceId" in _existing_columns(con, TABLE_CUDA_KERNEL):
        active_rows = _active_gpu_rows(con, tables, max_rows=128)
    active = {
        int(row["physical_gpu_id"])
        for row in active_rows
        if row.get("physical_gpu_id") is not None
    }
    unknown = sorted(active - registered)
    idle = sorted(registered - active) if active else []
    if unknown:
        return _doctor_check(
            "gpu_device_consistency",
            "fail",
            f"Kernel activity references GPU device ids not present in {TABLE_TARGET_INFO_GPU}.",
            {
                "logical_to_physical_gpu_mapping": gpus,
                "kernel_device_activity": active_rows,
                "active_physical_gpu_ids": sorted(active),
                "unknown_device_ids": unknown,
            },
        )
    if not active:
        return _doctor_check(
            "gpu_device_consistency",
            "warn",
            "GPU metadata exists, but no kernel device activity was found.",
            {"logical_to_physical_gpu_mapping": gpus},
        )
    status = "pass"
    summary = "GPU metadata and kernel device ids are consistent."
    if any(row.get("gpu_id_mapping_source") != "identity" for row in active_rows):
        summary += " CUDA logical device ids were mapped to physical GPU ids before comparison."
    if idle:
        summary += " Some registered GPUs had no kernel activity; this can be normal when metadata lists all visible GPUs."
    return _doctor_check(
        "gpu_device_consistency",
        status,
        summary,
        {
            "logical_to_physical_gpu_mapping": gpus,
            "kernel_device_activity": active_rows,
            "active_physical_gpu_ids": sorted(active),
            "registered_without_kernel_activity": idle,
        },
    )


def _gpu_mapping(con: Any, gpu_columns: set[str]) -> list[dict[str, Any]]:
    visible_columns = [
        SYNTHETIC_REPORT_LABEL,
        "id",
        "name",
        "busLocation",
        "chipName",
        "computeMajor",
        "computeMinor",
        "uuid",
    ]
    selected = [column for column in visible_columns if column in gpu_columns]
    if not selected:
        return []
    report_order = f"{SYNTHETIC_REPORT_LABEL}, " if SYNTHETIC_REPORT_LABEL in gpu_columns else ""
    sql = (
        "SELECT DISTINCT "
        + ", ".join(_quote_identifier(column) for column in selected)
        + f' FROM "{TABLE_TARGET_INFO_GPU}" ORDER BY '
        + report_order
        + "id LIMIT 128"
    )
    rows = _query_dicts(con, sql, max_rows=128)
    return [_rename_report_label(row) for row in rows]


def _rename_report_label(row: dict[str, Any]) -> dict[str, Any]:
    if SYNTHETIC_REPORT_LABEL not in row:
        return row
    return {
        "report_label": row[SYNTHETIC_REPORT_LABEL],
        **{k: v for k, v in row.items() if k != SYNTHETIC_REPORT_LABEL},
    }


def _doctor_runtime_kernel_correlation(con: Any, tables: set[str], thresholds: DoctorThresholds) -> dict[str, Any]:
    required = {TABLE_CUDA_KERNEL, TABLE_CUDA_RUNTIME}
    if not required.issubset(tables):
        return _doctor_check("runtime_kernel_correlation", "warn", "Runtime or kernel activity table is missing.")
    kernel_cols = _existing_columns(con, TABLE_CUDA_KERNEL)
    runtime_cols = _existing_columns(con, TABLE_CUDA_RUNTIME)
    if "correlationId" not in kernel_cols or "correlationId" not in runtime_cols:
        return _doctor_check("runtime_kernel_correlation", "warn", "Correlation id columns are not present.")
    graph_filter = ' AND (k.graphNodeId IS NULL OR k.graphNodeId = 0)' if "graphNodeId" in kernel_cols else ""
    rows = _query_dicts(
        con,
        f"""
        SELECT
          COUNT(*) AS correlatable_kernel_count,
          SUM(CASE WHEN r.correlationId IS NOT NULL THEN 1 ELSE 0 END) AS matched_kernel_count
        FROM "{TABLE_CUDA_KERNEL}" k
        LEFT JOIN "{TABLE_CUDA_RUNTIME}" r ON k.correlationId = r.correlationId
        WHERE k.correlationId IS NOT NULL {graph_filter}
        """,
        max_rows=1,
    )
    row = rows[0] if rows else {}
    total = int(row.get("correlatable_kernel_count") or 0)
    matched = int(row.get("matched_kernel_count") or 0)
    if total == 0:
        return _doctor_check("runtime_kernel_correlation", "info", "No correlatable non-graph kernels were found.")
    rate = matched / total
    status = "pass" if rate >= thresholds.runtime_kernel_match_pass else "warn" if rate >= thresholds.runtime_kernel_match_warn else "fail"
    return _doctor_check(
        "runtime_kernel_correlation",
        status,
        f"{matched}/{total} correlatable non-graph kernels matched a CUDA runtime call ({rate:.1%}).",
        {
            "correlatable_kernel_count": total,
            "matched_kernel_count": matched,
            "match_rate": rate,
            "pass_threshold": thresholds.runtime_kernel_match_pass,
            "warn_threshold": thresholds.runtime_kernel_match_warn,
        },
    )


def _doctor_nvtx_coverage(con: Any, tables: set[str], _thresholds: DoctorThresholds) -> dict[str, Any]:
    if TABLE_NVTX_EVENTS not in tables:
        return _doctor_check("nvtx_coverage", "warn", f"{TABLE_NVTX_EVENTS} is not present.")
    nvtx_count = _scalar(con, f'SELECT COUNT(*) FROM "{TABLE_NVTX_EVENTS}"') or 0
    runtime_threads = 0
    nvtx_threads = 0
    if TABLE_CUDA_RUNTIME in tables and "globalTid" in _existing_columns(con, TABLE_CUDA_RUNTIME):
        runtime_threads = _scalar(
            con,
            f'SELECT COUNT(DISTINCT globalTid) FROM "{TABLE_CUDA_RUNTIME}" WHERE globalTid IS NOT NULL',
        ) or 0
    if "globalTid" in _existing_columns(con, TABLE_NVTX_EVENTS):
        nvtx_threads = _scalar(
            con,
            f'SELECT COUNT(DISTINCT globalTid) FROM "{TABLE_NVTX_EVENTS}" WHERE globalTid IS NOT NULL',
        ) or 0
    if nvtx_count == 0:
        return _doctor_check("nvtx_coverage", "warn", "NVTX table is present but empty.", {"runtime_threads": runtime_threads})
    status = "warn" if runtime_threads and nvtx_threads < runtime_threads else "pass"
    summary = f"NVTX has {nvtx_count} event(s)."
    if status == "warn":
        summary += " Fewer NVTX threads than CUDA runtime threads were observed."
    return _doctor_check("nvtx_coverage", status, summary, {"runtime_threads": runtime_threads, "nvtx_threads": nvtx_threads})


def _doctor_metrics_completeness(con: Any, tables: set[str], _thresholds: DoctorThresholds) -> dict[str, Any]:
    if TABLE_TARGET_INFO_GPU_METRICS not in tables and TABLE_GPU_METRICS not in tables:
        return _doctor_check("metrics_completeness", "info", "GPU metrics tables are not present.")
    definitions = (
        _scalar(con, f'SELECT COUNT(*) FROM "{TABLE_TARGET_INFO_GPU_METRICS}"')
        if TABLE_TARGET_INFO_GPU_METRICS in tables
        else None
    )
    samples = (
        _scalar(con, f'SELECT COUNT(*) FROM "{TABLE_GPU_METRICS}"')
        if TABLE_GPU_METRICS in tables
        else None
    )
    if definitions and not samples:
        return _doctor_check(
            "metrics_completeness",
            "warn",
            "GPU metric definitions exist, but no GPU metric samples were captured.",
            {"metric_definition_count": definitions, "metric_sample_count": samples},
        )
    if samples and not definitions:
        return _doctor_check(
            "metrics_completeness",
            "warn",
            "GPU metric samples exist, but metric definitions are missing.",
            {"metric_definition_count": definitions, "metric_sample_count": samples},
        )
    return _doctor_check(
        "metrics_completeness",
        "pass" if samples else "info",
        "GPU metric table coverage was inspected.",
        {"metric_definition_count": definitions, "metric_sample_count": samples},
    )


def _doctor_flat_metrics(con: Any, tables: set[str], thresholds: DoctorThresholds) -> dict[str, Any]:
    if TABLE_GPU_METRICS not in tables:
        return _doctor_check("flat_metrics", "info", f"{TABLE_GPU_METRICS} is not present.")
    if (_scalar(con, f'SELECT COUNT(*) FROM "{TABLE_GPU_METRICS}"') or 0) == 0:
        return _doctor_check("flat_metrics", "info", f"{TABLE_GPU_METRICS} is present but empty.")
    rows = _query_dicts(
        con,
        f"""
        SELECT typeId, metricId, COUNT(*) AS sample_count, MIN(value) AS min_value, MAX(value) AS max_value
        FROM "{TABLE_GPU_METRICS}"
        GROUP BY typeId, metricId
        HAVING COUNT(*) >= ?
        LIMIT ?
        """,
        max_rows=FLAT_METRIC_SERIES_LIMIT,
        params=(thresholds.min_metric_samples_for_flatness, FLAT_METRIC_SERIES_LIMIT),
    )
    if not rows:
        return _doctor_check("flat_metrics", "info", "No metric series had enough samples to assess flatness.")
    flat = [row for row in rows if row.get("min_value") == row.get("max_value")]
    ratio = len(flat) / len(rows)
    status = "warn" if ratio >= thresholds.flat_metric_warn_ratio else "pass"
    return _doctor_check(
        "flat_metrics",
        status,
        f"{len(flat)}/{len(rows)} sampled GPU metric series were constant.",
        {
            "flat_series_count": len(flat),
            "checked_series_count": len(rows),
            "flat_ratio": ratio,
            "warn_threshold": thresholds.flat_metric_warn_ratio,
            "min_samples": thresholds.min_metric_samples_for_flatness,
        },
    )


def _doctor_timeline_health(con: Any, tables: set[str], thresholds: DoctorThresholds) -> dict[str, Any]:
    if TABLE_CUDA_KERNEL not in tables:
        return _doctor_check("timeline_health", "warn", "No kernel table is present to assess GPU timeline health.")
    count = _scalar(con, f'SELECT COUNT(*) FROM "{TABLE_CUDA_KERNEL}"') or 0
    if count == 0:
        return _doctor_check("timeline_health", "warn", "Kernel table is present but empty.")
    rows = _query_dicts(
        con,
        f"""
        SELECT MIN(start) AS start_ns, MAX("end") AS end_ns, COUNT(*) AS kernel_count
        FROM "{TABLE_CUDA_KERNEL}"
        """,
        max_rows=1,
    )
    row = rows[0] if rows else {}
    start = int(row.get("start_ns") or 0)
    end = int(row.get("end_ns") or 0)
    duration = max(0, end - start)
    gaps = _query_dicts(
        con,
        f"""
        WITH ordered AS (
          SELECT deviceId, start, "end", LAG("end") OVER (PARTITION BY deviceId ORDER BY start) AS prev_end
          FROM "{TABLE_CUDA_KERNEL}"
        )
        SELECT deviceId, start - prev_end AS gap_ns, prev_end AS gap_start_ns, start AS next_kernel_start_ns
        FROM ordered
        WHERE prev_end IS NOT NULL AND start > prev_end AND start - prev_end >= ?
        ORDER BY gap_ns DESC
        LIMIT 5
        """,
        max_rows=5,
        params=(thresholds.large_kernel_gap_ns,),
    )
    issues = []
    if duration < thresholds.short_timeline_ns:
        issues.append(f"kernel timeline duration is under {thresholds.short_timeline_ns / 1e6:g} ms")
    if gaps:
        issues.append(f"large GPU-kernel gaps over {thresholds.large_kernel_gap_ns / 1e9:g} second(s) were found")
    status = "warn" if issues else "pass"
    summary = f"Kernel timeline duration is {duration / 1e9:.6g}s across {count} kernel launch(es)."
    if issues:
        summary += " " + "; ".join(issues) + "."
    return _doctor_check(
        "timeline_health",
        status,
        summary,
        {
            "start_ns": start,
            "end_ns": end,
            "duration_ns": duration,
            "kernel_count": count,
            "large_gaps": gaps,
            "short_timeline_threshold_ns": thresholds.short_timeline_ns,
            "large_gap_threshold_ns": thresholds.large_kernel_gap_ns,
        },
    )


def _doctor_process_thread_summary(con: Any, tables: set[str], _thresholds: DoctorThresholds) -> dict[str, Any]:
    details: dict[str, Any] = {}
    if TABLE_CUDA_RUNTIME in tables and "globalTid" in _existing_columns(con, TABLE_CUDA_RUNTIME):
        details["cuda_runtime_thread_count"] = _scalar(
            con,
            f'SELECT COUNT(DISTINCT globalTid) FROM "{TABLE_CUDA_RUNTIME}" WHERE globalTid IS NOT NULL',
        )
    if TABLE_OSRT_API in tables and "globalTid" in _existing_columns(con, TABLE_OSRT_API):
        details["osrt_thread_count"] = _scalar(
            con,
            f'SELECT COUNT(DISTINCT globalTid) FROM "{TABLE_OSRT_API}" WHERE globalTid IS NOT NULL',
        )
    if TABLE_TARGET_INFO_PROCESS in tables:
        details["target_process_count"] = _scalar(
            con,
            f'SELECT COUNT(*) FROM "{TABLE_TARGET_INFO_PROCESS}"',
        )
    if not details:
        return _doctor_check("process_thread_summary", "info", "No process/thread summary tables were available.")
    return _doctor_check("process_thread_summary", "pass", "Process/thread summary was collected.", details)


DOCTOR_CHECKS: tuple[DoctorCheckSpec, ...] = (
    DoctorCheckSpec("table_inventory", (), _doctor_table_inventory),
    DoctorCheckSpec("gpu_device_consistency", (TABLE_TARGET_INFO_GPU,), _doctor_gpu_consistency),
    DoctorCheckSpec(
        "runtime_kernel_correlation",
        (TABLE_CUDA_KERNEL, TABLE_CUDA_RUNTIME),
        _doctor_runtime_kernel_correlation,
    ),
    DoctorCheckSpec("nvtx_coverage", (TABLE_NVTX_EVENTS,), _doctor_nvtx_coverage),
    DoctorCheckSpec(
        "metrics_completeness",
        (TABLE_GPU_METRICS, TABLE_TARGET_INFO_GPU_METRICS),
        _doctor_metrics_completeness,
    ),
    DoctorCheckSpec("flat_metrics", (TABLE_GPU_METRICS,), _doctor_flat_metrics),
    DoctorCheckSpec("timeline_health", (TABLE_CUDA_KERNEL,), _doctor_timeline_health),
    DoctorCheckSpec("process_thread_summary", (), _doctor_process_thread_summary),
)
