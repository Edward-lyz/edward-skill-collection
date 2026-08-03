# FPS and frame time

**Short:** Frame time is the duration of a single rendered frame; FPS is its reciprocal, usually averaged over a window of frames.

**Details:**

- Frame time is measured between two consecutive frame boundaries, typically successive present calls on the CPU side, or between the first GPU workloads of successive frames on the GPU side.
- FPS is a derived headline number; frame time is the underlying signal and is more useful when diagnosing smoothness.
- A high average FPS can still feel bad if individual frames spike, so distributions and percentiles (for example the 99th percentile frame time) matter as much as the mean.
- Stutter is usually defined as a frame whose time deviates sharply from its neighbors, even when the overall average is healthy.
- Target frame time depends on the display: 16.7 ms for 60 Hz, 6.94 ms for 144 Hz, and so on; missing the target by even a small amount can cause a dropped frame under VSync.
- CPU frame time and GPU frame time can differ; comparing them is the primary way to tell whether a workload is CPU-bound or GPU-bound.

**See also:**

- [Graphics frame](graphics-frame.md)
- [Frame boundary / Present](frame-boundary-present.md)
- [CPU bound](cpu-bound.md)
- [GPU bound](gpu-bound.md)
- [VSync](vsync.md)
