# NVTX mark

**Short:** An NVTX mark is a point-in-time event emitted through the NVIDIA Tools Extension API; it has a single timestamp and no duration.

**Details:**

- Marks share the rest of NVTX's event model with ranges: a message, an optional category, an optional payload, and a domain that scopes them.
- They are the right tool for annotating discrete moments (a frame boundary crossed, a flag set, an error observed) where bracketing a duration would be misleading.
- Because a mark has no end, it does not participate in stack pairing or handle-based start/end pairing; only its domain, category, and payload contribute to correlation.
- A timeline view typically renders a mark as a vertical tick or a glyph rather than a bar, so a dense burst of marks reads differently than a dense set of ranges.

**See also:**

- [NVTX range](nvtx-range.md)
- [NVTX domain](nvtx-domain.md)
- [Perf marker](perf-marker.md)
