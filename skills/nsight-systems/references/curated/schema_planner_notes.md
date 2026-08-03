# Schema Planner Notes for Report Queries

> Curated overlay: release-reviewed synthesis. Source inputs: QuadD/Docs/Rst/AnalysisGuide/topics/sqlite-schema-reference.rst; Report tools and report-fact metric definitions. Official generated docs, live CLI/recipe help, and report-tool evidence remain authoritative when facts differ.

Use these notes to choose evidence for common Nsight Systems report questions. They are supplemental planning guidance. The official SQLite Schema Reference defines possible tables and columns, and a concrete report contains only the tables collected for that run. Always inspect the loaded report before making a measured claim.

## Evidence workflow




1. For a loaded report, start with report context or table discovery.
2. Use deterministic report facts for common metrics such as GPU name, kernel summary, CUDA API summary, memcpy summary, and report inventory.
3. Use schema lookup to check documented columns, then inspect the concrete table before writing ad-hoc SQL.
4. Keep SQL bounded and distinguish totals, counts, unique names, means, and longest single events.

## Common table families

| Question intent | Start with | Notes |
|---|---|---|
| GPU model/name used by the report | `TARGET_INFO_GPU` | Prefer report fact/context when available. GPU rows are report evidence, not system inventory. |
| Kernel launches, longest kernel, unique kernel names | `CUPTI_ACTIVITY_KIND_KERNEL` | One row per launch. Kernel name columns such as `shortName` and `demangledName` reference `StringIds` in many exports. |
| CUDA Runtime API calls | `CUPTI_ACTIVITY_KIND_RUNTIME` | CPU-side runtime calls. `nameId` references `StringIds`; `correlationId` may link CPU launch calls to GPU activity when present. |
| CUDA memory copies | `CUPTI_ACTIVITY_KIND_MEMCPY` | Contains timing and byte counts. Direction/kind fields are enum-like and version-sensitive; inspect concrete values before interpreting labels. |
| CUDA memory sets | `CUPTI_ACTIVITY_KIND_MEMSET` | Similar timing semantics to memcpy; use `bytes` for volume and `end - start` for duration. |
| NVTX ranges/events | `NVTX_EVENTS` | Text can be inline or referenced through `textId`/`StringIds` depending on export. Absence means the report has no NVTX table or no collected NVTX rows, not that the application has no annotations. |
| OS runtime calls | `OSRT_API` | CPU-side OS runtime events such as pthread/file/runtime calls when collected. Names commonly reference `StringIds`. |
| Process/thread context | `PROCESSES`, `THREADS`, metadata tables | Use for context only. For the profiled command, prefer capture metadata when present instead of assuming the largest process table row is the target. |
| GPU metrics samples | GPU metrics tables documented in the schema | Sampling can be absent, partial, or flat. Use report doctor/context before drawing conclusions. |

## String and correlation conventions

- `StringIds(id, value)` consolidates repeated strings. When a column name ends in `Id` and the schema says it references strings, join through `StringIds`.
- Do not assume every text field is an ID. Some tables contain inline text columns.
- `correlationId` can connect related CPU and GPU events, but only when both sides were collected and the relevant columns exist in the concrete report.
- CUDA activity `deviceId` values are CUDA logical device IDs. When `TARGET_INFO_CUDA_DEVICE` is present, use its `cudaId` to `gpuId` mapping before comparing kernel activity with `TARGET_INFO_GPU` or GPU metrics. If that table is absent, only use `CUDA_VISIBLE_DEVICES` as a fallback when the captured environment also shows `CUDA_DEVICE_ORDER=PCI_BUS_ID`.
- Time columns such as `start` and `end` are generally timestamp values in the exported report timebase. Use `end - start` for event duration.
- `globalPid`/`globalTid` values are serialized identifiers, not plain OS process/thread IDs. Prefer report facts, recipe composite tables, or explicit process/thread joins before presenting process or thread identity.

## Timebase, identity, and sampling cautions

- Treat timestamps as report-time values unless the inspected table or official schema says otherwise. Prefer durations computed from event intervals (`end - start`) and trace-relative presentation over raw timestamp values.
- Use `ANALYSIS_DETAILS.duration` or other inspected report metadata when a workflow needs the valid analysis window. Do not invent a wall-clock duration from the largest timestamp unless the trace-time basis is clear.
- Some rows can have negative or pre-analysis timestamps because of capture setup, buffering, or imported data. Filter to the documented/inspected analysis window before computing percentages or rates.
- CPU sampling rows can mix sampled instruction records with other event families. When the concrete schema exposes a `cpuCycles` distinction, use the sampled/cycle-bearing rows for CPU time attribution and do not combine them with non-sampling rows as if they had the same meaning.
- Scheduler/blocking tables describe observed scheduling state, not root cause by themselves. Join or correlate with process/thread/NVTX/CUDA evidence before claiming why a thread was blocked.
- Do not expose raw serialized IDs as user-facing process/thread identity unless no better label exists. Prefer decoded process/thread names, report labels, or a clear statement that only internal IDs were available.

## Common metric distinctions

- **Longest kernel**: maximum single launch duration from kernel rows.
- **Total kernel time**: sum of launch durations; this can exceed wall-clock time when kernels overlap across streams or devices. Use interval union logic before making wall-time or coverage claims.
- **Unique kernel names**: distinct resolved names, not launch count.
- **API/runtime total time**: sum of CPU-side API/event durations within the relevant API table. The CUDA Runtime API shortcut is `cuda_api_summary`.
- **Longest API/runtime call**: maximum single event duration within the relevant API table.
- **Memcpy volume**: sum of `bytes`; **memcpy duration**: sum or max of `end - start`, depending on the question.

When the question matches one of these common distinctions, prefer the deterministic report-fact tool. Use ad-hoc SQL only when the fact tool does not cover the requested metric.
