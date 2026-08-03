# DumpTimeline

**Short:** A separate executable that extracts the timeline hierarchy from a ``.nsys-rep`` as JSON — an alternative to ``nsys export``, but the unit it returns is rows / hierarchy builders / items rather than raw event tables.

**Details:**

- Loads one or more ``.nsys-rep`` files through Nsight Systems's analysis library and serializes the same structure the GUI would render.
- Useful when you need to know how events group into rows / tracks without parsing the binary ``.nsys-rep`` directly, or when investigating a discrepancy between raw events and how they appear in the GUI.
- A separate binary, not a ``nsys`` subcommand. Lives at ``QuadD/Tools/DumpTimeline/``. Reference dumps for known hierarchies (NVTX, DX12, Vulkan, WDDM, KhrDebug, GPU metrics, etc.) live under ``QuadD/Tools/DumpTimeline/Tests/<area>/`` and can be diffed against to validate hierarchy changes.
- Useful flags: ``--full`` (don't summarize row contents), ``--show-all`` (include low-utilization rows hidden by default), ``--correlation`` (compute cross-row links), ``--filter-rules`` / ``--filter-key-value`` (narrow the dump), ``--simulated-resoluton`` (timeline width for generic items).

**See also:**

- [Export](export.md)
- [Hierarchy row](hierarchy-row.md)
- [Nsight Systems timeline](nsys-timeline.md)
