# Reflex SDK row

**Short:** GUI timeline row that visualizes NVIDIA Reflex SDK latency markers as time ranges, captured automatically when D3D11, D3D12, or Vulkan tracing is enabled.

**Details:**

- Reflex SDK markers are NVAPI calls applications use to integrate NVIDIA's Ultra Low Latency feature and lower end-to-end input-to-photon latency.

  - On Windows they are collected from two sources: CPU-side markers via the PCLStats TraceLogging ETW provider, and GPU-side markers by intercepting NvAPI_D3D_GetLatency / NvAPI_Vulkan_GetLatency and reading the NV_LATENCY_RESULT_PARAMS frame report.
  - On Linux they are collected by intercepting the Vulkan low_latency2 extension.

- Marker types shown as ranges in the row: **RenderSubmit**, **Simulation**, **Present**, **Driver**, **OS Render Queue**, **GPU Render**.
- Captured automatically — no extra ``-t`` flag needed beyond enabling one of the graphics APIs (D3D11 / D3D12 / Vulkan).
- Useful when investigating input lag, frame pacing, or pipeline-stage overlap on Reflex-instrumented titles.

**See also:**

- [Perf marker](perf-marker.md)
- *Frame Duration row* — [Rst/UserGuide/topics/fps-overview.md](https://docs.nvidia.com/nsight-systems/UserGuide/)
