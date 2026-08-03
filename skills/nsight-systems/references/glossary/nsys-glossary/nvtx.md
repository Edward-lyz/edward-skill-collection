# NVTX

**Short:** NVIDIA Tools Extension — a header-only instrumentation library that lets an application annotate its own work with timed ranges, point marks, named threads, domains, categories, and structured payloads, which profiling tools then render on the timeline.

**Details:**

- Three primary annotation types: push/pop ranges (stack-scoped, per thread), start/end ranges (free-form, can cross threads), and instant marks.
- Annotations live inside a *domain* (one logical namespace per library or subsystem) and are tagged with an optional *category* for color-coding and grouping.
- Ranges can carry messages (literal or registered strings) and structured payloads, allowing arbitrary application data to be attached to timeline events.
- Captured by Nsight Systems when NVTX tracing is enabled (``nsys profile -t nvtx ...``); appears as per-thread, per-domain rows on the timeline.
- Drives several derived workflows: the NVTX-based capture-range trigger (``--capture-range=nvtx --nvtx-capture=...``), the F11 hotkey marker, and NVTX-projection recipes that map CPU NVTX time onto the GPU work it caused.

**See also:**

- [NVTX domain](nvtx-domain.md)
- [NVTX range](nvtx-range.md)
- [NVTX mark](nvtx-mark.md)
- [NVTX payload](nvtx-payload.md)
- [NVTX category](nvtx-category.md)
- [NVTXT trace](nvtxt-trace.md)
- [Perf marker](perf-marker.md)
