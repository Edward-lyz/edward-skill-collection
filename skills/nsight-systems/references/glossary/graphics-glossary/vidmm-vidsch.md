# VidMm / VidSch

**Short:** VidMm is the video memory manager and VidSch is the video scheduler, two cooperating components inside the Windows graphics kernel that manage GPU memory and GPU work execution.

**Details:**

- VidMm tracks GPU allocations across video memory segments, system memory, and shared pools, and decides what is resident on the GPU at any moment.
- VidMm enforces per-process memory budgets, evicts allocations under pressure, and issues paging operations to move data between segments.
- VidSch maintains per-context queues of GPU work, picks the next packet to run on each GPU engine, and handles preemption, priorities, and quanta.
- VidSch produces DMA packets from queued command buffers and signals fences when work completes.
- With hardware-accelerated GPU scheduling, dispatch shifts to HwQueue and HwSchedDmaPacket events alongside the legacy DMA stream.
- Both components emit detailed telemetry that is the primary source of system-level GPU traces: scheduling packets, paging operations, residency changes, and memory budget transitions.

**See also:**

- [ETW](etw.md)
- [DxgKrnl events](dxgkrnl-events.md)
- [WDDM](wddm.md)
- [ETW provider mask](etw-provider-mask.md)
