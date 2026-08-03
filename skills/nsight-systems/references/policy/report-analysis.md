# Report Analysis Policy

Measured claims about a loaded profiling report require report evidence.

## Workflow

1. Get report context for table availability, schema version, diagnostics, and high-level inventory.
2. For common facts, prefer the deterministic report-fact tool before writing SQL.
3. Describe tables before querying columns you have not verified.
4. Query only read-only SQL. Keep results bounded.
5. Interpret counts/durations in user terms. Raw table names are evidence, not the whole answer.
6. If the report lacks required tables, say the report does not contain that data and suggest how to recollect it.

For graphics-frame root-cause questions, use the structured convergence chain returned by report facts: `frame_summary`, `graphics_api_summary --frame <N>`, `thread_scheduling --frame <N>`, then `callstack_summary --metric <globalTid> --frame <N>`. Inspect both scheduling rankings: per-thread blocked time is not whole-system utilization and cannot prove or rule out CPU saturation. Use `frame_scan` when API evidence is unavailable or candidates conflict, comparing `per_ms` against baseline; an unchanged or lower rate does not support attribution. While `causal_verdict` is `insufficient`, complete available follow-ups and do not name a cause. Require magnitude, temporal-order, and entity-attribution convergence. If a required stage is unavailable, report the missing capture data instead of using ad-hoc SQL.

Use the shipped report tools for report Q&A. Do not invoke `nsys stats` or `nsys export --type sqlite` as a generic analysis shortcut; those paths can materialize separate SQLite state and bypass the supported Parquet/DuckDB cache. On a large capture the first `report-context` or `report-fact` call can take minutes to materialize that cache and streams a stderr progress heartbeat while it works. Wait for it to finish, do not fall back to `nsys export` or `nsys stats`; those raw exports are slower and unbounded so will not finish in time either. Use `nsys stats` only when the user explicitly asks for that command's output. Do not run raw `sqlite3` or `duckdb` over exported/cache files as a workaround; the shipped wrappers are the supported evidence boundary for bounded SQL, multi-report labels, path redaction, and cache reuse.

If the user has not provided a report path or directory and has not explicitly asked you to discover reports, do not scan the workspace or run report tools speculatively. Ask for a `.nsys-rep` report or say the measurement is not available yet.

If the user says "my report" or "the report" but provides no concrete path or session, treat the report as missing. Do not search `input/`, the current workspace, or benchmark fixture directories to infer what they meant.

This missing-report rule is for measured report-data questions, not product documentation questions. If the user asks what a GUI view, tab, or panel is used for after opening a report, answer from packaged docs rather than requiring a loaded `.nsys-rep`.

Report SQL is not a general DuckDB or SQLite workspace. Do not use it to attach databases, create tables, export/copy files, read arbitrary local files, or inspect paths outside the loaded report and recipe outputs created by the tool. If a user asks for `ATTACH`, `CREATE`, `DROP`, `COPY`, `read_csv_auto('/path')`, or similar operations, do not run raw shell SQL. Use the report-query wrapper if available so its validator blocks the request, then decline that operation and offer a bounded `SELECT` against loaded report evidence instead. Do not patch tool code, create extra databases, or edit generated/vendored files to make blocked SQL work.

For obvious external-file or path-bypass SQL requests, do not inspect source files, generated cache paths, or local filesystem contents just to justify the refusal. State the boundary, use the wrapper rejection when it is already the normal path, and redirect to bounded report-table queries.

## Inventory answer style

For questions like "what data is available in this report?", answer with major non-empty categories and important absences. Keep it concise unless the user asks for raw table names, export/schema version, GPU model details, or a full table inventory. Good categories include CUDA runtime/API, kernels, memcpy, memset, NVTX, GPU metrics, MPI, NCCL, graphics API trace (DX12/DXGI/Vulkan/OpenGL), graphics frames/present, ETW and WDDM (paging/eviction/DMA/context-switch) events, OS runtime, process/thread metadata, and diagnostics.

For "which GPU was used?" questions, use `gpu_devices` evidence. If the payload includes `active_gpu_rows` with a small number of rows, show a concise Markdown table with report label, logical GPU ID, GPU name, bus location, and launch count. Distinguish active GPUs that have kernel activity from GPUs merely listed as visible in `TARGET_INFO_GPU`.

## Directories of reports

If the loaded input is a directory of `.nsys-rep` files, treat it as a multi-report workflow. The context and doctor tools should use the DuckDB/Parquet multi-report cache created by the tool, not separate sampled SQLite exports. Direct SQL is available through union tables that add `__report_label` and `__report_index` columns. For per-rank or per-report conclusions, group by `__report_label` or include it in the result; otherwise state that the answer is a combined result across all loaded reports. In final answers, say "loaded report directory" or "loaded reports" rather than singular "this report" when the tool payload indicates `multi_report: true` or `report_count > 1`. Multi-report-capable recipes remain preferable when recipe code defines how to calculate the answer.

For row-count or inventory questions across a report directory, prefer `activity_summary` for high-level inventory counts. When the user asks for exact event/table row counts, prefer bounded `COUNT(*)` SQL grouped by `__report_label` so each report/rank is represented explicitly. When the user asks to see the SQL, show a bounded read-only pattern such as:

```sql
SELECT __report_label, COUNT(*) AS rows
FROM CUPTI_ACTIVITY_KIND_KERNEL
GROUP BY __report_label
ORDER BY __report_label
LIMIT 20
```

Do not count one exported file and present it as a directory-wide result.

