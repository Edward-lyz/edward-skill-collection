# nsys stats

**Short:** CLI command that runs report scripts against a SQLite export to produce tabular summaries (column, table, csv, tsv, json, hdoc, htable) printed to console, written to files, or piped to another command.

**Details:**

- Default report set covers NVTX, CUDA API + kernels + memops, OS runtime, OpenGL / Vulkan / DX11 / DX12 markers, WDDM queues, and Unified Memory.
- Each report is a script that queries the SQLite export and returns CSV; ``nsys stats`` reformats it for the requested output.
- Discover what's available with ``nsys stats --help-reports ALL`` and ``nsys stats --help-formats ALL``.
- Auto-generates the SQLite export from the ``.nsys-rep`` if one isn't already present.
- Complementary to ``nsys analyze`` (rule-based, not statistical) and ``nsys recipe`` (multi-report, richer output, often originating from the same scripts).

**See also:**

- [SQLite export](sqlite-export.md)
- [Expert system](expert-system.md)
- [Recipe](recipe.md)
- For recipe output keywords (Summary / Trace / Pace / Heatmap / Histogram / Expert System / Stats System), see the keywords table in [Rst/AnalysisGuide/topics/available-recipes.md](https://docs.nvidia.com/nsight-systems/AnalysisGuide/).
