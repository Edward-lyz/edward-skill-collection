---
source_path: AnalysisGuide/topics/available-recipes.rst
title: ## Available Advanced Analysis Recipes
---
## Available Advanced Analysis Recipes

All advanced analysis recipes are run using the ``recipe`` CLI command switch.

usage:


   nsys recipe [args] <recipe-name> [recipe args]

Nsight Systems provides several initial analysis recipes, mostly based around
making our existing statistics and expert systems rules run multi-report.

These recipes can be found at
``<target-linux-x64>/python/packages/nsys-recipe/recipes``.
Please note that all recipes are in the form of python scripts. You may alter
the given recipes or write your own to meet your needs. Refer to
Tutorial: Create a User-Defined Recipe <create user-defined recipe> for an example of how to do this.
However, be advised that the APIs may change for the next few versions. Additional
recipes will be added on an ongoing basis.

For more information about a specific recipe, including recipe parameters,
please use ``nsys recipe [recipe name] --help``.

**List of recipes**

Each recipe will be tagged with one or more keywords to help understand its
purpose.

   :name: table_multirecipe_table
   :class: table-compact

   +------------------+-------------------------------------------------------------+
   | Keywords         | Description                                                 |
   +==================+=================================+===========================+
   | Expert System    | The recipe originated from the Expert System. A script      |
   |                  | with the same name is also available via ``nsys analyze``,  |
   |                  | but its behavior and implementation may differ.             |
   +------------------+-------------------------------------------------------------+
   | Stats System     | The recipe originated from the Stats System. A script       |
   |                  | with the same name is also available via ``nsys stats``,    |
   |                  | but its behavior and implementation may differ.             |
   +------------------+-------------------------------------------------------------+
   | Trace            | The recipe provides a trace record of individual events     |
   |                  | that are observable in the GUI timeline.                    |
   +------------------+-------------------------------------------------------------+
   | Summary          | The recipe provides a summarized view of events, often      |
   |                  | representing aggregated data.                               |
   +------------------+-------------------------------------------------------------+
   | Pace             | The recipe provides a detailed analysis of how a            |
   |                  | specific event progresses across the application.           |
   +------------------+-------------------------------------------------------------+
   | Heatmap          | The recipe provides a heatmap that visualizes patterns      |
   |                  | across the application.                                     |
   +------------------+-------------------------------------------------------------+


-   cuda_api_sum : CUDA API Summary
        This recipe provides a summary of CUDA API functions and their execution
        times.

        Keywords: CUDA, Summary, Stats System
-   cuda_api_sync : CUDA Synchronization APIs
        This recipe identifies synchronization APIs that block the host until
        the issued CUDA calls are complete.

        Keywords: CUDA, Synchronization, Trace, Expert System
-   cuda_gpu_kern_hist : CUDA GPU Kernel Duration Histogram
        This recipe represents the probability of the duration of a CUDA kernel 
        among all its instances or all kernels in the program.

        Keywords: CUDA, Kernel, Histogram, Duration
-   cuda_gpu_kern_pace : CUDA GPU Kernel Pacing
        This recipe investigates the progress and consistency of a particular
        CUDA kernel throughout the application.

        Keywords: CUDA, Kernel, Pace
-   cuda_gpu_kern_sum : CUDA GPU Kernel Summary
        This recipe provides a summary of CUDA kernels and their execution times.

        Keywords: CUDA, Kernel, Summary, Stats System
-   cuda_gpu_mem_size_sum : CUDA GPU MemOps Summary (by Size)
        This recipe provides a summary of GPU memory operations and the amount
        of memory they utilize.

        Keywords: CUDA, Memory, Summary, Stats System
-   cuda_gpu_mem_time_sum : CUDA GPU MemOps Summary (by Time)
        This recipe provides a summary of GPU memory operations and their
        execution times.

        Keywords: CUDA, Memory, Summary, Stats System
-   cuda_gpu_time_util_map : CUDA GPU Time Utilization Heatmap
        This recipe calculates the percentage of time that CUDA kernels were
        running.

        Keywords: CUDA, Kernel, Heatmap
-   cuda_memcpy_async : CUDA Async Memcpy with Pageable Memory
        This recipe identifies asynchronous memory transfers that end up
        becoming synchronous if the memory is pageable.

        Keywords: CUDA, Memcpy, Trace, Expert System
-   cuda_memcpy_sync : CUDA Synchronous Memcpy
        This recipe identifies memory transfers that are synchronous.

        Keywords: CUDA, Memcpy, Trace, Expert System
-   cuda_memset_sync : CUDA Synchronous Memset
        This recipe identifies synchronous memset operations with pinned host
        memory or Unified Memory region.

        Keywords: CUDA, Memset, Trace, Expert System
-   diff : Statistics Diff
        This script compares outputs from two runs of the same statistical recipe.

        Keywords: Diff, Summary
-   dx12_mem_ops : DX12 Memory Operations
        This recipe flags problematic memory operations with warnings.

        Keywords: DX12, Memory, Trace, Expert System
-   file_access_sum : OS Runtime File Access Summary
        This recipe provides a summary of file access functions, including high-level overview
        of file access patterns across the system.

        For details and use cases of this recipe, see file_access_sum Recipe.

        Keywords: OSRT, Summary
-   gfx_hotspot : Graphics Hotspot Analysis
        This recipe generates a report of CPU hotspots for graphics applications.

        The output format for this recipe is different than other recipes. See
        gfx_hotspot Recipe.

        Keywords: DX12, Vulkan, Summary, Trace
-   gpu_gaps : GPU Gaps
        This recipe identifies time regions where a GPU is idle for longer than
        a set threshold.

        Keywords: CUDA, Utilization, Expert System
