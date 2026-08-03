---
source_path: UserGuide/topics/nccl-trace.rst
title: ## NVIDIA NCCL Trace
---
## NVIDIA NCCL Trace

Nsight Systems provides two methods for tracing NVIDIA NCCL (NVIDIA Collective Communications Library) operations:

1. **Legacy NCCL tracing:** is based on NVTX annotations within the NCCL library itself.
   
   - Enabled by default when NVTX tracing is active
   - Traces API calls on the CPU
   - Provides limited GPU-projection of ranges in the GUI
   
2. **Advanced NCCL tracing:** A more detailed tracing mechanism introduced in Nsight Systems 2025.6.1.
   
   - Requires NCCL version 2.28 or higher (with limited support for versions 2.27.4 and later)
   - Support for Copy Engine (CE) collectives requires NCCL version 2.29 or higher
   - Provides detailed information about GPU operations and asynchronous runtime scheduling
   - Enhances correlation across events
   - Less precise timestamps for CPU API calls compared to legacy NCCL tracing


#### NCCL Execution Concepts

To effectively interpret NCCL traces, it is important to understand the following aspects of NCCL's operation.
A NCCL collective operation comprises multiple steps on the CPU and GPU:

- The application calls the NCCL API.
- The NCCL runtime prepares and schedules the operation in queues for the GPU.
- The CUDA kernel is launched.
- The operation executes within a CUDA kernel.

The order of these steps and the threads in which they occur depend on the application pattern:

- Use of groups
- Blocking vs. non-blocking communicators
- CUDA graph capture

**Group Operations**

When using NCCL groups, all operations within the group are executed at the end of the group:

- Operations in a group are typically fused into a single CUDA kernel per rank/device.
- With legacy NCCL tracing, the ``ncclGroupEnd`` function is projected to the fused CUDA kernel on the GPU.
- When no explicit groups are used, there is an implicit group as part of each API call. This implicit grouping is not shown in legacy NCCL tracing.

**Non-blocking Communicators**

For non-blocking communicators, CUDA calls are performed in different threads:

- Legacy NCCL tracing cannot track these cross-thread operations.
- Plugin-based tracing properly correlates all events (e.g., API calls, CUDA calls, and GPU operations) that belong to one logical operation.

**Graph Capture**

With graph capture, the API calls and kernel launch are captured once, but the runtime scheduling and GPU operations happen multiple times, once per graph launch.


#### Advanced NCCL Tracing

The advanced NCCL tracing mechanism provides comprehensive visibility into NCCL operations across the CPU and GPU.
The actual trace structure depends heavily on the specific application patterns.

Internally, the advanced NCCL tracing is built as a profiler plugin of NCCL (not to be confused with an nsys plugin).

### Trace Information

The advanced NCCL tracing provides the following information in reports:

**API Calls**

NCCL API calls (collective, point-to-point, and group operations) on the CPU are traced with the following characteristics:

- Groups are shown as an ``API Group`` range that spans all API calls within the group. Technically, this range does not include ``ncclGroupStart``, but extends through the end of ``ncclGroupEnd``/``GroupLaunch``.
- Individual API calls are shown below the ``API Group`` range.
- The ``nccl`` prefix is omitted from function names (e.g., ``ncclAllReduce`` appears as ``AllReduce``).
- The ``GroupLaunch`` range corresponds to the ``ncclGroupEnd`` function call on the application thread invoking the NCCL group functions.
  
  - For blocking communication, this range encompasses the preparation for kernel launches. There can be multiple launches per group, usually one per rank/device, and the actual CUDA kernel launches are collected as ``KernelLaunch`` ranges.

**Runtime Scheduling**

Runtime scheduling events show where NCCL runs on the CPU and queues operations for the GPU:

- ``GroupRuntime`` ranges encompass the individual runtime scheduling for collective and point-to-point operations.
- Runtime scheduling can occur in different contexts:
  
  - Directly at the end of the ``API Group`` for blocking communicators
  - In a separate thread for non-blocking communicators
  - For graph launches, there are multiple runtime groups for a single API group, one per launch, and the group events occur in a host function on a special thread

**GPU Operations**

GPU operations are displayed with the following details:

- Individual operations within fused CUDA kernels are shown with accurate GPU timestamps.
- Operations are further split across multiple channels that execute concurrently.
- GPU operations are shown directly under the GPU in the timeline view.

