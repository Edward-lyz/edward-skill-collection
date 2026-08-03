# Performance Warnings row

**Short:** GUI timeline row that surfaces auto-detected performance warnings and common pitfalls based on the enabled capture types.

**Details:**

- Reported warning sources:
  - ETW performance warnings.
  - ``vkQueueSubmit`` (Vulkan) and ``ID3D12CommandQueue::ExecuteCommandLists`` (D3D12) calls that take longer than the total time of the GPU workloads they generated.
  - D3D12 memory operation warnings.
  - Vulkan API calls that may adversely affect performance.
  - Vulkan device creation with memory zeroing (whether by physical-device default or explicit request).
  - Vulkan command-buffer barriers that can be combined or removed (subsequent barriers, read-to-read barriers, etc.).
- Each warning appears as a marker on the row at the time it was detected; the warning text is shown in the tooltip.
- Useful as a first-pass triage row when opening an unfamiliar report — surfaces "this is probably wrong" hotspots without needing to run an analysis recipe.

**See also:**

- [Expert system](expert-system.md)
- [Graphics-focused recipes](graphics-recipes.md)
- *Frame Duration row* — [Rst/UserGuide/topics/fps-overview.md](https://docs.nvidia.com/nsight-systems/UserGuide/)
- *Frame Health row* — [Rst/UserGuide/topics/frame-health.md](https://docs.nvidia.com/nsight-systems/UserGuide/)
