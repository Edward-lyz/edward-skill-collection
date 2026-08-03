# Nsight Systems event

**Short:** One captured occurrence during a profiling session — an API call, an NVTX range, a kernel launch, a context switch, a GPU metric sample, etc. A typical report contains millions of them.

**Details:**

- Each event has at minimum a timestamp (and usually an end timestamp for ranged events), a source/type, owning process / thread / GPU IDs, and often a ``correlationId`` linking it to related events from other sources.
- Correlation IDs let one logical operation be tracked across layers — e.g. a CUDA runtime API call → its CUPTI driver activity → the GPU kernel it launched, or a Vulkan API call → the GPU workload it produced. The GUI renders these links as arrows between rows.
- In the SQLite / Parquet export, events are stored as rows in source-specific tables (``NVTX_EVENTS``, ``DX12_API``, ``CUPTI_ACTIVITY_KIND_KERNEL``, ``OSRT_API``, etc.). Each row is one event.
- **NVTX events** are application-instrumented ranges, marks, and counters (in ``NVTX_EVENTS`` and ``NVTX_PAYLOAD_*``). **ETW events** are OS-level events on Windows (in ``ETW_EVENTS`` and ``WDDM_*``). **Generic events** (``GENERIC_EVENTS``) are user / plugin-defined typed events whose field schemas live in ``GENERIC_EVENT_TYPES``.

**See also:**

- [Correlation arrow](correlation-arrow.md)
- [Trace vs. sample](trace-vs-sample.md)
- [Export](export.md)
- [Export tables](export-tables.md)
- [NVTX](nvtx.md)
- [ETW](../graphics-glossary/etw.md)
