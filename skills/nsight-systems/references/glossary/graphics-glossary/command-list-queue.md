# Command list and queue

**Short:** In D3D12 a command list records GPU commands on the CPU, and a command queue executes batches of those lists on the GPU via ``ExecuteCommandLists``.

**Details:**

- Command lists come in types: direct (graphics + compute + copy), compute, copy, and bundle; the type must match the queue that executes it.
- A command queue is the GPU-side scheduler endpoint; multiple queues of different types can run in parallel and synchronize through fences.
- Bundles are short, reusable secondary lists invoked from a primary direct list; they let the driver pre-validate a fixed sequence of commands so it can be replayed cheaply.
- Recording is single-threaded per list but multiple lists can be recorded on different threads, which is the main way D3D12 scales CPU submission work.
- ``ExecuteCommandLists`` is the actual submission boundary: any state set inside a list does not persist across that boundary, so callers must rebind pipeline state, descriptor heaps, and render targets at the start of each list.

**See also:**

- [DX12](dx12.md)
- [Vulkan command buffer](vulkan-command-buffer.md)
- [DXGI](dxgi.md)
