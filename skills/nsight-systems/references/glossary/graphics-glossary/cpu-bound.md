# CPU-bound frame

**Short:** A frame whose end-to-end duration is gated by CPU work rather than by GPU execution.

**Details:**

- The CPU is the bottleneck when game logic, draw-call recording, or driver submission take longer than the GPU needs to render the resulting work.
- Typical signs are a fully busy main or render thread, a GPU that goes idle between frames, and frame time that scales with CPU clock or thread count rather than GPU settings.
- Common causes include too many draw calls, expensive simulation or scripting, contention on a single thread, and synchronous readbacks that stall the CPU on the GPU.
- Lowering graphics quality usually does not help a CPU-bound frame, because the limit is on the submission side, not the rendering side.
- Mitigations include batching draws, moving work to worker threads, reducing per-frame allocations, and avoiding API patterns that force the CPU to wait on the GPU.
- A run can shift between CPU-bound and GPU-bound across scenes, so the classification is per workload, not per title.

**See also:**

- [GPU bound](gpu-bound.md)
- [FPS and frame time](fps-frame-time.md)
- [Graphics frame](graphics-frame.md)
- [Reflex render latency](reflex-render-latency.md)
