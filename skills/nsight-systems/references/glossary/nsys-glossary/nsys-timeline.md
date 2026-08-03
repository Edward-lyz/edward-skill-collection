# Nsight Systems timeline

**Short:** The main interactive view in ``nsys-ui`` — a tree-like hierarchy of rows on the left, an optional line-labels column in the middle, and charts / events on the right.

**Details:**

- Contents depend on which collectors were enabled during the profiling session; disabled collectors produce no rows.
- Each row is built by a hierarchy builder from one or more export tables (e.g. the NVTX builder turns ``NVTX_EVENTS`` into nested per-thread, per-domain ranges).
- Supports zoom and pan, time-range selection, tooltip on hover (with **Copy Tooltip** via right-click), and headless screenshot via ``nsys-ui --screenshot``.
- The same hierarchical structure is what [DumpTimeline](dumptimeline.md) serializes to JSON outside the GUI.

**See also:**

- [Hierarchy row](hierarchy-row.md)
- [Correlation arrow](correlation-arrow.md)
- [Sampling marks](sampling-marks.md)
- [nsys-ui](nsys-ui.md)
- [DumpTimeline](dumptimeline.md)
- *Frame Duration row*, *Stutter row*, *CPU bar process coloring* — [Rst/UserGuide/topics/timeline.md](https://docs.nvidia.com/nsight-systems/UserGuide/), [Rst/UserGuide/topics/fps-overview.md](https://docs.nvidia.com/nsight-systems/UserGuide/)
