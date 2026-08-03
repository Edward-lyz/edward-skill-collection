# Trace vs. sample

**Short:** Two ways Nsight Systems captures data: *trace* records every event from a source, *sample* periodically captures CPU call stacks.

**Details:**

- **Trace** — Records every event from the enabled source: every Vulkan API call into ``VULKAN_API``, every NVTX range into ``NVTX_EVENTS``, every CUDA kernel launch into ``CUPTI_ACTIVITY_KIND_KERNEL``, and so on. Exact and complete, but overhead scales with event volume.
- **Sample** — Periodically captures CPU call stacks (into ``SAMPLING_CALLCHAINS``). Fixed low overhead, but statistical: hotspots show up reliably, but a sample miss doesn't prove the code didn't run.
- Most reports combine both. Trace covers anything event-driven; sampling covers CPU work that isn't surfaced by tracing.
- Sampling appears in the GUI timeline as orange marks (periodic-sampling stacks) or grey marks (stacks captured opportunistically from other sources such as ETW events on Windows).

**See also:**

- [Nsight Systems event](nsys-event.md)
- [CPU sampling](cpu-sampling.md)
- [Sampling marks](sampling-marks.md)
- [Thread state](thread-state.md)
