---
source_path: UserGuide/topics/vulkan-overview.rst
title: ## Vulkan Overview
---
## Vulkan Overview

Vulkan is a low-overhead, cross-platform 3D graphics and compute API, targeting a wide variety of devices from PCs to mobile phones and embedded platforms. The Vulkan API is defined by the Khronos Group. Information about Vulkan and the Khronos Group can be found at the Khronos Vulkan Site .

Nsight Systems can capture information about Vulkan usage by the profiled process. This includes capturing the execution time of Vulkan API functions, corresponding GPU workloads, debug util labels, and frame durations. Vulkan profiling is supported on both Windows and x86 Linux operating systems.

   :alt: Vulkan overview picture
   :class: image

The Command Buffer Creation row displays time periods when command buffers were being created. This enables developers to improve their application’s multi-threaded command buffer creation. Command buffer creation time period is measured between the call to ``vkBeginCommandBuffer`` and the call to ``vkEndCommandBuffer``.

   :alt: Vulkan command buffer creation
   :class: image

A Queue row is displayed for each Vulkan queue created by the profiled application. The API sub-row displays time periods where ``vkQueueSubmit`` was called. The GPU Workload sub-row displays time periods where workloads were executed by the GPU.

   :alt: Vulkan API and Workload
   :class: image

In addition, you can see Vulkan debug util labels  on both the CPU and the GPU.

   :alt: Vulkan CPU marker
   :class: image

Clicking on a GPU workload highlights the corresponding ``vkQueueSubmit`` call, and vice versa.

   :alt: Vulkan correlation
   :class: image

The Vulkan Memory Operations row contains an aggregation of all the Vulkan host-side memory operations, such as host-blocking writes and reads or non-persistent map-unmap ranges.

The row is separated into sub-rows by heap index and memory type - the tooltip for each row and the ranges inside show the heap flags and the memory property flags.

   :alt: Vulkan Memory Operations
   :class: image

   :alt: Vulkan Memory Operations
   :class: image
