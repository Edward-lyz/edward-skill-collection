# Vulkan

**Short:** Khronos's explicit, low-overhead cross-platform graphics and compute API; the application owns memory, command recording, queue submission, and synchronization, and the driver does very little behind its back.

**Details:**

- The object model centers on ``VkInstance``, ``VkPhysicalDevice``, ``VkDevice``, ``VkQueue``, ``VkCommandPool``, ``VkCommandBuffer``, ``VkPipeline``, and descriptor sets bound through a ``VkPipelineLayout``.
- Work is recorded into ``VkCommandBuffer`` objects, allocated from a pool tied to a single queue family; recording is single-threaded per buffer but trivially parallel across buffers. Submission goes through ``vkQueueSubmit`` / ``vkQueueSubmit2``.
- Synchronization is fully explicit: pipeline barriers, image layouts, render passes (or dynamic rendering), semaphores (``VkSemaphore``, binary and timeline), and fences (``VkFence``) for CPU side.
- Memory is allocated as ``VkDeviceMemory`` and sub-allocated by the application; resources (buffers, images) bind into those allocations. Most engines layer an allocator like VMA on top.
- Capability is exposed through device features and a vast extension ecosystem: ray tracing, mesh shaders, dynamic rendering, descriptor indexing, sync2, video decode / encode.

**See also:**

- [DX12](dx12.md)
- [Vulkan command buffer](vulkan-command-buffer.md)
- [Swap chain](swap-chain.md)
- [Graphics pipeline](graphics-pipeline.md)
- [Low-level graphics API](low-level-api.md)
