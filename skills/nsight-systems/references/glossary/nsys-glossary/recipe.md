# Recipe

**Short:** A Python analysis script that runs against one or more ``.nsys-rep`` reports via ``nsys recipe <name>`` and produces a directory of tables, visualizations, and notebooks.

**Details:**

- Ships with Nsight Systems under ``<target>/python/packages/nsys-recipe/recipes/`` and can be customized or written from scratch.
- Output is a directory containing tabular data (CSV / Parquet / Arrow), Plotly visualizations, and often a Jupyter notebook (``stats.ipynb``).
- The path for **multi-report analysis** — comparing runs, multi-rank cluster jobs, multi-pass collections.
- The path for **richer output** than ``nsys stats`` can produce — interactive notebooks, visualizations, even web apps (e.g. ``gfx_hotspot``).
- Several expert-system rules also exist as recipes of the same name, often with extended behavior or multi-report support.
- Each recipe is tagged with one or more output keywords (Summary, Trace, Pace, Heatmap, Histogram, etc.) describing the shape of its output.

**See also:**

- [Graphics-focused recipes](graphics-recipes.md)
- [Expert system](expert-system.md)
- *Recipe output keywords* (Summary / Trace / Pace / Heatmap / Histogram / Expert System / Stats System) — see the keywords table in [Rst/AnalysisGuide/topics/available-recipes.md](https://docs.nvidia.com/nsight-systems/AnalysisGuide/)
