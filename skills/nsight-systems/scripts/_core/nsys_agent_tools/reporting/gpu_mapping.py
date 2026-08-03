"""GPU activity attribution helpers.

Nsight Systems reports can use two different GPU ID spaces:

* activity tables such as ``CUPTI_ACTIVITY_KIND_KERNEL`` store CUDA logical
  device IDs in ``deviceId``;
* metadata/metrics tables use physical GPU IDs from ``TARGET_INFO_GPU.id``.

``TARGET_INFO_CUDA_DEVICE`` records the logical-to-physical mapping when it is
available.  Keeping this logic in one place prevents each report fact/check from
reimplementing a slightly different join and accidentally attributing work to
the wrong GPU.
"""

from __future__ import annotations

import re
from typing import Any

from .evidence import add_key
from .schema import (
    SYNTHETIC_REPORT_COLUMNS,
    SYNTHETIC_REPORT_INDEX,
    SYNTHETIC_REPORT_LABEL,
    TABLE_CUDA_KERNEL,
    TABLE_STRING_IDS,
    TABLE_TARGET_INFO_CUDA_DEVICE,
    TABLE_TARGET_INFO_GPU,
)
from .sql_utils import _existing_columns, _query_dicts, _quote_identifier

_CUDA_VISIBLE_DEVICES_RE = re.compile(
    r"['\"]?CUDA_VISIBLE_DEVICES['\"]?\s*[:=]\s*['\"]?([^'\",\s}]+(?:,[^'\"}\s]+)*)['\"]?"
)
_CUDA_DEVICE_ORDER_RE = re.compile(r"['\"]?CUDA_DEVICE_ORDER['\"]?\s*[:=]\s*['\"]?(\w+)['\"]?")


