---
source_path: AnalysisGuide/topics/recipe-composite-tables.rst
title: ## Recipe Composite Tables
---
## Recipe Composite Tables

When writing a recipe, you use ``CompositeTable`` enum values to request
pre-processed DataFrames. These composite tables join, rename, and resolve
raw parquet export tables into analysis-ready DataFrames, so you don't
have to do the merging and ID-to-string resolution yourself.

### Available Composite Tables

   :header-rows: 1
   :widths: 25 75

   * - CompositeTable
     - Description
   * - ``CUDA_GPU``
     - All GPU activities (kernels, memcpy, memset, mem_decompress) concatenated
       into one table. Columns are the union of the raw CUPTI activity columns.
       Use this when you want a broad view of everything the GPU did.
   * - ``CUDA_GPU_GRAPH``
     - Same as ``CUDA_GPU`` but includes ``graphNodeId`` and ``graphId`` columns
       for correlating activities to CUDA graph nodes. Use this when analyzing
       CUDA graph execution.
   * - ``CUDA_COMBINED``
     - GPU activities + CPU runtime API calls, correlated by ``correlationId``.
       GPU timing is renamed to ``gpu_start``/``gpu_end`` to avoid conflicts
       with the runtime ``start``/``end``. The runtime ``nameId`` is resolved
       to a human-readable ``name`` column (e.g., ``"cudaLaunchKernel"``).
       Use this when you need to analyze the full CPU-to-GPU execution pipeline.
   * - ``CUDA_COMBINED_KERNEL``
     - Runtime + kernels only (no memcpy/memset). Like ``CUDA_COMBINED`` but
       limited to kernel launches, and kernel name columns (``shortName``,
       ``mangledName``, ``demangledName``) are resolved from string IDs to
       actual names. GPU timing renamed to ``gpu_start``/``gpu_end``.
   * - ``CUDA_KERNEL``
     - Kernels only with ``shortName``, ``mangledName``, and ``demangledName``
       resolved from integer IDs to actual string names. Use this when you
       only need kernel data without the runtime API correlation.
   * - ``NVTX``
     - NVTX ranges with ``textId`` resolved into a unified ``text`` column and
       ``domainId`` resolved into ``domainName``. The raw ``NVTX_EVENTS`` table
       stores text as integer IDs; this table has readable strings.
   * - ``NCCL``
     - NCCL communication operations parsed from NVTX events. Includes
       ``jsonText`` fields for advanced NCCL tracing data.
   * - ``NCCL_API``
     - NCCL API-level view showing call durations, parsed from NVTX events.
   * - ``NCCL_GPU_OPERATIONS``
     - NCCL GPU-level operations view parsed from NVTX events. Includes
       collective and P2P operations with common payload fields and normalized
       operation identity columns.
   * - ``NCCL_GPU_OPERATIONS_COLLECTIVE``
     - NCCL collective GPU operation view with collective-specific payload
       fields such as ``apiId`` and ``seqNumber``.
   * - ``NIC``
     - Network interface metrics joined with device info. Columns include
       ``nic_name``, ``metric_name``, ``GUID``, ``value``, and timing.
   * - ``IB_SWITCH``
     - InfiniBand switch port metrics with ``globalId`` renamed to ``GUID`` and
       metric names resolved into ``metric_name``.
   * - ``MPI``
     - All MPI event tables (P2P, collectives, start/wait, other) concatenated
       and sorted by start time. ``textId`` resolved to ``text``.
   * - ``UCX``
     - All UCX event tables (submit, progress, general) concatenated and sorted
       by start time. ``textId`` resolved to ``text``.
   * - ``GPU_METRICS``
     - GPU hardware metrics pivoted so each metric name becomes its own column
       (e.g., ``"SMs Active"``, ``"Tensor Active"``). Indexed by ``timestamp``
       and ``typeId`` (GPU device). The raw ``GPU_METRICS`` table has one row
       per metric per timestamp; this table has one row per timestamp with
       metrics as columns.
   * - ``PERF_EVENTS``
     - CPU performance counter events enriched with ``componentType``
       (Core/Cache/Socket), ``cpu`` number, and event ``name``.
   * - ``GENERIC``
     - Generic metric events with type and field IDs resolved to
       ``metricName`` and ``dataSrc`` strings. Numeric values coalesced from
       int/uint/float/double into a single ``metricValue`` column.


### Choosing the Right CUDA Table

The CUDA-related composite tables can be confusing since there are five of
them. Here is when to use each one:

   :header-rows: 1
   :widths: 25 15 15 15 30

   * - Table
     - Includes kernels
     - Includes memcpy/memset
     - Includes runtime API
     - When to use
   * - ``CUDA_GPU``
     - Yes
     - Yes
     - No
     - Overview of all GPU activity
   * - ``CUDA_GPU_GRAPH``
     - Yes
     - Yes
     - No
     - Same, but with CUDA graph correlation
   * - ``CUDA_KERNEL``
     - Yes
     - No
     - No
     - Kernel-only analysis with resolved names
   * - ``CUDA_COMBINED``
     - Yes
     - Yes
     - Yes
     - Full CPU-to-GPU pipeline analysis
   * - ``CUDA_COMBINED_KERNEL``
     - Yes
     - No
     - Yes
     - Kernel launch overhead analysis with resolved names


