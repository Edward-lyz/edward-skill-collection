# Hierarchy row

**Short:** A single horizontal track in the GUI timeline. Built by a hierarchy builder from one or more event tables.

**Details:**

- Examples of hierarchy builders: NVTX (``NVTX_EVENTS`` → nested ranges per thread per domain), DX12 (``DX12_API`` + ``DX12_WORKLOAD`` → per-queue rows), WDDM (``WDDM_QUEUE_*_EVENTS`` → per-engine queue rows), GPU metrics (``GPU_METRICS`` → one row per counter).
- Rows are grouped by source / process / thread / engine in a tree on the left of the timeline; the tree can be collapsed and expanded to control density.
- **GPU rows** show work executing on a device queue or engine (CUDA streams, Vulkan / DX12 queues, video engines, WDDM hardware queues).
- **CPU rows** show per-thread work — sampled stacks, OS-runtime activity, API calls, NVTX ranges.
- Row ordering ("gpu-on-top" / "cpu-on-top") is a GUI preference and also a [DumpTimeline](dumptimeline.md) option.
- Low-utilization rows can be hidden by default. DumpTimeline's ``--show-all`` flag forces them to appear in its JSON output; the GUI offers an equivalent toggle in the timeline view.

**See also:**

- [Nsight Systems timeline](nsys-timeline.md)
- [DumpTimeline](dumptimeline.md)
- [Correlation arrow](correlation-arrow.md)
- *Frame Duration row* — [Rst/UserGuide/topics/fps-overview.md](https://docs.nvidia.com/nsight-systems/UserGuide/)
