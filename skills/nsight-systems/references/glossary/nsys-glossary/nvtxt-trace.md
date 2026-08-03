# NVTXT trace

**Short:** A plain text stream format that carries pre-recorded NVTX events so a profiler can ingest them offline.

**Details:**

- An NVTXT file is a line oriented log where each record encodes one NVTX event: a timestamp, a process and thread id, a domain, an optional category, and a message or payload.
- It mirrors the runtime NVTX API (push, pop, start, end, mark) as text, so any tool can produce a trace without linking against ``nvToolsExt``.
- Typical producers are emulators, simulators, replay harnesses, or post processing scripts that have timing data but cannot call ``nvtxRangePushEx`` live.
- A profiler ingests the file as if the events were captured in process, exposing them under the same domain and category rows as live NVTX.
- Multiple source files can be combined in one session, each tagged with its own process and thread namespace so identifiers do not collide.

**See also:**

- [NVTX domain](nvtx-domain.md)
- [NVTX range](nvtx-range.md)
- [NVTX mark](nvtx-mark.md)
- [NVTX category](nvtx-category.md)
