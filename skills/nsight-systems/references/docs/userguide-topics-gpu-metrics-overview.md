---
source_path: UserGuide/topics/gpu-metrics-overview.rst
title: ## GPU Metrics
---
## GPU Metrics


#### Overview

GPU Metrics feature is intended to identify performance limiters in applications
using GPU for computations and graphics. It uses periodic sampling to gather
performance metrics and detailed timing statistics associated with different GPU
hardware units taking advantage of specialized hardware to capture this data in
a single pass with minimal overhead.

Note:
   GPU Metrics will give you precise device level information, but it does not know which process or context is involved. GPU context switch trace provides less precise information, but will give you process and context information.


   :alt: Example report with GPU Metrics
   :class: image

These metrics provide an overview of GPU efficiency over time within compute,
graphics, and input/output (IO) activities such as:

-  **IO throughputs:** PCIe, NVLink, and GPU memory bandwidth
-  **SM utilization:** SMs activity, tensor core activity, instructions issued,
   warp occupancy, and unassigned warp slots

It is designed to help users answer the common questions:

-  Is my GPU idle?
-  Is my GPU full? Enough kernel grids size and streams? Are my SMs and warp
   slots full?
-  Am I using TensorCores?
-  Is my instruction rate high?
-  Am I possibly blocked on IO, or number of warps, etc.?

Nsight Systems GPU Metrics is only available for Linux targets on x86-64 and
aarch64, and for Windows targets. It requires NVIDIA Turing architecture or
newer.

Minimum required driver versions:

-  NVIDIA Turing architecture TU10x, TU11x - r440
-  NVIDIA Ampere architecture GA100 - r450
-  NVIDIA Ampere architecture GA100 MIG - r470 TRD1
-  NVIDIA Ampere architecture GA10x - r455

Note:

   **Permissions:** Elevated permissions are required. On Linux use sudo to
   elevate privileges. On Windows the user must run from an admin command prompt
   or accept the UAC escalation dialog. See `Permissions Issues and Performance
   Counters <https://developer.nvidia.com/ERR_NVGPUCTRPERM>`__ for more information.

Note:

   **Tensor Core:** If you run ``nsys profile --gpu-metrics-devices all``, the
   Tensor Core utilization can be found in the GUI under the
   **SM instructions/Tensor Active** row.

   Note that it is not practical to expect a CUDA kernel to reach 100%
   Tensor Core utilization since there are other overheads. In general, the more
   computation-intensive an operation is, the higher Tensor Core utilization
   rate the CUDA kernel can achieve.
