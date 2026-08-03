# SM, warp, occupancy

**Short:** The execution-unit hierarchy on NVIDIA GPUs: an SM runs warps of 32 threads in SIMT, and occupancy measures how many warps are resident relative to the hardware maximum.

**Details:**

- A Streaming Multiprocessor (SM) is the basic execution block; a GPU contains many SMs, each with its own schedulers, register file, shared memory, and execution units.
- A warp is a group of 32 threads executed in lockstep under the SIMT model; divergent branches serialize the diverging lanes within the warp.
- Occupancy is ``resident warps / max resident warps per SM``; the cap is set by hardware (commonly 48 or 64 warps per SM, depending on architecture).
- Per-block resource demands cap occupancy: register count per thread, shared memory per block, threads per block, and the maximum resident block count all reduce how many warps can co-reside on an SM.
- "SM active" means the SM is executing any work at all (one resident warp is enough), while "achieved occupancy" is the time-averaged ratio of warps-in-flight to the warp cap; an SM can be 100 percent active yet have low achieved occupancy.

**See also:**

- [GPU metrics](gpu-metrics.md)
- [GPU bound](../graphics-glossary/gpu-bound.md)