**Copy Engine (CE) Collectives**

CE-based collectives are not shown as GPU operations in the NCCL device row.
They use CUDA memory operations rather than CUDA kernels.
By default, for each API call to a CE collective, a corresponding range will be shown within the ``GroupLaunch`` range.
In addition, you can configure Nsight Systems to add two ``CE Sync`` ranges and one ``CE Batch`` range below each CE collective range (see nccl-trace-options).

**Proxy Activity**

NCCL uses a proxy thread to support CPU-orchestrated inter-node communication.
Some activity in this proxy thread can be collected and shown in the timeline view.
Proxy activity recording is experimental, may change in future releases, and is not enabled by default.
This view is intended for expert-level analysis and can be difficult to interpret.
Use it for deep dives into network bottlenecks and supplement it with general network counters.
In the Nsight Systems GUI, proxy step visualization can be dense due to the volume of detail and is best suited
to analysis of exported files.

Proxy operation ranges encapsulate the proxy activity for one peer, channel and direction.
Each proxy operation is split into proxy steps to process individual chunks in a pipelined manner.
Within each proxy step, state changes are recorded.
Due to the amount of data collected for proxy steps, the data collection can have a significant performance impact.

Proxy counters summarize the proxy activity within one communicator.
They display the number of proxy steps in any given state, separated into ``ProxyStepSend`` and ``ProxyStepRecv``.

All NCCL proxy activity is performed by a dedicated CPU thread for each rank/communicator.
This thread is named ``NCCL Progress [$rank/$nRanks]: $commHash`` to easily identify the context.
Nsight Systems shows both the proxy operations and proxy counters as part of this thread.

**Communicators**

All NCCL events are organized in categories: one for each communicator.
In the GUI, NCCL rows initially show events from all communicators but can be expanded to display events grouped by communicator.
For complex applications, developers should assign names to communicators within the application by setting ``commName`` in ``ncclConfig_t``.
Creation of communicators is indicated by a ``CommInit`` marker in a dedicated initialization thread.

**Metadata**

All NCCL events carry metadata (payload information):

- Information about the communicator,
- Operation-related events carry metadata about the specific operation, e.g., data type, element count, etc.,
- Correlation identifiers.

**Event Correlation**

Events corresponding to individual operations are correlated by the ``apiId``, which for collective operations includes the operations of all participating ranks.
The correlation links the API call, collective runtime scheduling, and GPU operation, helping to track operations through the UI.
Additional correlation identifiers are available but not currently used to avoid highlighting too many ranges simultaneously:

- ``apiGroupId``: All API calls and corresponding kernel launches in a specific (thread-local) group
- ``group``: Group identifier

**CUDA Graph Capture**

The advanced NCCL tracing can track individual operations through CUDA graph capture and graph launches, from the API call through runtime scheduling in host functions to the GPU operation.

**Memory Overhead**

To collect a consistent and correlated trace, the NCCL injection allocates data for each event using a growing pre-allocated buffer. The buffer is freed when the communicator is finalized.

**Capture Ranges**

Capture ranges affect data collection. Outside of capture ranges, no data is collected and the overhead is significantly reduced. In particular, the NCCL injection does not allocate data for each event outside capture ranges.
If correlating NCCL events are only partially inside a capture range, the correlation may be lost.
For example, if the API calls occur before a capture range and only the operations are inside, the operations will be included but without correlation identifiers.

### Report View

The timeline view of a report with advanced NCCL tracing includes several types of ``NCCL`` rows:

- A ``NCCL`` row directly under each device shows the GPU operations.
- CPU threads that call API functions include a ``NCCL`` row showing the respective API events.
- Internal threads that execute non-blocking or graph host functions also include a ``NCCL`` row showing runtime events (not shown in the example).
- An additional global ``NCCL`` row at the bottom combines the CPU-side NCCL events from all processes/threads in the report.
- Below the stream rows on the device, ``NCCL`` rows show projections of the respective internal NCCL ranges which were responsible for launching the corresponding CUDA activity.

Each ``NCCL`` row can be expanded to show individual events for each communicator.

