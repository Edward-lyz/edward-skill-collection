---
source_path: UserGuide/topics/unified-memory-transfer-trace.rst
title: ## Unified Memory Transfer Trace
---
## Unified Memory Transfer Trace

For Nsight Systems Workstation Edition, Unified Memory (also called Managed Memory) transfer trace is enabled automatically in Nsight Systems when CUDA trace is selected. It incurs no overhead in programs that do not perform any Unified Memory transfers. Data is displayed in the Managed Memory area of the timeline:

   :alt: UVM trace
   :class: image

**HtoD transfer** indicates the CUDA kernel accessed managed memory that was residing on the host, so the kernel execution paused and transferred the data to the device. Heavy traffic here will incur performance penalties in CUDA kernels, so consider using manual cudaMemcpy operations from pinned host memory instead.

**PtoP transfer** indicates the CUDA kernel accessed managed memory that was residing on a different device, so the kernel execution paused and transferred the data to this device. Heavy traffic here will incur performance penalties, so consider using manual cudaMemcpyPeer operations to transfer from other devices' memory instead. The row showing these events is for the destination device - the source device is shown in the tooltip for each transfer event.

**DtoH transfer** indicates the CPU accessed managed memory that was residing on a CUDA device, so the CPU execution paused and transferred the data to system memory. Heavy traffic here will incur performance penalties in CPU code, so consider using manual cudaMemcpy operations from pinned host memory instead.

Some Unified Memory transfers are highlighted with red to indicate potential performance issues:

   :alt: Unified Memory transfer migration cause highlight
   :class: image

Transfers with the following migration causes are highlighted:

-  **Coherence**

   Unified Memory migration occurred to guarantee data coherence. SMs (streaming multiprocessors) stop until the migration completes.

-  **Eviction**

   Unified Memory migrated to the CPU because it was evicted to make room for another block of memory on the GPU. This happens due to memory overcommitment which is available on Linux with Compute Capability ≥ 6.