def active_gpu_rows(con: Any, tables: set[str], max_rows: int) -> list[dict[str, Any]]:
    """Return active kernel GPU rows with logical and physical GPU IDs.

    The function scopes joins by report label/index when a multi-report DuckDB
    union is loaded.  When process IDs are available, it joins
    ``TARGET_INFO_CUDA_DEVICE`` by ``pid`` and ``cudaId``; otherwise it only
    uses mapping rows that are unambiguous for a given ``cudaId``.
    """

    if TABLE_TARGET_INFO_GPU not in tables or TABLE_CUDA_KERNEL not in tables:
        return []
    kernel_columns = _existing_columns(con, TABLE_CUDA_KERNEL)
    gpu_columns = _existing_columns(con, TABLE_TARGET_INFO_GPU)
    if "deviceId" not in kernel_columns or "id" not in gpu_columns:
        return []

    q = _quote_identifier
    output_scope = [column for column in SYNTHETIC_REPORT_COLUMNS if column in kernel_columns]
    gpu_scope = [column for column in output_scope if column in gpu_columns]
    gpu_selected = [
        column
        for column in (
            "name",
            "busLocation",
            "chipName",
            "computeMajor",
            "computeMinor",
            "smCount",
            "totalMemory",
            "uuid",
        )
        if column in gpu_columns
    ]

    gpu_select = [q(column) for column in gpu_scope]
    gpu_select.append(q("id"))
    gpu_select.extend(f"MIN({q(column)}) AS {q(column)}" for column in gpu_selected)
    gpu_group = ", ".join(q(column) for column in [*gpu_scope, "id"])
    with_parts = [
        f"""
        gpu_map AS (
            SELECT {", ".join(gpu_select)}
            FROM "{TABLE_TARGET_INFO_GPU}"
            GROUP BY {gpu_group}
        )
        """
    ]

    map_join = ""
    physical_expr = f"k.{q('deviceId')}"
    source_expr = "'identity'"
    cuda_map_columns = (
        _existing_columns(con, TABLE_TARGET_INFO_CUDA_DEVICE)
        if TABLE_TARGET_INFO_CUDA_DEVICE in tables
        else set()
    )
    if {"cudaId", "gpuId"}.issubset(cuda_map_columns) and _has_cuda_device_map_rows(con):
        map_scope = [column for column in output_scope if column in cuda_map_columns]
        can_join_pid = "pid" in cuda_map_columns and "globalPid" in kernel_columns
        if can_join_pid:
            selected = [q(column) for column in map_scope]
            selected.extend([q("cudaId"), q("gpuId"), q("pid")])
            with_parts.append(
                f"""
                cuda_device_map AS (
                    SELECT DISTINCT {", ".join(selected)}
                    FROM "{TABLE_TARGET_INFO_CUDA_DEVICE}"
                    WHERE cudaId IS NOT NULL AND gpuId IS NOT NULL AND pid IS NOT NULL
                )
                """
            )
            map_join = (
                "LEFT JOIN cuda_device_map m ON "
                f"k.{q('deviceId')} = m.{q('cudaId')} "
                f"AND m.{q('pid')} = ((k.{q('globalPid')} >> 24) & 16777215)"
            )
            for column in map_scope:
                map_join += f" AND k.{q(column)} = m.{q(column)}"
            physical_expr = f"COALESCE(m.{q('gpuId')}, k.{q('deviceId')})"
            source_expr = (
                f"CASE WHEN m.{q('gpuId')} IS NOT NULL "
                "THEN 'TARGET_INFO_CUDA_DEVICE(pid,cudaId)' ELSE 'identity' END"
            )
        else:
            selected = [q(column) for column in map_scope]
            selected.extend([q("cudaId"), f"MIN({q('gpuId')}) AS {q('gpuId')}"])
            group_columns = [*map_scope, "cudaId"]
            with_parts.append(
                f"""
                cuda_device_map AS (
                    SELECT {", ".join(selected)}
                    FROM "{TABLE_TARGET_INFO_CUDA_DEVICE}"
                    WHERE cudaId IS NOT NULL AND gpuId IS NOT NULL
                    GROUP BY {", ".join(q(column) for column in group_columns)}
                    HAVING COUNT(DISTINCT {q('gpuId')}) = 1
                )
                """
            )
            map_join = "LEFT JOIN cuda_device_map m ON " f"k.{q('deviceId')} = m.{q('cudaId')}"
            for column in map_scope:
                map_join += f" AND k.{q(column)} = m.{q(column)}"
            physical_expr = f"COALESCE(m.{q('gpuId')}, k.{q('deviceId')})"
            source_expr = (
                f"CASE WHEN m.{q('gpuId')} IS NOT NULL "
                "THEN 'TARGET_INFO_CUDA_DEVICE(cudaId)' ELSE 'identity' END"
            )
    elif fallback_map := _fallback_visible_devices_map(con, tables):
        physical_expr = _case_device_mapping_expr("k", "deviceId", fallback_map, q)
        mapped_values = ", ".join(str(logical) for logical in sorted(fallback_map))
        source_expr = (
            f"CASE WHEN k.{q('deviceId')} IN ({mapped_values}) "
            "THEN 'CUDA_VISIBLE_DEVICES(PCI_BUS_ID)' ELSE 'identity' END"
        )

    select_exprs = [f"k.{q(column)} AS {q(_public_scope_name(column))}" for column in output_scope]
    select_exprs.extend(
        [
            f"k.{q('deviceId')} AS logical_gpu_id",
            f"{physical_expr} AS physical_gpu_id",
            f"{source_expr} AS gpu_id_mapping_source",
            "COUNT(*) AS kernel_launch_count",
        ]
    )
    select_exprs.extend(f"g.{q(column)} AS {q(column)}" for column in gpu_selected)

    group_exprs = [f"k.{q(column)}" for column in output_scope]
    group_exprs.extend([f"k.{q('deviceId')}", physical_expr, source_expr])
    group_exprs.extend(f"g.{q(column)}" for column in gpu_selected)

    gpu_join = f"{physical_expr} = g.{q('id')}"
    for column in gpu_scope:
        gpu_join += f" AND k.{q(column)} = g.{q(column)}"

    order_exprs = [f"k.{q(column)}" for column in output_scope]
    order_exprs.extend([physical_expr, f"k.{q('deviceId')}"])

    sql = f"""
        WITH {", ".join(with_parts)}
        SELECT {", ".join(select_exprs)}
        FROM "{TABLE_CUDA_KERNEL}" k
        {map_join}
        LEFT JOIN gpu_map g ON {gpu_join}
        WHERE k.{q("deviceId")} IS NOT NULL
        GROUP BY {", ".join(group_exprs)}
        ORDER BY {", ".join(order_exprs)}
        LIMIT ?
    """
    rows = _query_dicts(con, sql, max_rows=max_rows, params=(max_rows,), suppress_errors=False)
    return [
        add_key(
            row,
            "gpu-active",
            row.get("report_label"),
            row.get("report_index"),
            row.get("logical_gpu_id"),
            row.get("physical_gpu_id"),
            row.get("busLocation"),
            row.get("uuid"),
        )
        for row in rows
    ]


