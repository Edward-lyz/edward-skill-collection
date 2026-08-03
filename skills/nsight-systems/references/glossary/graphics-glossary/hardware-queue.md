# Hardware queue

**Short:** A hardware queue is a GPU-scheduled submission queue introduced with WDDM 2.7 hardware scheduling, in which the GPU itself rather than the OS decides when each queued packet runs on an engine.

**Details:**

- When hardware-accelerated GPU scheduling (HWS) is enabled, each user-mode context binds to one or more hardware queues, and the firmware dequeues packets directly without a CPU-side software queue step.
- Lifecycle events ``HwQueue`` create, destroy, and state-change describe when a queue exists and what context it serves; per-packet activity is reported as ``HwSchedDmaPacket_Begin`` and ``_End`` rather than ``DmaPacket_Start`` / ``_Stop``.
- One context can map to several hardware queues (a parent queue with child queues for different engines), which lets a tool group activity back to a single submission.
- HWS reduces CPU overhead on submit and lowers Present-to-scan-out latency, but it changes which ETW events carry the truth: with HWS off, look at DmaPackets; with HWS on, look at HwSchedDmaPackets.
- The packet payload (engine type, submission sequence, fence values, fault flags) is the same regardless of scheduling path.

**See also:**

- [DMA packet](dma-packet.md)
- [Queue packet](queue-packet.md)
- [GPU engine](gpu-engine.md)
- [DxgKrnl events](dxgkrnl-events.md)
- [WDDM](wddm.md)
