# Recipe Framework Operational Reference

> Curated overlay: release-reviewed synthesis. Source inputs: installed nsys_recipe framework docs; installed nsys_recipe/lib/args.py; installed nsys_recipe/lib/recipe.py; installed nsys_recipe/lib/recipe_loader.py. Official generated docs, live CLI/recipe help, and report-tool evidence remain authoritative when facts differ.



This release-reviewed reference covers common operational questions about Nsight Systems recipes. Live `nsys recipe <name> --help` still wins for exact syntax in the installed version.

## Listing installed recipes




Use the installed CLI as the source of truth:

```text
nsys recipe --help
nsys recipe <recipe_name> --help
```

The top-level help lists installed built-in recipes and command usage. Per-recipe help gives exact options. Do not recommend a recipe listing flag unless it is shown by live help for the user's installed version.

## Recipe inputs, file types, and multi-report directories




Live per-recipe help is the authority for accepted inputs. In current recipe help, built-in recipes commonly use:

```text
nsys recipe <recipe_name> --input <report-or-directory> [recipe options]
```

Examples:

```text
nsys recipe cuda_api_sum --input rank0.nsys-rep rank1.nsys-rep
nsys recipe cuda_api_sum --input reports/
nsys recipe cuda_api_sum --input reports/:32
```

Useful rules:

- The concise user-facing form is `nsys recipe <recipe-name> [args]`; the recipe name comes before recipe-specific arguments such as `--input`.
- Current live help often describes `--input` as one or more `.nsys-rep` files or directories. Directory input can use `:n` to limit the number of files read from that directory.
- The installed input parser also accepts `.qdrep` files when present, including `.qdrep` files found in input directories.
- Directory matches are sorted by filename before the optional `:n` limit is applied. Use the generated `files.*` output for rank/file evidence instead of guessing from filenames.
- SQLite exports are relevant to `nsys stats` and some post-processing workflows, but do not promise direct SQLite recipe input unless live help or recipe code for that recipe confirms it.

For MPI or multi-rank workloads, collect one report per rank or selected rank, then pass the files or containing directory to the recipe. Use recipes such as `mpi_gpu_time_util_map` for MPI/GPU overlap and imbalance questions when installed.

## Time, NVTX, and timestamp filtering




Use recipe filtering options to narrow analysis before large outputs are materialized:

- `--filter-time <start_ns>/<end_ns>` restricts events to a nanosecond time range. Either side may be omitted, for example `/5000000` or `1000000/`.
- `--filter-nvtx range[@domain][/index]` restricts analysis to matching NVTX ranges when available.
- `--start` and `--end` are deprecated aliases; prefer `--filter-time` when live help lists it.
- `--disable-alignment` disables automatic time-offset alignment across input reports when the installed recipe exposes the option.

If a filter excludes all relevant events, the recipe may produce no output or report `NoDataError`.

## Custom recipe assistance boundary




Custom recipe assistance is allowed when it helps the user understand or debug their own work. It is appropriate to explain official concepts, review user-provided recipe code or `metadata.json`, interpret errors, and suggest the next focused implementation step.

Do not generate a complete ready-to-run custom recipe or every file for the user. If asked to write the whole recipe, decline that part and offer focused help: review an existing snippet, explain `DataService`/mapper concepts, point to official recipe-authoring docs, or suggest a built-in recipe/report-analysis alternative.

## Custom recipe discovery and `Unknown recipe`




The installed recipe loader discovers recipe directories containing `metadata.json` in this order:

1. directories from `NSYS_RECIPE_PATH`;
2. the current working directory;
3. the default installed `nsys_recipe/recipes` directory.

If `nsys recipe <name>` reports `Unknown recipe`, check that the directory name and `metadata.json` recipe identity match the command name, then check the search path order above. For built-in recipes, `nsys recipe --help` is the fastest installed-name check.

## Custom recipe parameters and arguments




Use the exact `metadata.json` keys documented by the installed framework when the user asks about file format. Shipped recipes commonly expose `module_name`, `display_name`, `description`, and tags, but live source docs for the installed version win.

Recipe CLI arguments are added in Python code, not by inventing an arbitrary `metadata.json` argument schema. A recipe that needs custom options overrides `get_argument_parser()`, calls `super().get_argument_parser()`, then calls `parser.add_recipe_argument(...)`. Verify resulting option names with live recipe help.

## Recipe framework core concepts




Use this to explain concepts, not to create a full custom recipe.

Typical pieces:

- a Python module defining a class derived from the framework `Recipe` base class;
- `metadata.json` for identity, display name, tags, and module/class discovery;
- optionally a notebook template when the recipe generates interactive visualization;
- mapper/reducer data flow: `mapper_func()` processes one input report, while the reducer combines per-report outputs.

