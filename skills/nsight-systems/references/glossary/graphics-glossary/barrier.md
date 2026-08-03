# Barrier

**Short:** Explicit synchronization that orders GPU work and transitions resource state when multiple operations touch the same resource.

**Details:**

- In D3D12, ``ID3D12GraphicsCommandList::ResourceBarrier`` issues transitions between ``D3D12_RESOURCE_STATE_*`` values such as ``RENDER_TARGET``, ``PIXEL_SHADER_RESOURCE``, ``COPY_DEST``, and ``COMMON``, plus UAV and aliasing barriers.
- Enhanced barriers (``D3D12_BARRIER_*``) decouple sync scope, access type, and layout into separate fields, allowing finer-grained ordering than legacy state transitions.
- Vulkan uses ``vkCmdPipelineBarrier`` and ``vkCmdPipelineBarrier2`` to express execution barriers (stage masks), memory barriers (access masks), and image layout transitions in a single call.
- Image layouts (``VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL``, ``VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL``, ``VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL``) describe how a resource is currently laid out in memory and must match the access about to occur.
- Common bubble causes include barriers inserted between back-to-back draws that did not need them, redundant transitions to ``COMMON``, and overly broad stage masks that drain the pipeline.

**See also:**

- [GPU bubble](gpu-bubble.md)
- [Command list and queue](command-list-queue.md)
- [Graphics pipeline](graphics-pipeline.md)
- [DX12](dx12.md)
- [Vulkan](vulkan.md)
