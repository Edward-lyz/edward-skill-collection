# Pipeline state object

**Short:** A compiled, pre-validated bundle of shaders and fixed-function state that the GPU binds as a single unit.

**Details:**

- In D3D12, ``ID3D12PipelineState`` for graphics packs vertex/pixel/hull/domain/geometry shaders together with blend, depth-stencil, rasterizer, input layout, primitive topology type, RTV/DSV formats, and sample description.
- A compute PSO is much simpler: just the compute shader plus its root signature linkage.
- The root signature (D3D12) or ``VkPipelineLayout`` (Vulkan) defines the binding interface; the PSO is validated against it at creation so binding at draw time is cheap.
- Vulkan's equivalent is ``VkPipeline``, created as graphics or compute via ``vkCreateGraphicsPipelines`` / ``vkCreateComputePipelines``; pipeline libraries (``VK_EXT_graphics_pipeline_library``) allow incremental compilation of vertex-input, pre-rasterization, fragment, and fragment-output sub-states.
- First-use PSO compilation is a classic stutter cause because the driver may JIT-compile the final GPU-specific binary on the first draw; PSO caches, pre-warming, and on-disk pipeline caches mitigate this.

**See also:**

- [Graphics pipeline](graphics-pipeline.md)
- [DX12](dx12.md)
- [Vulkan](vulkan.md)
- [Stutter](stutter.md)
- [Command list and queue](command-list-queue.md)
