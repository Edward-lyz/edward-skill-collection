# Resource migration

**Short:** The movement of a GPU allocation from one memory segment to another, typically between dedicated VRAM and shared system memory, while the allocation stays logically alive.

**Details:**

- On Windows, the video memory manager evicts allocations from local VRAM to non-local system memory (paging across PCIe) when the working set exceeds the device budget. The allocation is paged back in before its next use.
- Migration is not free. The bytes traverse PCIe (or NVLink) twice over an eviction-restore cycle, and the consuming draw call stalls until the resource is resident again.
- In a trace, migration appears as a gap or latency spike near a draw call, often correlated with a bandwidth burst on the link and with paging activity in the kernel-mode driver.
- Frequent migration is a red flag for budget overcommit. Fixes include reducing working-set size or adjusting priorities so hot resources stay resident.

**See also:**

- [VidMm / VidSch](vidmm-vidsch.md)
- [WDDM](wddm.md)
- [DxgKrnl events](dxgkrnl-events.md)
- [Memory transfer](memory-transfer.md)
