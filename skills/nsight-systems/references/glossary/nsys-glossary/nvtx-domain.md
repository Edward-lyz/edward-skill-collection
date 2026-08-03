# NVTX domain

**Short:** An NVTX domain is a named namespace under the NVIDIA Tools Extension API that groups related instrumentation events from a tool, library, or subsystem.

**Details:**

- Each domain is identified by a string name registered at runtime; the API returns an opaque handle that callers pass to subsequent NVTX calls.
- Domains let independent producers (an application, a math library, a communication layer) emit events without colliding on category IDs, message strings, or payload schemas.
- A profiler can filter, enable, or render events per domain, which keeps a busy timeline readable when many libraries are instrumented at once.
- Domains scope sub-entities: categories, registered string handles, payload schemas, and scopes are all interpreted within their owning domain.
- Two domains with the same name can resolve to different handles in different processes or load orders, so name-based identification is often more robust than handle-based identification across a trace.

**See also:**

- [NVTX range](nvtx-range.md)
- [NVTX mark](nvtx-mark.md)
- [Perf marker](perf-marker.md)
