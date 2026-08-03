# WDDM

**Short:** Windows Display Driver Model is the architecture Windows uses for graphics drivers, splitting them between user mode and kernel mode and arbitrating GPU access through the OS.

**Details:**

- A WDDM driver has two halves: a user-mode driver (UMD) loaded into each graphics process, and a kernel-mode driver (KMD) loaded by the OS graphics kernel.
- The OS graphics kernel (dxgkrnl) sits above the KMD and owns the video scheduler, the video memory manager, synchronization primitives, and adapter and display enumeration.
- Work is expressed as command buffers submitted to per-context queues; the scheduler turns these into DMA packets that the GPU executes.
- WDDM introduces the concepts of adapter, device, context, allocation, and synchronization object, all referenced by OS-level handles.
- WDDM is the boundary where graphics APIs like D3D and Vulkan meet the OS, so most system-level GPU telemetry is described in WDDM terms.

**See also:**

- [ETW](etw.md)
- [DxgKrnl events](dxgkrnl-events.md)
- [VidMm / VidSch](vidmm-vidsch.md)
- [ETW provider mask](etw-provider-mask.md)
