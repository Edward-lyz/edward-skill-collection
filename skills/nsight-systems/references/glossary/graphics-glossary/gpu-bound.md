# GPU-bound frame

**Short:** A frame whose end-to-end duration is gated by GPU execution; the CPU finishes submitting work and then waits for the GPU.

**Details:**

- The GPU is the bottleneck when rendering, compute, or copy work for a frame takes longer than the CPU needs to record and submit it.
- Typical signs are a GPU that is busy back-to-back across frames, a CPU thread that finishes early and idles, and frame time that scales with resolution, quality settings, or effects.
- Common causes include heavy pixel shaders at high resolution, expensive post-processing, large geometry or overdraw, and memory bandwidth limits.
- Lowering resolution, render scale, or shader quality usually helps, because the limit is on the rendering side.
- A long GPU frame paired with a short and idle-tailed CPU frame is the visual signature of a GPU-bound workload on a timeline.
- A run can flip between GPU-bound and CPU-bound across scenes, so the classification belongs to the frame, not the application as a whole.

**See also:**

- [CPU bound](cpu-bound.md)
- [FPS and frame time](fps-frame-time.md)
- [Graphics frame](graphics-frame.md)
- [WDDM](wddm.md)
