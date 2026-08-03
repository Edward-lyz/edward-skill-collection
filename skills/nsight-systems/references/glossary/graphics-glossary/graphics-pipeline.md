# Graphics pipeline

**Short:** The ordered sequence of fixed-function and programmable stages a GPU runs to turn vertex data into rendered pixels.

**Details:**

- The classic graphics pipeline runs Input Assembly (IA), Vertex Shader (VS), optional Hull / Tessellator / Domain (HS, TS, DS), optional Geometry Shader (GS), Rasterizer (RS), Pixel Shader (PS), and Output Merger (OM).
- Newer mesh-shader pipelines replace IA, VS, HS, TS, DS, GS with an Amplification Shader and a Mesh Shader that emit meshlets directly.
- Compute is a sibling pipeline with a single programmable stage; it runs a kernel over a thread grid and is launched with ``Dispatch`` or ``vkCmdDispatch`` instead of ``Draw``.
- State for the pipeline (shaders, blend, depth, raster, root signature, descriptor layout) is baked into a pipeline state object so the driver can validate and compile once.
- The pipeline matters because each stage has different bottlenecks: vertex-bound vs pixel-bound vs bandwidth-bound workloads need different tuning.

**See also:**

- [DX12](dx12.md)
- [Vulkan](vulkan.md)
- [Command list and queue](command-list-queue.md)
- [Vulkan command buffer](vulkan-command-buffer.md)
- [Render target](render-target.md)
