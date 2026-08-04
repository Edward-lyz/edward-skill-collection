---
name: nsys-simulator-operator-alignment
description: Compare a stable Nsight Systems kernel pattern with simulator operator timings. Export every Nsys kernel, attach simulator timings when mapped, calculate per-operator and per-layer errors, and write KU-style CSV and XLSX workbooks. Use for Nsys-vs-simulator throughput investigations, remote nsys-rep analysis, and layer/operator alignment reports.
---

# Nsys / Simulator Operator Alignment

This skill produces two artifacts:

- A flat CSV that keeps every stable Nsys kernel, including runtime, NCCL, and scheduler kernels that have no simulator mapping.
- A formatted XLSX workbook with a KU-style operator sheet, layer summaries, stage metrics, and methodology notes.

## Workflow

1. Export an ordered kernel window from the `.nsys-rep` on a machine that has `nsys` CLI. Keep device, PP rank, microbatch, and absolute start/end timestamps in the metadata.
2. Run the simulator with the same chunk size, context length, microbatch, and parallelism settings.
3. Build the alignment table. Do not drop Nsys rows when the simulator has no corresponding operator. Leave simulator time and error blank for those rows.
4. Treat host NVTX ranges and persistent NCCL SendRecv kernels as interval evidence, not additive kernel latency. Compute communication exposure from interval unions when reporting stage totals.
5. Generate the CSV and XLSX with `scripts/build_alignment_report.py`.

## Command

```bash
python3 scripts/build_alignment_report.py \
  --input k3_stage0_mb8_operator_compare.csv \
  --csv-out k3_stage0_mb8_operator_compare_ku.csv \
  --xlsx-out k3_stage0_mb8_operator_compare_ku.xlsx \
  --title '模拟器和nsys耗时对比' \
  --meta 'bs=8,ctx=32K,chunk=32K,pp=16,dp=1,tp=1,ep=1'
```

The input schema is the detailed alignment CSV used by the K3 analysis. The writer also accepts additional columns and preserves them in the raw-data sheet.

## Output sheets

- `算子明细`: one row per Nsys kernel or generated summary row; columns include Nsys name/time, simulator operator/time, and error percentage.
- `层级汇总`: one row per model layer with Nsys total, simulator total, and layer error.
- `阶段总览`: wall/compute/NCCL union, overlap, exposed communication, idle time, and stage-level comparison.
- `说明`: assumptions and overlap interpretation.

Do not interpret a persistent NCCL kernel duration as transfer latency. Use the `阶段总览` interval-union metrics for that comparison.
