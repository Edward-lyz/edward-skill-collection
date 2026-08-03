# Low-level graphics API

**Short:** The low-level graphics APIs are the explicit, close-to-the-driver rendering interfaces a profiler captures directly: Direct3D 12 and Vulkan.

**Details:**

- They share an explicit model: the application allocates command buffers, records draw and dispatch commands, submits them to typed queues (graphics, compute, copy), and synchronizes with fences and semaphores it owns.
- The API surface splits into CPU-side calls that record or submit work, GPU-side workload the driver schedules onto an engine, and debug or marker calls naming regions for tools.
- Capturing here gives a one-to-one mapping between API calls and the GPU work they produce, letting a profiler correlate a draw call back to its function and forward to the engine that ran it.
- Each API has its own object naming (``IDXGISwapChain``, ``VkCommandBuffer``, ``ID3D12GraphicsCommandList``) and memory and marker model, but the timeline shape is the same: API rows on CPU, workload rows on GPU, markers bridging them.
- Older immediate-mode APIs (Direct3D 9, Direct3D 11, OpenGL classic) hide queue submission and command-buffer construction, so they fall outside this group.

**See also:**

- [DX12](dx12.md)
- [Vulkan](vulkan.md)
- [DX11](dx11.md)
- [OpenGL](opengl.md)
- [Graphics pipeline](graphics-pipeline.md)
