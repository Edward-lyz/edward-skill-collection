# Queue packet

**Short:** A queue packet is a software-queue entry the OS graphics scheduler creates when an application submits work to a GPU context, before the work is dispatched to a hardware engine as a DMA packet.

**Details:**

- The packet sits on a per-context software queue inside the OS graphics kernel and represents one of: a render command buffer, a paging operation, a wait on a fence, a signal of a fence, an MMIO flip, or a software command buffer such as Present.
- On Windows it is bracketed by ``QueuePacket_Start``, optional ``QueuePacket_Info``, and ``QueuePacket_Stop`` ETW events and identified by a submission sequence number and an ``hContext``.
- The Start-to-Stop interval is the packet's residency in the software queue, roughly the "submitted but not yet retired" lifetime; the embedded DMA packet shows the actual engine time.
- Queue packets are what the timeline uses to show CPU-side queue depth: how many submissions are outstanding ahead of the work the GPU is currently running.

**See also:**

- [DMA packet](dma-packet.md)
- [Hardware queue](hardware-queue.md)
- [DxgKrnl events](dxgkrnl-events.md)
- [Command list and queue](command-list-queue.md)
- [WDDM](wddm.md)
