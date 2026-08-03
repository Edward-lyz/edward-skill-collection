# Perf marker

**Short:** "Perf marker" is an umbrella term for any application-emitted annotation that a profiler captures and renders on a timeline to label work in human terms.

**Details:**

- The category spans NVTX ranges and marks, PIX events on Windows D3D, Vulkan debug-utils labels and D3D12 PIX markers, and Reflex latency markers around simulation, render submit, present, and GPU work.
- The point is to bridge raw API events with the developer's mental model of phases like "physics step", "shadow pass", or "frame N".
- Different sources have different scope rules: NVTX events live on threads and domains, debug-utils labels live on command buffers, Reflex markers live on the rendering pipeline.
- Payloads vary: a name string is universal, while numeric IDs, frame numbers, and structured schemas are source-specific.
- A profiler usually normalizes these sources onto a single row primitive so a user can reason about all annotations the same way.

**See also:**

- [NVTX range](nvtx-range.md)
- [NVTX mark](nvtx-mark.md)
- [NVTX domain](nvtx-domain.md)
- [Debug marker](../graphics-glossary/debug-marker.md)
- [Reflex render latency](../graphics-glossary/reflex-render-latency.md)