### Output Columns

Each composite table produces a DataFrame with specific columns. The columns
depend on which raw tables were joined and what transformations were applied.
Also note: when tables are loaded through ``DataService``, bit-field
decomposition may add derived columns such as ``pid``, ``tid``, and ``gpuId``.

**CUDA_GPU**


   correlationId   start   end   globalPid   deviceId   contextId   greenContextId   streamId   pid

**CUDA_GPU_GRAPH**


   correlationId   start   end   globalPid   deviceId   contextId   greenContextId   streamId   graphNodeId   graphId   pid

``graphNodeId`` appears on kernel/memcpy/memset rows, and ``graphId`` appears on
graph-trace rows.

**CUDA_KERNEL**


   correlationId   globalPid   start   end   deviceId   shortName   mangledName   demangledName   pid

The ``*Name`` columns contain resolved strings (not integer IDs).

**CUDA_COMBINED**


   start   end   globalTid   name   correlationId   gpu_start   gpu_end   pid   tid   deviceId   contextId   greenContextId   streamId

``start``/``end`` are the CPU-side runtime API call times. ``gpu_start``/``gpu_end``
are the GPU-side activity times. ``name`` is the resolved API function name
(e.g., ``"cudaLaunchKernel"``). ``pid`` and ``tid`` are extracted from
``globalTid`` by bit field decomposition (``globalPid`` is dropped).

**CUDA_COMBINED_KERNEL**


   start   end   globalTid   correlationId   gpu_start   gpu_end   pid   tid   deviceId   shortName   mangledName   demangledName

Like ``CUDA_COMBINED`` but kernel-only, with resolved kernel names instead of
runtime API name. ``pid`` and ``tid`` are extracted from ``globalTid``
(``globalPid`` is dropped).

**NVTX**


   text   start   end   globalTid   endGlobalTid   domainId   domainName   eventType   pid   tid

``text`` is the resolved NVTX annotation string. ``domainName`` is ``"Default"``
if no domain was specified.

**NCCL**


   text   start   end   globalTid   endGlobalTid   domainId   eventType   jsonText   pid   tid

NCCL rows are filtered from NVTX to the domain named ``"NCCL"`` and keep NVTX
timing/thread columns. ``jsonText`` is present when advanced NCCL tracing payloads exist.

**NCCL_API**


   text   start   end   globalTid   endGlobalTid   domainId   eventType   jsonText   count   dataType   rank   pid   tid

Extends ``NCCL`` with parsed API payload fields (``count``, ``dataType``,
``rank``).

**NCCL_GPU_OPERATIONS**


   localId (index)   text   start   end   commHash   commRank   count   dataType   operationClass   operationId

One row per merged GPU operation (grouped from per-channel events). Includes
both collective and P2P operations, but only common NCCL GPU operation payload
fields. ``operationClass`` identifies ``"collective"`` versus ``"p2p"``
operations, and the 64-bit numeric ``operationId`` acts as unique id to correlated
collectives across all ranks as well as sends with their corresponding receives.
The id is unique across all collective and P2P operations.
``localId`` is the DataFrame index after grouping.

**NCCL_GPU_OPERATIONS_COLLECTIVE**


   localId (index)   text   start   end   commHash   commRank   count   dataType   seqNumber   apiId

One row per collective GPU operation merged across channels, not across ranks.
This table exposes collective-specific payload fields.

**MPI / UCX**


   globalTid   start   end   text   pid   tid

All sub-tables concatenated, sorted by ``start``. ``text`` is the resolved
operation name (e.g., ``"MPI_Send"``, ``"MPI_Allreduce"``).

**NIC**


   start   end   globalId   nicId   value   metricsListId   metricsIdx   GUID   nic_name   metric_name

**IB_SWITCH**


   start   end   GUID   value   metricsListId   metricsIdx   metric_name

**GPU_METRICS**


   timestamp   typeId   gpuId   SMs Active   SM Issue   Tensor Active   Unallocated Warps in Active SMs   ...

Each metric is a column. The available columns depend on the GPU and capture
settings.

**PERF_EVENTS**


   start   end   vmId   eventId   count   componentType   cpu   name

**GENERIC**


   timestamp   typeId   genericEventId   metricName   metricValue   dataSrc   gpuId


### Examples in Existing Recipes

These recipes demonstrate how composite tables are used in practice:

- ``cuda_gpu_kern_sum``: Uses ``CUDA_KERNEL`` for kernel summary statistics
- ``nvtx_sum``: Uses ``NVTX`` for NVTX range analysis
- ``nvtx_gpu_proj_sum``: Uses ``CUDA_GPU_GRAPH`` + ``NVTX`` for GPU projection
- ``network_map_aws``: Uses ``GENERIC`` for AWS EFA metrics

See also create user-defined recipe for a step-by-step tutorial on
creating your own recipe.
