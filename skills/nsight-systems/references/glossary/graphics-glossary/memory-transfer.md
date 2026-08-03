# Memory Transfer

**Short:** A copy of bytes between system (CPU) memory and device (GPU) memory, or between two device memory regions, as reported on a GPU memory row.

**Details:**

- nsys classifies direction with the WDDM ``MemoryTransferType`` enum: ``UnknownTransfer``, ``SystemToDevice``, ``DeviceToSystem``, ``AgpToDevice``, ``DeviceToAgp``, ``EvictToAlternateva``, ``RestoreFromAlternateva``, ``Discard``.
- System buffers can be pageable or pinned (page-locked). Pinned memory enables true asynchronous DMA and typically reaches higher sustained throughput because the OS cannot move the pages mid-transfer.
- Synchronous calls block the issuing thread until the copy finishes; asynchronous calls return immediately and queue work onto a GPU copy engine, allowing overlap with rendering and with other copies.
- On the device, transfers are executed by dedicated copy engines that run independently from the 3D engine. A GPU typically exposes one or more such engines, which is why a ``SystemToDevice`` copy and a ``DeviceToSystem`` copy can run concurrently with draw work when scheduled on separate queues.
- A transfer's duration depends on payload size plus the bandwidth of the underlying link (PCIe, NVLink, or on-chip memory bus).

**See also:**

- [Bandwidth usage](../nsys-glossary/bandwidth-usage.md)
- [Resource migration](resource-migration.md)
