---
source_path: AnalysisGuide/topics/expert-system-rules.rst
title: ## Expert System Rules
---
## Expert System Rules

Rules are scripts that run on the SQLite DB output from Nsight Systems to find
common improvable usage patterns.

Each rule has an advice summary with explanation of the problem found and
suggestions to address it. Only the top 50 results are displayed by default.

There are currently six rules in the expert system. They are described below.
Additional rules will be made available in a future version of Nsight Systems.


### CUDA Synchronous Operation Rules

**Asynchronous memcpy with pageable memory**

This rule identifies asynchronous memory transfers that end up becoming
synchronous if the memory is pageable. This rule is not applicable for Nsight
Systems Embedded Platforms Edition

Suggestion: If applicable, use pinned memory instead


      :alt: CUDA Graph trace at the node level
      :class: image


**Synchronous Memcpy**

This rule identifies synchronous memory transfers that block the host.

Suggestion: Use cudaMemcpy*Async APIs instead.

**Synchronous Memset**

This rule identifies synchronous memset operations that block the host.

Suggestion: Use cudaMemset*Async APIs instead.

**Synchronization APIs**

This rule identifies synchronization APIs that block the host until all issued
CUDA calls are complete.

Suggestions: Avoid excessive use of synchronization. Use asynchronous CUDA event
calls, such as cudaStreamWaitEvent and cudaEventSynchronize, to prevent host
synchronization.


### GPU Low Utilization Rules

Nsight Systems determines GPU utilization based on API trace data in the
collection. Current rules consider CUDA, Vulkan, DX12, and OpenGL API use of the
GPU.

**GPU Starvation**

This rule identifies time ranges where a GPU is idle for longer than 500ms. The
threshold is adjustable.

Suggestions: Use CPU sampling data, OS Runtime blocked state backtraces, and/or
OS Runtime APIs related to thread synchronization to understand if a sluggish or
blocked CPU is causing the gaps. Add NVTX annotations to CPU code to understand
the reason behind the gaps.

Notes: For each process, each GPU is examined, and gaps are found within the
time range that starts with the beginning of the first GPU operation on that
device and ends with the end of the last GPU operation on that device. GPU gaps
that cannot be addressed by the user are excluded. This includes:

-  Profiling overhead in the middle of a GPU gap.
-  The initial gap in the report that is seen before the first GPU operation.
-  The final gap that is seen after the last GPU operation.


**GPU Low Utilization**

This rule identifies time regions with low utilization.

Suggestions: Use CPU sampling data, OS Runtime blocked state backtraces, and/or
OS Runtime APIs related to thread synchronization to understand if a sluggish or
blocked CPU is causing the gaps. Add NVTX annotations to CPU code to understand
the reason behind the gaps.

Notes: For each process, each GPU is examined, and gaps are found within the
time range that starts with the beginning of the first GPU operation on that
device and ends with the end of the last GPU operation on that device. This time
range is then divided into equal chunks, and the GPU utilization is calculated
for each chunk. The utilization includes all GPU operations as well as profiling
overheads that the user cannot address.

The utilization refers to the "time" utilization and not the "resource"
utilization. This rule attempts to find time gaps when the GPU is or isn't being
used, but does not take into account how many GPU resources are being used.
Therefore, a single running memcpy is considered the same amount of "utilization"
as a huge kernel that takes over all the cores. If multiple operations run
concurrently in the same chunk, their utilization will be added up and may
exceed 100%.

Chunks with an in-use percentage less than the threshold value are displayed. If
consecutive chunks have a low in-use percentage, the individual chunks are
coalesced into a single display record, keeping the weighted average of
percentages. This is why returned chunks may have different durations.
