# Report file (.nsys-rep)

**Short:** Native Nsight Systems result file produced by a successful profiling session. Contains all captured events in nsys's binary format. Also called *report*, *Nsight Systems report*, or *result file*.

**Details:**

- Every downstream tool reads a ``.nsys-rep``: ``nsys-ui``, ``nsys stats``, ``nsys analyze``, ``nsys recipe``, ``nsys export``, and ``DumpTimeline``.
- The only nsys file format considered forward-compatible across versions; exported formats (SQLite, Parquet, etc.) are not.
- Holds CPU samples, GPU work, API traces (CUDA, DX12, Vulkan, OpenGL), NVTX, GPU metrics, WDDM, ETW, OSRT, and any plugin-defined generic events that were captured.
- Can be opened directly in ``nsys-ui`` for timeline analysis, or converted to a queryable form with ``nsys export``.

**See also:**

- [Profiling session](profiling-session.md)
- [Export](export.md)
- [SQLite export](sqlite-export.md)
- [nsys-ui](nsys-ui.md)