def _public_scope_name(column: str) -> str:
    if column == SYNTHETIC_REPORT_LABEL:
        return "report_label"
    if column == SYNTHETIC_REPORT_INDEX:
        return "report_index"
    return column.strip("_") or column


def _case_device_mapping_expr(
    table_alias: str,
    column: str,
    mapping: dict[int, int],
    quote: Any,
) -> str:
    cases = " ".join(f"WHEN {logical} THEN {physical}" for logical, physical in sorted(mapping.items()))
    return f"CASE {table_alias}.{quote(column)} {cases} ELSE {table_alias}.{quote(column)} END"


def _fallback_visible_devices_map(con: Any, tables: set[str]) -> dict[int, int] | None:
    """Infer logical-to-physical IDs from captured environment strings.

    This is intentionally conservative.  It only applies when
    ``CUDA_DEVICE_ORDER=PCI_BUS_ID`` and ``CUDA_VISIBLE_DEVICES`` contains
    comma-separated integer device IDs.  UUID/bus-id forms and multi-report
    scoped ``StringIds`` are left as identity mapping rather than guessing.
    """

    if TABLE_STRING_IDS not in tables:
        return None
    string_columns = _existing_columns(con, TABLE_STRING_IDS)
    if "value" not in string_columns or SYNTHETIC_REPORT_LABEL in string_columns:
        return None
    rows = _query_dicts(
        con,
        f'SELECT value FROM "{TABLE_STRING_IDS}" WHERE value LIKE ? LIMIT 50',
        max_rows=50,
        params=("%CUDA_%",),
        suppress_errors=True,
    )
    cvd_value: str | None = None
    device_order: str | None = None
    for row in rows:
        text = str(row.get("value") or "")
        if match := _CUDA_VISIBLE_DEVICES_RE.search(text):
            cvd_value = match.group(1).strip()
        if match := _CUDA_DEVICE_ORDER_RE.search(text):
            device_order = match.group(1).strip()
    if not cvd_value or device_order != "PCI_BUS_ID":
        return None
    try:
        physical_ids = [int(part.strip()) for part in cvd_value.split(",") if part.strip()]
    except ValueError:
        return None
    if not physical_ids:
        return None
    mapping = {logical: physical for logical, physical in enumerate(physical_ids)}
    return mapping if any(logical != physical for logical, physical in mapping.items()) else None


def _has_cuda_device_map_rows(con: Any) -> bool:
    rows = _query_dicts(
        con,
        f'SELECT 1 AS present FROM "{TABLE_TARGET_INFO_CUDA_DEVICE}" WHERE cudaId IS NOT NULL AND gpuId IS NOT NULL LIMIT 1',
        max_rows=1,
        suppress_errors=True,
    )
    return bool(rows)