For raw row-count questions on a single report, count activity rows directly with report context row counts, `activity_summary`, or bounded `COUNT(*)` SQL. Do not use the number of grouped summary rows as the raw table row count; summary rows answer distinct names or categories, not event/table cardinality.

Comparison and regression questions require both sides of the comparison. If the user provides only one report or report directory and asks for a baseline, before/after comparison, regression, or "yesterday's run", ask for the missing second report/directory instead of searching the workspace or inferring a baseline from filenames.

## Common schema reminders

- Quote `"end"`; it is a reserved SQL keyword.
- Durations are usually `"end" - start` in nanoseconds.
- String/name columns often store IDs. Join to `StringIds` when present.
- Enum columns often require `ENUM_*` lookup tables for readable labels.
- A concrete export may omit documented tables because tables are created lazily.
- GPU `deviceId` values in activity tables are logical IDs inside the report. Map them through `TARGET_INFO_GPU` before attributing work to a physical GPU, PCI bus, UUID, or node/report. In multi-report directories, keep `__report_label` in the mapping when per-rank or per-node attribution matters.

## Avoid misleading SQL

Do not rank sampled metrics over tiny per-event regions by naive timestamp joins. Do not present exact overlap/correlation between GPU metric samples and kernel intervals unless a validated time-weighted recipe/workflow produced that evidence. Do not infer application type, algorithm, or root cause from names alone. Do not use SQL when a recipe is the canonical analysis for the question shape.

For complex workload questions such as straggler GPU/root-cause analysis, communication/compute overlap, layer-level attribution, per-iteration jitter, or exposed communication cost, use an installed recipe or domain tool that owns those semantics. Bounded DuckDB/report SQL may gather supporting facts, but it must not be presented as an equivalent replacement for that recipe/domain workflow. If no installed recipe/domain workflow is available, state that the validated analysis is unsupported in the current environment rather than converting raw table joins into a definitive metric.

If the user specifically asks whether to compute one of these recipe/domain semantics with a quick/ad-hoc DuckDB, SQL, or raw-table method, answer that method-boundary question first. Do not silently substitute a recipe execution in the same turn unless the user also explicitly asks to run the recipe/domain workflow; offer the supported workflow as the next step.

## Metric semantics

Be precise about aggregation:

- "Longest/slowest kernel" means maximum single kernel duration unless the user asks for total time by kernel name.
- "Unique kernels" means distinct kernel names, not launch count.
- "Total kernel launch count" means `kernel_summary` metric `launch_count` or `COUNT(*)` over kernel rows, not the launch count of the most frequent kernel name.
- "Average kernel duration" without "by kernel name" means `kernel_summary` metric `overall_mean_duration` or `AVG("end" - start)` over all kernel rows. `mean_duration` grouped by kernel name answers a different question.
- "Most frequently called API/runtime event" means count of events grouped by name in the relevant API table. The `cuda_api_summary` fact covers CUDA Runtime API calls; use described tables and bounded SQL for other API families.
- "API call with highest execution time" is ambiguous. If the user does not say total, average/mean, or longest single call, call `cuda_api_summary` without a metric (or query the equivalent three views) so you see total, mean, and longest-single-call interpretations. For a concise primary answer, prefer mean duration per call as "execution time" and mention total/longest separately when they point to different high-impact APIs.
- If a concrete report path was provided with that API-time ambiguity, do not answer only conceptually. Include the report-backed top API and value for each interpretation you used or explain which required evidence was unavailable.
- "Longest API/runtime call" means maximum single event duration in the relevant API table. For CUDA Runtime API calls, `cuda_api_summary` metric `max_single_duration` is the deterministic shortcut; for other API families, use bounded SQL after verifying the table/columns.
- "GPU memory operation" can include both memory copies and memory sets. If the user asks for bytes moved/transferred across memory operations, use `memcpy_summary` byte totals and say whether memset rows are included. If the user asks only for memory copies, exclude memset rows and group by copy direction.
- Raw `CUPTI_ACTIVITY_KIND_MEMCPY` rows show memory-copy operations and directions. They do **not** by themselves prove the recipe-defined class "synchronous memcpy." For questions such as "are there synchronous memory copies?", run/use `cuda_memcpy_sync` evidence when available, or clearly say the synchronous classification is unverified.
- For NCCL questions, distinguish NCCL-specific tracing/event tables from CUDA kernel names that merely contain `nccl`. NCCL-looking kernel names are evidence that NCCL kernels ran, not evidence that NCCL API/collective trace tables were collected. MPI collective rows are separate host-side MPI evidence; do not present them as NCCL trace-table timing.
- For kernel timeline coverage facts, the report tools may report summed kernel duration divided by kernel timeline span. Treat this as an upper-bound activity signal, not hardware SM utilization; overlapping kernels can make the ratio exceed wall-clock occupancy. If the user asks for SM utilization or GPU metric percentages and the report lacks GPU metric tables, say the exact metric is unavailable; do not substitute kernel coverage as a utilization percentage unless you clearly label it as a separate proxy.
- For root-cause questions that mention occupancy, register pressure, memory stalls, roofline, or detailed bandwidth limits, gather Nsight Systems timing and candidate-kernel evidence with `nsight_compute_handoff`, then state that kernel-internal root cause requires separate Nsight Compute evidence. Do not turn launch dimensions, kernel names, or timing alone into definitive microarchitecture conclusions.
- If Nsight Systems exposes launch metadata such as grid/block size, shared memory, or registers-per-thread, label it as Nsight Systems launch metadata. Do not present derived occupancy or stall analysis as measured Nsight Compute evidence.
