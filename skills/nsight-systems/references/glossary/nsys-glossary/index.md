# Nsight Systems Glossary

Reference for Nsight Systems-specific vocabulary: CLI commands, file formats, exported event tables, GUI / timeline elements, and analysis recipes. Each entry is one Markdown (.md) file (a few are catalog reference docs with multiple sections).

This index lists terms grouped by area. Each link is a one-line hook; click through for the full entry.

For tool-agnostic graphics, ETW / WDDM, and NVTX-primitive concepts, see the sibling [graphics-glossary](../graphics-glossary/index.md).

## Conventions

- Each entry starts with a one-line **Short** definition.
- **Details** gives 2 to 6 short bullets, with concrete references to Nsight Systems syntax (CLI switches, file extensions, table names, GUI controls) where helpful.

- **See also** lists related entries. Links beginning with ``../graphics-glossary/`` point into the graphics (tool-agnostic) glossary for underlying concepts.

- A few catalog entries (``export-tables``, ``graphics-recipes``) use multiple Markdown section headers to organize the catalog instead of the single-concept layout.

## Concepts

- [profiling-session.md](profiling-session.md) - the bounded period of one collection that produces one .nsys-rep
- [nsys-event.md](nsys-event.md) - one captured occurrence during a profiling session
- [trace-vs-sample.md](trace-vs-sample.md) - event-driven trace vs. periodic statistical sampling
- [export.md](export.md) - converting .nsys-rep into queryable formats (SQLite, Parquet, ...)
- [recipe.md](recipe.md) - Python analysis scripts run via nsys recipe
- [expert-system.md](expert-system.md) - rule-based analyzer behind nsys analyze

## Report files and exports

- [report-file.md](report-file.md) - .nsys-rep, the native binary result file
- [sqlite-export.md](sqlite-export.md) - the .sqlite database produced by nsys export
- [parquet-export.md](parquet-export.md) - parquetdir export and the .parquet files inside

## CLI

- [collection-commands.md](collection-commands.md) - nsys profile, and the interactive launch / start / stop sequence
- [nsys-stats.md](nsys-stats.md) - tabular summary reports
- [dumptimeline.md](dumptimeline.md) - alternative extraction tool: dumps timeline hierarchy to JSON
- [nsys-ui.md](nsys-ui.md) - the Nsight Systems GUI executable
- (nsys export, nsys analyze, nsys recipe are covered in "Concepts" above)

## Timeline and GUI

- [nsys-timeline.md](nsys-timeline.md) - main interactive view in nsys-ui
- [hierarchy-row.md](hierarchy-row.md) - a single row / track on the timeline, built by a hierarchy builder
- [correlation-arrow.md](correlation-arrow.md) - visual link from CPU API call to the GPU work it produced
- [sampling-marks.md](sampling-marks.md) - orange / grey dots on the timeline marking captured stacks
- [thread-state.md](thread-state.md) - per-thread execution status on the Thread State timeline row

For CPU-bar process coloring (user / kernel / other), see the *Process Coloring* section of [Rst/UserGuide/topics/timeline.md](https://docs.nvidia.com/nsight-systems/UserGuide/).

### Frame-related rows

- [performance-warnings-row.md](performance-warnings-row.md) - auto-detected performance warnings and common pitfalls

For the **Reflex SDK row** (NVIDIA Reflex SDK latency markers), see [reflex-sdk-row.md](../graphics-glossary/reflex-sdk-row.md) in the sibling graphics glossary.

For the **Frame Duration**, **Stutter**, and **Frame Health** rows, see the user-facing docs directly: [Rst/UserGuide/topics/fps-overview.md](https://docs.nvidia.com/nsight-systems/UserGuide/) (frame duration + stutter, including the 19-frame median, 4 ms floor, and OSC detection) and [Rst/UserGuide/topics/frame-health.md](https://docs.nvidia.com/nsight-systems/UserGuide/).

## NVTX and perf markers

- [nvtx.md](nvtx.md) - NVIDIA Tools Extension instrumentation library overview
- [nvtx-domain.md](nvtx-domain.md) - namespace grouping NVTX events
- [nvtx-range.md](nvtx-range.md) - start/end push/pop range
- [nvtx-mark.md](nvtx-mark.md) - point-in-time NVTX marker
- [nvtx-payload.md](nvtx-payload.md) - typed data attached to an NVTX event
- [nvtx-category.md](nvtx-category.md) - integer category id, used for color-coding
- [nvtxt-trace.md](nvtxt-trace.md) - NVTXT offline NVTX trace format
- [perf-marker.md](perf-marker.md) - umbrella over NVTX, PIX, Vulkan, Reflex markers

## GPU activity and metrics

- [gpu-metrics.md](gpu-metrics.md) - sampled hardware counters: SM activity, memory throughput, video engines
- [sm-warp-occupancy.md](sm-warp-occupancy.md) - SM, warp, and occupancy on NVIDIA GPUs
- [bandwidth-usage.md](bandwidth-usage.md) - measured throughput of a transfer path

## Analysis views

- [cpu-sampling.md](cpu-sampling.md) - periodic PC + stack capture per CPU
- [module-view.md](module-view.md) - profile aggregated by binary module

## Reference catalogs

- [export-tables.md](export-tables.md) - catalog of SQLite / Parquet tables produced by nsys export
- [graphics-recipes.md](graphics-recipes.md) - catalog of graphics-focused nsys recipes

For the recipe output **keyword** tags (Summary / Trace / Pace / Heatmap / Histogram / Expert System / Stats System), see the keywords table in [Rst/AnalysisGuide/topics/available-recipes.md](https://docs.nvidia.com/nsight-systems/AnalysisGuide/).
