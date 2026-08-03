# GPU metrics

**Short:** Periodically sampled hardware counters from the GPU (SM activity, occupancy, memory bandwidth, tensor / video engine usage, interconnect throughput) shown as plot rows on a timeline.

**Details:**

- Sampled from on-chip performance monitors via NVIDIA's PerfWorks / NVPerf API; a sampling thread reads counter snapshots at a fixed cadence.
- Two broad families: compute and memory (SM active, occupancy, warp issue, tensor active, DRAM throughput, L2 hit rate), and engines and links (NVDEC, NVENC, NVJPG, PCIe, NVLink, power, clocks).
- Sampling frequency trades fidelity for overhead; typical defaults are tens to a few hundred Hz. Higher rates catch micro-bursts but multiply data volume and can perturb the workload.
- Counters are read by the GPU itself, so they stay accurate when CPU and GPU are loosely coupled, including bursty workloads where DMA Start / Stop pairs understate engine activity.
- Independent of any kernel or NVTX instrumentation; you can collect them without recompiling the application.
- Watch for misreads: "SM active" means at least one SM is busy, not full utilization; memory counters report observed traffic, not peak.

**See also:**

- [GPU engine](../graphics-glossary/gpu-engine.md)
- [Bandwidth usage](bandwidth-usage.md)
- [Perf marker](perf-marker.md)
- [CPU sampling](cpu-sampling.md)
