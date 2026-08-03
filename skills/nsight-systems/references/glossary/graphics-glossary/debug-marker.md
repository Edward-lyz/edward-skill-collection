# Debug marker

**Short:** A named region or label that an application records into a graphics command stream so tools can show what each block of GPU work represents.

**Details:**

- A begin and end pair brackets a run of commands: ``PIXBeginEvent`` and ``PIXEndEvent`` in D3D11 and D3D12, and ``vkCmdDebugMarkerBeginEXT`` and ``vkCmdDebugMarkerEndEXT`` (or the newer ``vkCmdBeginDebugUtilsLabelEXT`` and ``vkCmdEndDebugUtilsLabelEXT``) in Vulkan.
- A point marker has no duration and is used for one-off annotations, exposed as ``PIXSetMarker`` and ``vkCmdInsertDebugUtilsLabelEXT``.
- Markers carry a short string and sometimes a color; the same calls also work on the queue to label submissions rather than recorded commands.
- They live inside the command stream: nesting is strict, and begin and end must be on the same command list or queue.
- They complement NVTX: NVTX describes CPU side phases, while debug markers describe GPU side regions and are visible to graphics tools without extra instrumentation.
- Profilers match begin and end by nesting depth and render a labeled hierarchy aligned with draw calls, dispatches, and submissions.

**See also:**

- [Command list and queue](command-list-queue.md)
- [Vulkan command buffer](vulkan-command-buffer.md)
- [NVTX range](../nsys-glossary/nvtx-range.md)
- [Perf marker](../nsys-glossary/perf-marker.md)
