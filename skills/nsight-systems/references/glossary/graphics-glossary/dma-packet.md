# DMA packet

**Short:** A DMA packet is a single unit of GPU work dispatched to a specific GPU engine, the smallest granularity at which the OS reports actual on-GPU execution time.

**Details:**

- The GPU scheduler turns a submitted command buffer into one or more DMA packets and hands each to an engine; the packet's lifetime is the engine's execution lifetime.
- On Windows, each packet is bracketed by ``DmaPacket_Start`` and ``DmaPacket_Stop`` ETW events and identified by a ``SubmitSequence`` and an ``hContext``. ``DmaPacket_Info`` events report fence updates.
- The packet carries the engine type and node ordinal of the engine that ran it, so a timeline can stack packets per engine and show real engine utilization.
- Packet types include render, paging, wait-on-fence, signal-fence, and software command buffers (which is how Present flows through the same path).
- A DMA packet can be preempted, page-fault, or time out; those flags appear on the record and drive the UI caption.
- Pairing a packet to the queue packet that produced it ties on-GPU execution back to the CPU-side submit call.

**See also:**

- [Queue packet](queue-packet.md)
- [GPU engine](gpu-engine.md)
- [DxgKrnl events](dxgkrnl-events.md)
- [WDDM](wddm.md)
- [VidMm / VidSch](vidmm-vidsch.md)
