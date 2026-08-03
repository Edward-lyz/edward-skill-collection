# Export tables (SQLite / Parquet)

**Short:** Catalog of the tables produced by ``nsys export``. Each table holds one source of events; almost every text column is an integer ID into a central ``StringIds`` table.

The full schema is documented in the [SQLite Schema Reference](https://docs.nvidia.com/nsight-systems/AnalysisGuide/). Tables are created lazily by default (only those with data appear) — pass ``--lazy=false`` to emit empty tables too.

## Identity / metadata

- ``StringIds`` is the central string lookup table; join almost every ``nameId`` column against it.
- ``PROCESSES`` records the ``pid``, ``globalPid``, and process name for every captured process.
- ``ThreadNames`` maps thread names by ``globalTid``.
- ``TARGET_INFO_GPU`` stores GPU device info (name, UUID, SM count, L2 size, clocks, memory).
- ``TARGET_INFO_PROCESS`` stores per-process info, including OpenGL version.
- ``TARGET_INFO_SESSION_START_TIME`` provides the wall-clock anchor (UTC + local + system clock ns).
- ``ANALYSIS_DETAILS`` records the overall trace start, stop, and duration in ns.
- ``META_DATA_CAPTURE`` and ``META_DATA_EXPORT`` version the report and schema.
- ``PROFILER_OVERHEAD`` marks regions where the profiler itself was busy (subtract from "GPU idle").
- ``ANALYSIS_FILE`` holds files embedded by analysis.
- ``ENUM_*`` tables provide lookup tables for enum-valued columns.

## CPU sampling and scheduling

- ``SAMPLING_CALLCHAINS`` holds periodic CPU stack samples (the orange marks in the timeline) and is the primary CPU hotspot source.
- ``COMPOSITE_EVENTS`` stores composite per-sample info, including thread state at sample time.
- ``SCHED_EVENTS`` records OS thread scheduling run / wait state transitions.
- ``PMU_EVENTS``, ``PMU_EVENT_COUNTERS``, and ``PMU_EVENT_REQUESTS`` capture hardware perf counter data.
- ``OSRT_CALLCHAINS`` stores call stacks for OS-runtime blocking events.

## NVTX

- ``NVTX_EVENTS`` records every NVTX range and marker (start, end, text, domain, category, payload).
- ``NVTX_PAYLOAD_SCHEMAS``, ``_ENTRIES``, ``NVTX_PAYLOAD_ENUMS``, and their ``_ENTRIES`` tables define structured payload schemas.
- ``NVTX_SCOPES`` stores scope definitions for extended NVTX.

## CUDA

- ``CUPTI_ACTIVITY_KIND_RUNTIME`` records CUDA runtime API calls on the CPU side.
- ``CUPTI_ACTIVITY_KIND_KERNEL`` records GPU kernel launches (grid, block, shmem, regs, duration).
- ``CUPTI_ACTIVITY_KIND_MEMCPY``, ``_MEMSET``, and ``_MEM_DECOMPRESS`` record GPU memory operations.
- ``CUPTI_ACTIVITY_KIND_SYNCHRONIZATION`` and ``_CUDA_EVENT`` record sync primitives.
- ``CUPTI_ACTIVITY_KIND_GRAPH_*`` tables record CUDA Graphs (node, host node, trace).
- ``CUPTI_ACTIVITY_KIND_BLOCK_TRACE``, ``_BLOCK_PHASE_TRACE``, ``_WARP_TRACE``, and ``_WARP_PHASE_TRACE`` provide block / warp-level trace data when enabled.
- ``CUPTI_ACTIVITY_KIND_OVERHEAD`` marks CUPTI / driver overhead regions.
- ``CUDA_GPU_MEMORY_USAGE_EVENTS`` and ``_POOL_EVENTS`` record device-memory residency and pool events.
- ``CUDA_UM_CPU_PAGE_FAULT_EVENTS`` and ``_GPU_PAGE_FAULT_EVENTS`` record Unified Memory page faults.
- ``CUDA_CALLCHAINS`` stores CPU call stacks attached to CUDA APIs.
- ``CUDNN_EVENTS`` and ``CUBLAS_EVENTS`` record cuDNN and cuBLAS API calls.

## Graphics APIs

- ``OPENGL_API`` and ``OPENGL_WORKLOAD`` record OpenGL CPU calls and GPU work.
- ``KHR_DEBUG_EVENTS`` records OpenGL and Vulkan ``KHR_debug`` ranges and markers.
- ``DX12_API`` and ``DX12_WORKLOAD`` record DX12 CPU calls and GPU work, matched per command list.
- ``DX12_MEMORY_OPERATION`` records DX12 resource create, destroy, map, unmap, and related operations.
- ``DXGI_API`` records DXGI calls (``Present``, swapchain, factory).
- ``D3D11_PIX_DEBUG_API`` and ``D3D12_PIX_DEBUG_API`` record PIX ``BeginEvent``, ``EndEvent``, and ``SetMarker`` calls.
- ``VULKAN_API`` and ``VULKAN_WORKLOAD`` record Vulkan CPU calls and GPU work.
- ``VULKAN_DEBUG_API`` records Vulkan debug labels (``VK_EXT_debug_utils``, etc.).
- ``VULKAN_PIPELINE_CREATION_EVENTS`` and ``_STAGE_EVENTS`` record pipeline creation timing.
- ``VULKAN_MEMORY_OPERATION`` and ``VULKAN_MEMORY_TYPES`` record Vulkan allocations and heap / property metadata.
- ``NVAPI_API`` and ``NVAPI_MEMORY_OPERATION`` record NVAPI calls and memory operations.

## Windows GPU / WDDM

- ``WDDM_QUEUE_PACKET_START_EVENTS``, ``_STOP_EVENTS``, and ``_INFO_EVENTS`` record kernel command queue packets.
- ``WDDM_DMA_PACKET_START_EVENTS``, ``_STOP_EVENTS``, and ``_INFO_EVENTS`` record DMA packets to and from the engine.
- ``WDDM_PAGING_QUEUE_PACKET_*_EVENTS`` records paging queue activity (residency / eviction work).
- ``WDDM_HW_QUEUE_EVENTS`` records hardware-scheduling queues.
- ``WDDM_EVICT_ALLOCATION_EVENTS`` records allocations evicted from VRAM.
- ``MEMORY_TRANSFER_EVENTS`` records raw ETW memory transfers (VRAM↔SYSMEM, DMA size / offset / type).
- ``GPU_CONTEXT_SWITCH_EVENTS`` records GPU context switches.
- ``GPU_VIDEO_ENGINE_WORKLOAD`` and ``_MISSING`` record video engine (NVENC / NVDEC) work.
- ``NV_LOAD_BALANCE_MASTER_EVENTS`` and ``NV_LOAD_BALANCE_EVENTS`` record NV driver frame pacing, queued-frame stats, and the "GPU one frame ahead" signal.
- ``GPU_MEMORY_BUDGET_EVENTS``, ``GPU_MEMORY_USAGE_EVENTS``, and ``DEMOTED_BYTES_EVENTS`` are deprecated but may still appear in older exports.

## ETW / generic events

- ``ETW_PROVIDERS``, ``ETW_TASKS``, and ``ETW_EVENTS`` store raw ETW stream metadata and events.
- ``GENERIC_EVENTS``, ``GENERIC_EVENT_DATA``, ``GENERIC_EVENT_SOURCES``, ``GENERIC_EVENT_TYPES``, ``GENERIC_EVENT_TYPE_FIELDS``, and ``GENERIC_EVENT_TYPE_FIELD_MAP`` define typed user / plugin events with schemas.

## GPU metrics

- ``GPU_METRICS`` holds periodic GPU counter samples (SM Active, SM Issue, Tensor Active, DRAM, etc., depending on chip).
- ``TARGET_INFO_GPU_METRICS`` defines the available metric definitions.
- ``SOC_METRICS`` and ``TARGET_INFO_SOC_METRICS`` record SoC counters on Tegra.

## OS runtime

- ``OSRT_API`` records libc and Win32 OS calls and is often the source of CPU blocking.
- ``OSRT_ARGUMENTS`` stores captured argument values.
- ``OSRT_FILE_ACCESS_EVENTS`` and ``_DESCRIPTORS`` record file access traces.

## MPI / NCCL / UCX / Network

- ``MPI_P2P_EVENTS``, ``MPI_COLLECTIVES_EVENTS``, ``MPI_START_WAIT_EVENTS``, ``MPI_OTHER_EVENTS``, ``MPI_RANKS``, and ``MPI_COMMUNICATORS`` record MPI communication events and metadata.
- ``UCP_*`` tables record UCX events.
- ``NET_NIC_METRIC``, ``NET_IB_SWITCH_METRIC``, ``NET_IB_SWITCH_CONGESTION_EVENT``, and related ``TARGET_INFO_NIC_INFO`` / ``NET_IB_DEVICE_*`` tables record network and InfiniBand metrics.

**See also:**

- [Export](export.md)
- [SQLite export](sqlite-export.md)
- [Parquet export](parquet-export.md)
- [Report file](report-file.md)