-   gpu_metric_util_map : GPU Metric Utilization Heatmap
        This recipe calculates the percentage of SM Active, SM Issue, and
        Tensor Active metrics.

        Keywords: GPU Metrics, Heatmap
-   gpu_metric_util_sum : GPU Metrics Utilization Summary
        This recipe provides a summary of different GPU metrics. GPU metrics
        are based on binary inclusion. Any ranges that do not include at least
        one sampling point are excluded from the output.

        Keywords: GPU Metrics, Summary
-   gpu_time_util : GPU Time Utilization
        This recipe identifies time regions with low GPU utilization.

        Keywords: CUDA, Utilization, Expert System
-   gpu_vram_usage_trace : GPU VRAM Usage Trace
        This recipe traces the VRAM usage of GPU workloads, allowing comparison of changes between CPU frames,
        and identifying issues in resource migration between VRAM and SYSMEM, and with resource allocation & deallocation.

        For details and use cases of this recipe, see gpu_vram_usage_trace Recipe.

        Keywords: VRAM, Trace
-   mpi_gpu_time_util_map : MPI and GPU Time Utilization Heatmap
        This recipe calculates the percentage of time that CUDA kernels were
        running and MPI communication was active, as well as their overlap.

        Keywords: MPI, CUDA, Kernel, Utilization, Heatmap
-   mpi_sum : MPI Summary
        This recipe provides a summary of MPI functions and their execution times.

        Keywords: MPI, Summary
-   nccl_gpu_overlap_trace : NCCL GPU Overlap Trace
        This recipe calculates the percentage of overlap for communication and
        compute kernels. Communication kernels are identified by the 'nccl'
        prefix.

        Keywords: NCCL, CUDA, Kernel, Overlap, Trace
-   nccl_gpu_proj_sum : NCCL GPU Projection Summary
        This recipe provides a summary of NCCL functions projected from the CPU
        onto the GPU. For advanced NCCL tracing, use nccl_sum instead because
        GPU projection is unnecessary.

        Keywords: NCCL, CUDA, GPU Projection, Summary
-   nccl_gpu_time_util_map : NCCL GPU Time Utilization Heatmap
        This recipe calculates the percentage of time that communication and
        compute kernels were running, as well as their overlap. Communication
        kernels are identified by the 'nccl' prefix.

        Keywords: NCCL, CUDA, Kernel, Utilization, Overlap, Heatmap
-   nccl_straggler : NCCL Straggler
        This recipe analyzes NCCL collective timing to identify ranks that
        repeatedly delay communicator progress. It requires advanced NCCL
        tracing.

        Keywords: NCCL, Straggler, Collective, Heatmap
-   nccl_sum : NCCL Summary
        This recipe provides a full-run NCCL communication summary over
        communicators, operations, message sizes, datatypes, and ranks.

        Keywords: NCCL, Summary
-   network_map_aws : AWS Metrics Heatmap
        This recipe displays heatmaps of AWS EFA metrics.

        Keywords: Network, AWS, EFA, Heatmap
-   network_sum : Network Traffic Summary
        This recipe provides a summary of the network traffic over NICs and
        InfiniBand Switches.

        Keywords: Network, Summary
-   network_traffic_map : Network Devices Traffic Heatmap
        This recipe displays heatmaps of sent traffic, received traffic, and
        congestion events for network devices.

        Keywords: Network, Heatmap
-   nvtx_cpu_topdown : CPU Topdown methodology metrics correlated to NVTX ranges
        This recipe calculates CPU Topdown methodology metrics for NVTX
        push/pop ranges based on collected PMU core events for NVIDIA CPUs
        featuring Arm cores.

        For details and use cases of this recipe, see nvtx_cpu_topdown Recipe.

        Keywords: NVTX, CPU Topdown, Metrics, Summary
-   nvlink_sum : NVLink Network Throughput Summary
        This recipe provides a summary of the NVLink network throughput.

        Keywords: NVLink, Summary
-   nvtx_gpu_proj_pace : NVTX GPU Projection Pacing
        This recipe investigates the progress and consistency of a particular
        NVTX range projected from the CPU onto the GPU, throughout the
        application.

        Keywords: NVTX, GPU Projection, Pace
-   nvtx_gpu_proj_sum : NVTX GPU Projection Summary
        This recipe provides a summary of NVTX time ranges projected from the
        CPU onto the GPU, and their execution times.

        Keywords: NVTX, GPU Projection, Summary, Stats System
-   nvtx_gpu_proj_trace : NVTX GPU Projection Trace
        This recipe provides a trace of NVTX time ranges projected from the CPU
        onto the GPU.

        Keywords: NVTX, GPU Projection, Trace, Stats System
-   nvtx_pace : NVTX Pacing
        This recipe investigates the progress and consistency of a particular
        NVTX range throughout the application.

        Keywords: NVTX, Pace
-   nvtx_sum : NVTX Range Summary
        This recipe provides a summary of NVTX Start/End and Push/Pop Ranges,
        and their execution times.

        Keywords: NVTX, Summary, Stats System
-   osrt_sum : OS Runtime Summary
        This recipe provides a summary of C library functions and their
        execution times.

        Keywords: OSRT, Summary, Stats System
-   s3_access_sum : S3 Access Summary
        This recipe provides a summary of S3 object store access across traced S3 client libraries.

        For details and use cases of this recipe, see s3_access_sum Recipe.

        Keywords: S3, Storage, Summary
-   storage_util_map : Storage Metrics Heatmap
        This recipe displays heatmaps of storage devices metrics.

        Keywords: Storage, Heatmap
-   ucx_gpu_time_util_map : UCX and GPU Time Utilization Heatmap
        This recipe calculates the percentage of time that CUDA kernels were
        running and UCX communication was active, as well as their overlap.

        Keywords: UCX, CUDA, Kernel, Heatmap
