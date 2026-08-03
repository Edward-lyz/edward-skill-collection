# Tool Selection Policy

Use tool shape, not keyword memorization. Choose tools from the user's intent and available evidence.

## Product/docs questions

Use packaged docs lookup for concepts, workflows, troubleshooting, UI actions, requirements, platform support, and broad capability questions. If retrieved docs have weak coverage, say so rather than fabricating.

Documentation questions about GUI concepts remain docs questions even if the word "report" appears in the UI context. Answer questions about what GUI views, tabs, or panels are used for from packaged docs; do not require a loaded `.nsys-rep` unless the user asks for measurements or contents from their specific report.

When generated Installation Guide, Release Notes, or other packaged docs directly state a support requirement, answer it directly and cite that evidence. Live CLI help is for installed command syntax and options, not for support matrices.

## CLI questions

Use live CLI help before asserting command syntax, flag existence, default values, or valid option values. If a flag is absent from live help, say it is not verified in the installed `nsys`; do not guess from another version.

When the user asks what an exact flag does, inspect the flag itself first, such as `nsys_skill_cli inspect-cli --target "--disable-alignment"`, so the helper can search command and recipe scopes.

When the user asks about a bare option name without naming an `nsys` command or recipe, do not assume the `profile` command. Search packaged docs and recipe metadata for the option, then answer by context or ask for the command context.

## Recipe questions

Use recipe lookup/help for recipe discovery, options, inputs, outputs, and interpretation. Use recipe execution only when a report is loaded and the user asks to run or generate recipe output.

If the user asks how to list recipes, answer with `nsys recipe --help` and stop unless they also ask for the full catalog.

For recipe operational questions, search packaged docs/curated recipe references first, then inspect live per-recipe help before asserting recipe-specific flags. Examples include multi-report inputs, `--filter-time`, `--filter-nvtx`, directory `:n` limits, `--mode none`, `NoDataError`, `.nsys-analysis`, common output files, and memory/disk troubleshooting.

Recipe output inspection uses the `schema_command` / `output_label` returned by recipe execution:

- Call `nsys_skill_cli recipe-output-schema` with the returned label.
- For follow-up SQL-style questions about generated recipe rows, use `nsys_skill_cli recipe-output-query` with the returned label.
- SQL should query the returned `query_table` names such as `all_stats`, not local file paths or DuckDB file readers such as `read_csv_auto` or `read_parquet`.

Do not pass, ask for, test, or demonstrate arbitrary local input/output directories for recipes. The wrapper chooses report and output paths.

Use `recipe-analysis.md` for recipe command syntax, output-file interpretation, custom recipe boundaries, and failure behavior.

## Report-data questions

Use report context to see available tables and diagnostics. For common measured facts, use the report-fact tool before ad-hoc SQL so metric semantics are stable. Use table descriptions before writing SQL against unfamiliar tables.

Use SQL for direct aggregations over concrete activity tables. Use recipes for analyses where recipe code encodes non-trivial semantics such as utilization maps, overlap math, pacing, synchronization classes, idle-gap classification, or multi-report correlation. If no official recipe is available for the requested complex analysis, say that exact analysis is not supported rather than inventing an equivalent SQL method.

Treat straggler detection, exposed communication cost, layer-level attribution, per-iteration jitter, and communication/compute overlap as recipe or domain-tool questions. Report facts and SQL can provide bounded evidence such as top kernels, CUDA API timing, NCCL-looking rows, or active GPUs, but they do not own the higher-level diagnosis. Do not present a quick DuckDB/raw-table query as a validated result for these concepts.

When the question is specifically about using a quick/ad-hoc DuckDB, SQL, or raw-table method for those concepts, do not auto-run the recipe as a silent substitute. State that the requested method is not valid for the recipe/domain metric, then offer the installed recipe/domain workflow as the supported next step if the user wants the validated metric.

Do not use `nsys stats` or `nsys export --type sqlite` as a generic shortcut for report Q&A. The supported report path is `nsys_skill_cli report-*` or the packaged report scripts, which export/cache native `.nsys-rep` inputs through Parquet/DuckDB. Use `nsys stats` only when the user specifically asks for that command's output.

In shell hosts, do not bypass the report wrappers with raw `sqlite3`, `duckdb`, direct reads of generated cache files, or extra databases.

Use the report-doctor tool/script when the user asks whether a report is empty, incomplete, missing CUDA/NVTX/GPU metrics data, inconsistent, or trustworthy enough for analysis. Treat doctor warnings as evidence.

If the user asks which recipes are appropriate for the loaded report, first use report context or report facts to learn what data is present, then list installed recipes that match those data categories.

For loaded-report bottleneck questions, gather deterministic facts first: kernel summary, CUDA API summary, memcpy summary, and NVTX presence for compute workloads, or frame summary, graphics API summary, and thread scheduling (blocking waits) for graphics/frame workloads, as relevant. Then recommend recipes based on observed data. For Nsight Compute handoff questions, use the `nsight_compute_handoff` report-fact intent when available.

For "which recipes should I use" questions, prefer a short ranked list of the directly relevant installed recipes. Do not pad the answer with every adjacent CUDA/GPU/NCCL recipe.

## Troubleshooting questions

Use generated docs plus curated troubleshooting references. Broad symptom questions such as empty reports, profiling crashes, GUI startup failures, install failures, permission errors, download/platform support, and system requirements often need a short list of likely causes plus the exact evidence to collect. Do not require a report before giving documented likely causes.

For broad product questions such as what `nsys` means, whether CUDA/MPI or DirectX/Vulkan/OpenGL graphics applications are supported, report compatibility, file formats, metric categories, general limitations, and use with other tools, use packaged docs and curated support references.

## Compound questions

Split the question into sub-questions. A question can require docs plus report data, or recipe lookup plus recipe execution. Do not answer a report-data sub-question from docs, and do not answer a docs/support-matrix sub-question from the current report hardware.
