# Correlation arrow

**Short:** A visual link drawn in the GUI timeline between a CPU-side API call and the GPU work it produced.

**Details:**

- Examples: CUDA runtime kernel launch → GPU kernel execution; Vulkan / DX12 submit → GPU workload; NVTX-projection lines connecting CPU NVTX ranges to the GPU work they correspond to.
- Backed by the ``correlationId`` column found in many event tables — events that share a correlation ID describe the same logical work captured at different layers (host API, driver activity, device execution).
- Useful for tracing a single operation across the host / driver / device boundary, and for figuring out which CPU activity is responsible for a given GPU bubble or hotspot.

**See also:**

- [Nsight Systems event](nsys-event.md)
- [Hierarchy row](hierarchy-row.md)
- [Nsight Systems timeline](nsys-timeline.md)
- [GPU bubble](../graphics-glossary/gpu-bubble.md)
