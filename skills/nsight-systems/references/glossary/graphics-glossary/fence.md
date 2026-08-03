# Fence

**Short:** A GPU/CPU synchronization primitive that tracks completion of submitted work via a monotonically increasing counter.

**Details:**

- In D3D12, ``ID3D12Fence`` holds a 64-bit value; ``ID3D12CommandQueue::Signal`` writes a value when prior work on that queue completes, and ``Wait`` makes a queue stall until the fence reaches a target value.
- In Vulkan, ``VkFence`` is a binary GPU-to-CPU signal, while timeline semaphores (``VkSemaphore`` created with ``VK_SEMAPHORE_TYPE_TIMELINE``) provide the equivalent monotonic-counter behavior for GPU-to-GPU and GPU-to-CPU ordering.
- CPU-side waits use ``ID3D12Fence::SetEventOnCompletion`` paired with ``WaitForSingleObject``, or ``vkWaitSemaphores`` / ``vkWaitForFences``; these block the host thread until the GPU reaches the requested value.
- Cross-queue ordering is expressed by signaling a fence on one queue and waiting on it from another, letting compute, copy, and direct queues coordinate without CPU involvement.
- In WDDM, monitored fences are kernel-tracked variants the scheduler can wait on directly, avoiding a round-trip through user mode for queue-to-queue dependencies.

**See also:**

- [Command list and queue](command-list-queue.md)
- [GPU bubble](gpu-bubble.md)
- [WDDM](wddm.md)
- [GPU context switch](gpu-context-switch.md)
- [Vulkan command buffer](vulkan-command-buffer.md)
