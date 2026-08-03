# Vulkan command buffer

**Short:** A ``VkCommandBuffer`` records draws, dispatches, copies, and synchronization on the CPU for later execution on a ``VkQueue``.

**Details:**

- Command buffers are allocated from a ``VkCommandPool`` that is tied to a single queue family; pools are not thread-safe, so each recording thread typically owns its own pool.
- Primary command buffers are submitted to a queue with ``vkQueueSubmit``, ``vkQueueSubmit2``, or ``vkQueueSubmit2KHR``; secondary command buffers can only be executed from a primary one via ``vkCmdExecuteCommands``.
- A command buffer has an explicit lifecycle (initial, recording, executable, pending, invalid) controlled by ``vkBeginCommandBuffer``, ``vkEndCommandBuffer``, and ``vkResetCommandBuffer``.
- ``vkQueueSubmit`` takes one or more ``VkSubmitInfo`` batches, each with wait semaphores, command buffers, and signal semaphores, which express GPU-side ordering across queues; host-side CPU / GPU completion synchronization is provided separately by the optional ``VkFence`` passed to ``vkQueueSubmit``, which is signaled once the submitted work finishes.
- Synchronization inside a buffer is the caller's responsibility: pipeline barriers, events, and render-pass dependencies must be inserted explicitly, unlike higher-level APIs.

**See also:**

- [Command list and queue](command-list-queue.md)
- [Swap chain](swap-chain.md)
