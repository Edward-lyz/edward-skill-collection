# GPU bubble

**Short:** A gap in GPU execution where one or more engines sit idle with no work queued, even though the application has more work to do; visible on the timeline as empty space between GPU activity bars.

**Details:**

- A bubble means the submission pipeline could not keep the GPU fed: the CPU was slow to record and submit, a host-side stall blocked submission, or a fence wait paused a queue.
- Bubbles are the visual signature of a CPU-bound frame on the GPU side; the matching CPU thread is usually idle or blocked on a sync object.
- A bubble on one engine can come from a hand-off to another: a 3D engine waiting for a Copy engine's upload, or vice versa; cross-engine fences make this explicit.
- Not every gap is a bubble. Vsync-paced workloads intentionally idle the GPU after Present; a gap inside a frame is a problem, a gap after Present is by design.
- Fixes typically involve recording command buffers earlier, parallelizing recording, double-buffering work, or removing stalls in the submission path.

**See also:**

- [CPU bound](cpu-bound.md)
- [GPU bound](gpu-bound.md)
- [GPU engine](gpu-engine.md)
- [Stutter](stutter.md)
- [VSync](vsync.md)
