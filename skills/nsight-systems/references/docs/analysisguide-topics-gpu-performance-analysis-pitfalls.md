---
source_path: AnalysisGuide/topics/gpu-performance-analysis-pitfalls.rst
title: ## GPU Performance Analysis Pitfalls
---
## GPU Performance Analysis Pitfalls

When interpreting GPU/CPU performance traces, a handful of misconceptions
recur and lead to incorrect conclusions. Each entry below pairs a common but
**wrong** assumption with the **correct** interpretation.

### CPU vs GPU cost confusion

#### Resolution does not affect CPU-side API call cost

- **Wrong**: "Present() / Draw() / Dispatch() / vkQueueSubmit() takes longer at higher resolutions because there are more pixels to process."
- **Correct**: The CPU cost of issuing these API calls is resolution-independent. The CPU records a command; it does not process pixels. GPU-side work (compositing, copying the back-buffer) may scale with resolution, but that work is asynchronous and does not appear on the CPU timeline unless explicitly synchronized via a fence or wait.

#### Command-buffer submission cost is not proportional to GPU workload

- **Wrong**: "Submitting more complex shaders takes longer on the CPU."
- **Correct**: CPU-side command recording and submission cost is driven by the number and type of API calls, state changes, and descriptor updates -- not by shader complexity or GPU workload size.

### Synchronization and async operations

#### Async compute / copy does not block the CPU

- **Wrong**: "The async compute work is causing a CPU stall."
- **Correct**: Work submitted to async compute or copy queues does not block the CPU timeline unless the application explicitly waits on a fence tied to that work. If a CPU stall coincides with async GPU work, the stall is caused by whatever fence or event the CPU is waiting on -- identify the specific synchronization point.

#### Fence waits vs work completion

- **Wrong**: "The CPU is waiting for the GPU to finish [specific pass]."
- **Correct**: The CPU waits on a **fence value**, not on a specific pass. The fence may be signaled after multiple passes complete. Identify which fence the CPU is waiting on and what GPU work signals that fence.

### Barrier and synchronization costs

#### Barriers have separate CPU and GPU costs

- **Wrong**: "Barriers are expensive".
- **Correct**: Resource barriers have two distinct costs at different points in time:

  1. **CPU cost**: recording the barrier into the command buffer (typically negligible per-barrier, but can accumulate with hundreds per frame).
  2. **GPU cost**: cache flush / invalidate and possible decompression (varies enormously by resource size, transition type, split-vs-immediate).

  Always check and specify which cost you mean and cite measurements for the specific barrier(s) in question.

#### Barrier storms: count matters, but not all barriers are equal

- **Wrong**: "This frame has 200 barriers, so barriers are the bottleneck."
- **Correct**: Barrier count alone does not determine cost. A barrier transitioning a small buffer between shader stages costs far less than one decompressing a render target. Evaluate barrier cost by measuring GPU time consumed by barrier operations, not by counting them.

### Draw calls and rendering cost

#### Draw-call count is not the primary cost driver

- **Wrong**: "The frame has 5000 draw calls, so draw-call overhead is the problem."
- **Correct**: On modern APIs (D3D12, Vulkan), per-draw CPU overhead is minimal because command recording is explicit and multi-threaded. The cost drivers are: state changes between draws (PSO switches, root signature / pipeline-layout changes, descriptor table / set updates), command-buffer structure, and GPU-side work per draw. A frame with 5000 draws but few state changes may be faster than one with 500 draws and frequent PSO switches.

### Memory and bandwidth

#### Theoretical peak bandwidth is not achieved bandwidth

- **Wrong**: "The GPU has 1 TB/s bandwidth, so this shader should be able to read X GB in Y ms."
- **Correct**: Achieved memory bandwidth depends on access pattern, cache behavior, and contention. Real-world utilization is typically 60-85% of theoretical peak for well-optimized compute workloads, lower for mixed graphics workloads. Use measured bandwidth (from profiler SOL metrics) rather than theoretical calculations.

#### VRAM capacity vs bandwidth

- **Wrong**: "The game uses 8 GB of VRAM, so memory is under pressure."
- **Correct**: VRAM capacity usage and bandwidth usage are independent concerns. A game can use most of VRAM without any bandwidth bottleneck (textures resident but not actively sampled), or it can have severe bandwidth pressure while using a fraction of capacity. Identify which dimension is the actual concern.

### Timing and measurement

#### API wall-clock duration is not active CPU time

- **Wrong**: "``UpdateTileMappings`` / ``vkAllocateMemory`` took 14.5 ms -- that's 14.5 ms of CPU work."
- **Correct**: API call durations from ``DX12_API`` / ``DXGI_API`` / ``VULKAN_API`` tables are **wall-clock** from call start to call return. That includes: (a) on-CPU execution, (b) kernel lock waits (e.g. DXGI Present contending with DWM), (c) user-mode waits (e.g. fence waits), (d) scheduling delays while the thread is runnable but off-CPU. A 14.5 ms call may be 2 ms of CPU work and 12.5 ms blocked. Distinguish wall-clock from active CPU time using ``SCHED_EVENTS`` to see on-CPU vs blocked within the call window.

#### Present / vkQueuePresentKHR latency vs frame time

- **Wrong**: "Present takes 5 ms, which is adding to frame time."
- **Correct**: Present latency (time from CPU call to actual flip / display) includes wait time for vsync, compositor, and display refresh. This latency is largely not the application's GPU/CPU work. Distinguish between: (a) CPU time spent in the Present call (which may include a blocking wait), (b) GPU time for any associated copy/composite, and (c) display latency (vsync alignment, present-mode queueing).

### Investigation discipline

#### Reversed causation

GPU idle, paging bursts, and fence waits during a slow window are often **consequences**, not causes. Always trace backward to find the initiator (the operation that pushed VRAM over budget, the thread that took the lock, the API call that blocked).
