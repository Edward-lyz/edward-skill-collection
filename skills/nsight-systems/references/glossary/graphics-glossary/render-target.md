# Render target

**Short:** The image, or set of images, that the output-merger stage writes to during a draw.

**Details:**

- In D3D12 a render target is bound through a render-target view (RTV) via ``OMSetRenderTargets``, paired with an optional depth-stencil view (DSV) for the depth buffer.
- In Vulkan a render target is a framebuffer attachment described either by a ``VkRenderPass`` and ``VkFramebuffer`` or by the dynamic-rendering extension (``vkCmdBeginRendering``) which takes attachments inline.
- Render targets can be the swap chain back buffer, an offscreen color texture for post-processing, a depth or stencil image, or a multi-sampled image that is later resolved.
- Clearing happens with ``ClearRenderTargetView`` and ``ClearDepthStencilView`` on D3D12, or via load operations (``VK_ATTACHMENT_LOAD_OP_CLEAR``) on Vulkan; load and store ops are important for bandwidth on tiled GPUs.
- Multiple Render Targets (MRT) lets a single pixel shader write several outputs at once, which is the basis for deferred shading G-buffers.

**See also:**

- [Graphics pipeline](graphics-pipeline.md)
- [Swap chain](swap-chain.md)
