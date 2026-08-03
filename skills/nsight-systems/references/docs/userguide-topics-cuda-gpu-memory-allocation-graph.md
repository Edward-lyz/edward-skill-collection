---
source_path: UserGuide/topics/cuda-gpu-memory-allocation-graph.rst
title: ## CUDA GPU Memory Allocation Graph
---
## CUDA GPU Memory Allocation Graph

When the **Collect GPU Memory Usage** option is selected from the **Collect CUDA
trace** option set, Nsight Systems will track CUDA GPU memory allocations and
deallocations and present a graph of this information in the timeline. This is
not the same as the GPU memory graph generated during stutter analysis on the
Windows target. See Windows GPU Memory Utilization.

Below, in the report on the left, memory is allocated and freed during the
collection. In the report on the right, memory is allocated, but not freed
during the collection.

   :alt: CUDA memory allocation graphs where the memory is or is not released during application run
   :class: image

Here is another example, where allocations are happening on multiple GPUs.

   :alt: CUDA memory usage graph on multiple threads
   :class: image

Nsight Systems uses CUPTI for CUDA profiling, including to collect the CUDA
memory usage by the application processes. CUPTI tracks various kinds of memory
allocations and deallocations done by the user application that is being
profiled. See: CUPTI documentation .


..

  CUPTI_ACTIVITY_MEMORY_KIND_PAGEABLE = 1
  The memory is pageable.
  CUPTI_ACTIVITY_MEMORY_KIND_PINNED = 2
  The memory is pinned.
  CUPTI_ACTIVITY_MEMORY_KIND_DEVICE = 3
  The memory is on the device.
  CUPTI_ACTIVITY_MEMORY_KIND_ARRAY = 4
  The memory is an array.
  CUPTI_ACTIVITY_MEMORY_KIND_MANAGED = 5
  The memory is managed
  CUPTI_ACTIVITY_MEMORY_KIND_DEVICE_STATIC = 6
  The memory is device static
  CUPTI_ACTIVITY_MEMORY_KIND_MANAGED_STATIC = 7
  The memory is managed static 


There are three graphs shown in nsys GUI timeline. One graph is called the
"Memory usage" under each GPU. It is the sum of memory kinds device and array
used by that process. The graph increases when memory allocation APIs (such as
cudaMalloc, cudaMallocManaged) are called and the graph decreases when memory
deallocation APIs (such as cudaFree) are called.

   :alt: CUDA memory allocation graphs aligned with cudaMalloc calls
   :class: image
 
The second graph, titled 'Managed Memory usage', shows the managed memory
kind, in this case CUPTI_ACTIVITY_MEMORY_KIND_MANAGED, used by that process.

   :alt: CUDA memory allocation graphs both kinds
   :class: image

The third graph called "Static Memory usage" is the sum of memory kind device
static and managed static used by the process: 

*  CUPTI_ACTIVITY_MEMORY_KIND_DEVICE_STATIC is a static memory allocation. It
   does not have a context. Since it is static, it is allocated by variable
   declaration. For example, __device__ int var;

*  CUPTI_ACTIVITY_MEMORY_KIND_MANAGED_STATIC s static managed allocation. For
   example, __device__  __managed__ int var; In other words, this is static
   equivalent of cudaMallocManaged() API.
   
   :alt: all three of the memory usage graphs
   :class: image   

The pageable and pinned are both host-side memory calls, so we don't show those
on the GUI timeline.