The screenshot shows two participating devices with a simple API group that includes two API calls (one for each rank).
Since this is a blocking communicator, the group directly executes the NCCL internal functions ``GroupLaunch`` and ``GroupRuntime``.
A tooltip shows the metadata of a NCCL operation.

   :alt: Example report of NCCL tracing
   :class: image

### Exporting

The data from advanced NCCL tracing can be exported as SQLite database for further processing.
See sqlite-schema for more details.

NCCL events are available as NVTX ranges in the exported database.
While legacy NCCL tracing also uses NVTX, the exported events differ.
Add ``--include-json true`` to include the metadata as JSON in the exported tables.
The specific schema of the exported tables may be subject to change in the future.

### Limitations

The advanced NCCL tracing has the following limitations (as of NCCL v2.28):

- Communicator creation API functions are not collected directly. However, the creation is indicated in the initialization thread via ``CommInit`` markers.
- Single-rank communications, which are usually only buffer copies, are not shown at all. Their events are not captured.
- Symmetric memory based collectives (new low latency implementations of AllReduce, AllGather and ReduceScatter) are not fully supported. Only the API calls are collected.
- AllToAll, Gather, Scatter operations will be shown as their underlying grouped point-to-point operations rather than the high-level API call.

### Usage

To use advanced NCCL tracing:

1. Enable NCCL tracing using the ``-t nccl`` option with ``nsys profile`` or enable the "NCCL" section in the Network profiling options of the GUI:


      nsys profile -t nccl <application>

Note:
      By default, only the legacy NCCL tracing (API calls) is active.

2. Normally, both NCCL and CUDA tracing are enabled.


      nsys profile -t nccl,cuda <application>

3. When advanced NCCL tracing is enabled, the legacy NCCL tracing is automatically disabled.


### Configuration Options

Configure advanced NCCL tracing using the ``--nccl-trace`` option with ``nsys profile``. The following values are available and can be combined using commas (e.g., ``--nccl-trace=api,rt``):

- ``api-group``: The ``API Group`` range
- ``api-coll``: Collective API calls (e.g., ``AllReduce``)
- ``api-p2p``: Point-to-point API calls (``Send`` and ``Recv``)
- ``api``: All of the three API ranges above (``api-group``, ``api-coll``, ``api-p2p``)
- ``group``: ``GroupRuntime`` ranges for operation scheduling on the CPU
- ``coll``: Runtime scheduling of individual collective operations
- ``p2p``: Runtime scheduling of individual point-to-point operations
- ``kernel-launch``: Ranges around CUDA kernel launches
- ``ce-coll``: Launch of memory operations for Copy Engine (CE) -based collectives
- ``ce-sync``: Synchronization of CE collectives (within ce-coll)
- ``ce-batch``: Batch operations of CE collectives (within ce-coll)
- ``rt``: All runtime ranges (``group``, ``coll``, ``p2p``, ``kernel-launch``)
- ``gpu``: Individual operations on the GPU
- ``proxy-op``: Proxy operation ranges (experimental)
- ``proxy-step``: Proxy step ranges including state changes (experimental, high overhead)
- ``proxy-counters``: Proxy counters (experimental)
- ``default``: The default set of events (``api``, ``group``, ``gpu``, ``ce-coll``)
- ``all``: All possible events (except ``proxy-op``, ``proxy-step``)

The interaction between ``--nccl-trace`` and ``--trace`` works as follows:

- If ``--nccl-trace`` is explicitly set, it takes priority over any NCCL-related settings from ``--trace``. Any value other than ``none`` implicitly includes ``nccl`` in ``--trace``.
- If ``--nccl-trace`` is not set, the default behavior depends on ``--trace``: if ``nccl`` is included in ``--trace``, ``default`` is used for ``--nccl-trace``; otherwise, ``none`` is used.

### More Examples

Enable advanced NCCL tracing with all events as well as CUDA tracing:


   nsys profile -t nccl,cuda --nccl-trace=all <application>

Disable advanced NCCL tracing to fall back to legacy NCCL tracing:


   nsys profile -t cuda,nvtx <application>

Disable the NCCL NVTX domain, neither advanced NCCL tracing nor legacy NCCL tracing will be enabled:


   nsys profile -t cuda,nvtx --nvtx-domain-exclude=NCCL <application>

Disable NVTX tracing completely, neither advanced NCCL tracing nor legacy NCCL tracing will be enabled:


   nsys profile -t cuda <application>
