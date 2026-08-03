# NVTX range

**Short:** An NVTX range is a timed interval emitted through the NVIDIA Tools Extension API, with a start timestamp, a stop timestamp, and optional message, payload, and category.

**Details:**

- The API offers two flavors: stack-scoped push/pop ranges that nest within a single thread, and free-form start/end ranges identified by a handle that can cross threads.
- Push/pop ranges form a LIFO stack per thread and per domain, which makes them natural for marking call scopes and nested phases of work.
- Start/end ranges decouple start and stop, so asynchronous work (a submitted job, a network operation, a frame) can be bracketed from different threads.
- Each range carries a message (literal or registered string), an optional category for grouping, and an optional payload (numeric or structured per a registered schema).
- Ranges live inside a domain, so the same category number means different things in different domains; tools render and correlate per domain.

**See also:**

- [NVTX domain](nvtx-domain.md)
- [NVTX mark](nvtx-mark.md)