Typical flow:

1. **Input:** reports or report directories are passed through `--input`.
2. **Storage/export:** each report is converted to the storage needed by the installed framework if the storage does not already exist.
3. **DataService:** recipe code queues/requests raw or composite report tables, reads them as DataFrames, and applies recipe filters and time alignment.
4. **Mapper:** per-report intermediate data is produced.
5. **Context:** `context.map()`, `context.launch()`, and `context.wait()` coordinate sequential, local concurrent, or Dask execution depending on mode.
6. **Reducer:** mapper outputs are concatenated, grouped, ranked, or otherwise aggregated.
7. **Outputs:** recipes write Parquet/CSV files, notebooks, and sometimes an `.nsys-analysis` entry point.

For output management, mention the framework APIs only at a conceptual level unless exact installed source is available: `self.add_output_file(...)`, `self.create_notebook(...)`, and `self.create_analysis_file()`.

## Standard recipe outputs




Most recipes create an output directory. Common files include:

- `files.parquet` / `files.csv`: input file list and rank/file mapping.
- `rank_stats.parquet` / `.csv`: per-input or per-rank statistics.
- `rank_stats_by_device.parquet` / `.csv`: per-device statistics.
- `all_stats.parquet` / `.csv`: aggregate statistics across inputs.
- `all_stats_by_device.parquet` / `.csv`: aggregate per-device stats.
- `stats.ipynb` or another notebook: interactive visualization.
- `<output-name>.nsys-analysis`: JSON metadata entry point that lets the GUI open the recipe result directory as an analysis. The framework initializes it with recipe metadata and execution parameters such as `RecipeVersion`, `RecipeName`, `DisplayName`, `Options`, and `StartTime`; recipes commonly add `EndTime` and an `Outputs` inventory of generated files/types before calling `create_analysis_file()`.

Exact files and columns are recipe- and version-specific. Inspect `files`, `output_schemas`, and `output_previews` after running a recipe when the user asks what a particular run produced. Typical stats columns include `Name` or `Text`, `Count`, `Mean`, `Std`, `Min`, `Q1`, `Median`, `Q3`, `Max`, `Sum`, and grouping fields such as `Rank` or `Device`. Durations are usually nanoseconds unless the recipe output says otherwise.

Recipe-generated Parquet files are ordinary Parquet files. Read them with Pandas, PyArrow, DuckDB, or other Parquet tooling. Control the main result directory with `--output <directory>` when live help lists it; use `--force-overwrite` only when intentionally replacing existing output. `--export-dir` controls exported intermediate files and is not the same as the main result directory.

Notebook customization is recipe-code work: recipes can call `create_notebook()` with replacement values and can copy helper files with `add_notebook_helper_file()`. For normal users, prefer inspecting the generated notebook/output files; for custom recipe authors, explain these APIs conceptually or review their existing snippet rather than generating a complete ready-to-run recipe package.

## NCCL recipe selection




For NCCL-focused optimization, start with NCCL-specific recipes when installed:

- `nccl_sum`: summarize NCCL calls and timing.
- `nccl_gpu_overlap_trace`: inspect communication/compute overlap over time.
- `nccl_gpu_time_util_map`: heatmap GPU time utilization around NCCL work; useful for rank/time imbalance and communication bubbles.
- `nccl_gpu_proj_sum`: project NCCL CPU calls onto GPU work.

Supporting recipes can provide context: `gpu_gaps` for idle gaps, `cuda_api_sync` for synchronization, `cuda_gpu_trace` / `cuda_gpu_kern_sum` for kernels around collectives, `nvlink_sum` / `network_sum` for link traffic, and MPI/UCX recipes when those libraries are used. Verify installed names with live help before listing them as available.

## Large reports, memory, and `NoDataError`




For large reports:

- Filter early with `--filter-time` or `--filter-nvtx`.
- Process fewer files at once, or limit directory inputs with `:n`.
- Prefer summary recipes when aggregates are sufficient.
- Limit concurrent recipe workers with `NSYS_CONCURRENT_MAX_WORKERS` when using the default concurrent mode.
- Use `--mode none` when live help supports it to debug parallel failures sequentially.
- Keep export/output paths on a fast local filesystem with enough free space.

If parallel mode fails, rerun with `--mode none`, then reduce the input set to isolate the failing report. Check corrupted/incomplete reports and memory/disk pressure before assuming recipe code is wrong.

Do not recommend a generic `--rows` workaround for all recipes. Row-limit arguments are recipe-specific and must be verified with live help.

`NoDataError` usually means the recipe found no relevant input rows after trace selection and filters. Common causes are a missing trace source, unsupported report contents, an over-restrictive time/NVTX filter, or a capture range that missed the work.
