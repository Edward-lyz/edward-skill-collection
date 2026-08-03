# Reflex SDK row

**Short:** GUI timeline row that visualizes NVIDIA Reflex SDK latency markers as time ranges, captured automatically when D3D11, D3D12, or Vulkan tracing is enabled.

**Details:**

- Reflex SDK markers are used to integrate NVIDIA's Ultra Low Latency feature; the mechanism for collecting markers differs by platform and between CPU and GPU sides. They help lower end-to-end input-to-photon latency.
- Marker types shown as ranges in the row: **RenderSubmit**, **Simulation**, **Present**, **Driver**, **OS Render Queue**, **GPU Render**.
- Captured automatically — no extra ``-t`` flag needed beyond enabling one of the graphics APIs (D3D11 / D3D12 / Vulkan).
- Useful when investigating input lag, frame pacing, or pipeline-stage overlap on Reflex-instrumented titles.

**See also:**

- [Reflex render latency](reflex-render-latency.md)
- [Perf marker](../nsys-glossary/perf-marker.md)
- *Frame Duration row* — [Rst/UserGuide/topics/fps-overview.md](https://docs.nvidia.com/nsight-systems/UserGuide/index.html#fps-overview)
