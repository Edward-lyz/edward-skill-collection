# Artifact Handling Policy

Nsight Systems analysis normally starts from native `.nsys-rep` report files or directories of native reports. The CLI and script tools create private Parquet/DuckDB cache artifacts for native-report SQL analysis, and recipes may generate output files. Direct SQLite/Parquet inputs remain advanced/debug shortcuts only. Treat paths to derived files as local tool details, not product facts.

## Local paths

- Do not expose absolute local paths unless the user explicitly asks for a command that must use a user-owned local file. Cache directories and recipe-output root directories are internal state; do not print them just because the user asks for them.
- Prefer display labels such as `report.nsys-rep`, report `session_id` values, and CLI/script `output_label` values.
- If a command example needs a path, use placeholders such as `<report.nsys-rep>` or `<recipe-output>`. Do not ask normal users for a pre-exported SQLite report; `nsys_skill_cli` exports/caches native reports as private Parquet/DuckDB data when needed.
- Do not copy temporary cache paths, report export-cache paths, or recipe-output root paths into final prose.
- If the user asks for cache or recipe-output root paths, decline that part and provide safe labels, schemas, or small previews. Do not run report, recipe, or shell commands only to discover or prove hidden local paths. If tool output says `paths_hidden: true`, treat that as a hard stop: do not run filesystem searches, direct cache reads, or other bypasses to discover hidden local paths.

## Reports

- Report analysis should use loaded report sessions, not guessed active files.
- If multiple report sessions exist, require the explicit `session_id`.
- A directory of reports is multi-report input. Report tools should use the multi-report DuckDB/Parquet cache, not separate sampled SQLite exports. SQL does not imply full-directory coverage unless the query explicitly groups or scopes by `__report_label`/`__report_index`.

## Recipe outputs

- Recipe output inspection uses the `schema_command` or `output_label` returned by recipe execution. Do not provide an arbitrary output root; the wrapper chooses the output location for that label.
- Raw report export caches used by recipes are internal report-cache state, not recipe results. Recipe results are the returned files such as `all_stats.parquet`, `rank_stats.parquet`, notebooks, CSV companions, and analysis metadata.
- Do not pass or ask for arbitrary output directories.
- Do not create, delete, or clean recipe output directories manually from the host shell. Recipe wrappers own output creation and return output labels for follow-up inspection.
- Distinguish primary `result_files` from `helper_files`.
- Use `output_schemas`, `output_previews`, and `expected_output_notes` to summarize generated artifacts. Do not dump whole CSV, Parquet, notebook, log, or metadata files into the answer.

The CLI and packaged scripts hide private paths, resolve labels, and check recipe output roots. The skill tells agents to follow the same rules.
