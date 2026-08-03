---
source_path: AnalysisGuide/topics/sqlite-schema-event-values.rst
title: ## SQLite Schema Event Values
---
## SQLite Schema Event Values

Here are the set values stored in enums in the Nsight Systems SQLite schema

**CUDA Memcopy Kind**

::

   0 - CUDA_MEMCPY_KIND_UNKNOWN
   1 - CUDA_MEMCPY_KIND_HTOD
   2 - CUDA_MEMCPY_KIND_DTOH
   3 - CUDA_MEMCPY_KIND_HTOA
   4 - CUDA_MEMCPY_KIND_ATOH
   5 - CUDA_MEMCPY_KIND_ATOA
   6 - CUDA_MEMCPY_KIND_ATOD
   7 - CUDA_MEMCPY_KIND_DTOA
   8 - CUDA_MEMCPY_KIND_DTOD
   9 - CUDA_MEMCPY_KIND_HTOH
   10 - CUDA_MEMCPY_KIND_PTOP
   11 - CUDA_MEMCPY_KIND_UVM_HTOD
   12 - CUDA_MEMCPY_KIND_UVM_DTOH
   13 - CUDA_MEMCPY_KIND_UVM_DTOD


**CUDA Memory Operations Memory Kind**

::

   0 - CUDA_MEMOPR_MEMORY_KIND_PAGEABLE
   1 - CUDA_MEMOPR_MEMORY_KIND_PINNED
   2 - CUDA_MEMOPR_MEMORY_KIND_DEVICE
   3 - CUDA_MEMOPR_MEMORY_KIND_ARRAY
   4 - CUDA_MEMOPR_MEMORY_KIND_MANAGED
   5 - CUDA_MEMOPR_MEMORY_KIND_DEVICE_STATIC
   6 - CUDA_MEMOPR_MEMORY_KIND_MANAGED_STATIC
   7 - CUDA_MEMOPR_MEMORY_KIND_UNKNOWN


**CUDA Event Class Values**

::

   0 - TRACE_PROCESS_EVENT_CUDA_RUNTIME
   1 - TRACE_PROCESS_EVENT_CUDA_DRIVER
   13 - TRACE_PROCESS_EVENT_CUDA_EGL_DRIVER
   28 - TRACE_PROCESS_EVENT_CUDNN
   29 - TRACE_PROCESS_EVENT_CUBLAS
   33 - TRACE_PROCESS_EVENT_CUDNN_START
   34 - TRACE_PROCESS_EVENT_CUDNN_FINISH
   35 - TRACE_PROCESS_EVENT_CUBLAS_START
   36 - TRACE_PROCESS_EVENT_CUBLAS_FINISH
   67 - TRACE_PROCESS_EVENT_CUDABACKTRACE
   77 - TRACE_PROCESS_EVENT_CUDA_GRAPH_NODE_CREATION


See CUPTI documentation  for
detailed information on collected event and data types.

**NVTX Event Type Values**

::

   33 - NvtxCategory
   34 - NvtxMark
   39 - NvtxThread
   59 - NvtxPushPopRange
   60 - NvtxStartEndRange
   75 - NvtxDomainCreate
   76 - NvtxDomainDestroy


The difference between text and textId columns is that if an NVTX event message
was passed via call to nvtxDomainRegisterString function, then the message will
be available through textId field, otherwise the text field will contain the
message if it was provided.

**OpenGL Events**

KHR event class values

::

   62 - KhrDebugPushPopRange
   63 - KhrDebugGpuPushPopRange
       

KHR source kind values

::

   0x8249 - GL_DEBUG_SOURCE_THIRD_PARTY
   0x824A - GL_DEBUG_SOURCE_APPLICATION
       

KHR type values

::

   0x824C - GL_DEBUG_TYPE_ERROR
   0x824D - GL_DEBUG_TYPE_DEPRECATED_BEHAVIOR
   0x824E - GL_DEBUG_TYPE_UNDEFINED_BEHAVIOR
   0x824F - GL_DEBUG_TYPE_PORTABILITY
   0x8250 - GL_DEBUG_TYPE_PERFORMANCE
   0x8251 - GL_DEBUG_TYPE_OTHER
   0x8268 - GL_DEBUG_TYPE_MARKER
   0x8269 - GL_DEBUG_TYPE_PUSH_GROUP
   0x826A - GL_DEBUG_TYPE_POP_GROUP
      

KHR severity values

::

   0x826B - GL_DEBUG_SEVERITY_NOTIFICATION
   0x9146 - GL_DEBUG_SEVERITY_HIGH
   0x9147 - GL_DEBUG_SEVERITY_MEDIUM
   0x9148 - GL_DEBUG_SEVERITY_LOW
      

**OSRT Event Class Values**

OS runtime libraries can be traced to gather information about low-level
userspace APIs. This traces the system call wrappers and thread synchronization
interfaces exposed by the C runtime and POSIX Threads (pthread) libraries. This
does not perform a complete runtime library API trace, but instead focuses on
the functions that can take a long time to execute, or could potentially cause
your thread be unscheduled from the CPU while waiting for an event to complete.

OSRT events may have callchains attached to them, depending on selected
profiling settings. In such cases, one can use callchainId column to select
relevant callchains from OSRT_CALLCHAINS table

OSRT event class values

::

   27 - TRACE_PROCESS_EVENT_OS_RUNTIME
   31 - TRACE_PROCESS_EVENT_OS_RUNTIME_START
   32 - TRACE_PROCESS_EVENT_OS_RUNTIME_FINISH
      

**DX12 Event Class Values**

::

   41 - TRACE_PROCESS_EVENT_DX12_API
   42 - TRACE_PROCESS_EVENT_DX12_WORKLOAD
   43 - TRACE_PROCESS_EVENT_DX12_START
   44 - TRACE_PROCESS_EVENT_DX12_FINISH
   52 - TRACE_PROCESS_EVENT_DX12_DISPLAY
   59 - TRACE_PROCESS_EVENT_DX12_CREATE_OBJECT
      

**PIX Event Class Values**

::

   65 - TRACE_PROCESS_EVENT_DX12_DEBUG_API
   75 - TRACE_PROCESS_EVENT_DX11_DEBUG_API
      

**Vulkan Event Class Values**

::

   53 - TRACE_PROCESS_EVENT_VULKAN_API
   54 - TRACE_PROCESS_EVENT_VULKAN_WORKLOAD
   55 - TRACE_PROCESS_EVENT_VULKAN_START
   56 - TRACE_PROCESS_EVENT_VULKAN_FINISH
   60 - TRACE_PROCESS_EVENT_VULKAN_CREATE_OBJECT
   66 - TRACE_PROCESS_EVENT_VULKAN_DEBUG_API
      

**Vulkan Flags**

::

   VALID_BIT = 0x00000001
   CACHE_HIT_BIT = 0x00000002
   BASE_PIPELINE_ACCELERATION_BIT = 0x00000004
      

**WDDM Event Values**

VIDMM operation type values

::

   0 - None
   101 - RestoreSegments
   102 - PurgeSegments
   103 - CleanupPrimary
   104 - AllocatePagingBufferResources
   105 - FreePagingBufferResources
   106 - ReportVidMmState
   107 - RunApertureCoherencyTest
   108 - RunUnmapToDummyPageTest
   109 - DeferredCommand
   110 - SuspendMemorySegmentAccess
   111 - ResumeMemorySegmentAccess
   112 - EvictAndFlush
   113 - CommitVirtualAddressRange
   114 - UncommitVirtualAddressRange
   115 - DestroyVirtualAddressAllocator
   116 - PageInDevice
   117 - MapContextAllocation
   118 - InitPagingProcessVaSpace
   200 - CloseAllocation
   202 - ComplexLock
   203 - PinAllocation
   204 - FlushPendingGpuAccess
   205 - UnpinAllocation
   206 - MakeResident
   207 - Evict
   208 - LockInAperture
   209 - InitContextAllocation
   210 - ReclaimAllocation
   211 - DiscardAllocation
   212 - SetAllocationPriority
   1000 - EvictSystemMemoryOfferList
      

Paging queue type values

::

   0 - VIDMM_PAGING_QUEUE_TYPE_UMD
   1 - VIDMM_PAGING_QUEUE_TYPE_Default
   2 - VIDMM_PAGING_QUEUE_TYPE_Evict
   3 - VIDMM_PAGING_QUEUE_TYPE_Reclaim
      

Packet type values

::

   0 - DXGKETW_RENDER_COMMAND_BUFFER
   1 - DXGKETW_DEFERRED_COMMAND_BUFFER
   2 - DXGKETW_SYSTEM_COMMAND_BUFFER
   3 - DXGKETW_MMIOFLIP_COMMAND_BUFFER
   4 - DXGKETW_WAIT_COMMAND_BUFFER
   5 - DXGKETW_SIGNAL_COMMAND_BUFFER
   6 - DXGKETW_DEVICE_COMMAND_BUFFER
   7 - DXGKETW_SOFTWARE_COMMAND_BUFFER
      

Engine type values

::

   0 - DXGK_ENGINE_TYPE_OTHER
   1 - DXGK_ENGINE_TYPE_3D
   2 - DXGK_ENGINE_TYPE_VIDEO_DECODE
   3 - DXGK_ENGINE_TYPE_VIDEO_ENCODE
   4 - DXGK_ENGINE_TYPE_VIDEO_PROCESSING
   5 - DXGK_ENGINE_TYPE_SCENE_ASSEMBLY
   6 - DXGK_ENGINE_TYPE_COPY
   7 - DXGK_ENGINE_TYPE_OVERLAY
   8 - DXGK_ENGINE_TYPE_CRYPTO
      

DMA interrupt type values

::

   1 = DXGK_INTERRUPT_DMA_COMPLETED
   2 = DXGK_INTERRUPT_DMA_PREEMPTED
   4 = DXGK_INTERRUPT_DMA_FAULTED
   9 = DXGK_INTERRUPT_DMA_PAGE_FAULTED
      

Queue type values

::

   0 = Queue_Packet
   1 = Dma_Packet
   2 = Paging_Queue_Packet
      

**Driver Events**

Load balance event type values

::

   1 - LoadBalanceEvent_GPU
   8 - LoadBalanceEvent_CPU
   21 - LoadBalanceMasterEvent_GPU
   22 - LoadBalanceMasterEvent_CPU
      

**OpenMP Events**

OpenMP event class values

::

   78 - TRACE_PROCESS_EVENT_OPENMP
   79 - TRACE_PROCESS_EVENT_OPENMP_START
   80 - TRACE_PROCESS_EVENT_OPENMP_FINISH
      

OpenMP event kind values

::

   15 - OPENMP_EVENT_KIND_TASK_CREATE
   16 - OPENMP_EVENT_KIND_TASK_SCHEDULE
   17 - OPENMP_EVENT_KIND_CANCEL
   20 - OPENMP_EVENT_KIND_MUTEX_RELEASED
   21 - OPENMP_EVENT_KIND_LOCK_INIT
   22 - OPENMP_EVENT_KIND_LOCK_DESTROY
   25 - OPENMP_EVENT_KIND_DISPATCH
   26 - OPENMP_EVENT_KIND_FLUSH
   27 - OPENMP_EVENT_KIND_THREAD
   28 - OPENMP_EVENT_KIND_PARALLEL
   29 - OPENMP_EVENT_KIND_SYNC_REGION_WAIT
   30 - OPENMP_EVENT_KIND_SYNC_REGION
   31 - OPENMP_EVENT_KIND_TASK
   32 - OPENMP_EVENT_KIND_MASTER
   33 - OPENMP_EVENT_KIND_REDUCTION
   34 - OPENMP_EVENT_KIND_MUTEX_WAIT
   35 - OPENMP_EVENT_KIND_CRITICAL_SECTION
   36 - OPENMP_EVENT_KIND_WORKSHARE
      

OpenMP thread type values

::

   1 - OpenMP Initial Thread
   2 - OpenMP Worker Thread
   3 - OpenMP Internal Thread
   4 - Unknown
      

OpenMP sync region kind values

::

   1 - Barrier
   2 - Implicit barrier
   3 - Explicit barrier
   4 - Implementation-dependent barrier
   5 - Taskwait
   6 - Taskgroup
       

OpenMP task kind values

::

   1 - Initial task
   2 - Implicit task
   3 - Explicit task
       

OpenMP prior task status values

::

   1 - Task completed
   2 - Task yielded to another task
   3 - Task was cancelled
   7 - Task was switched out for other reasons
       

OpenMP mutex kind values

::

   1 - Waiting for lock
   2 - Testing lock
   3 - Waiting for nested lock
   4 - Tesing nested lock
   5 - Waitng for entering critical section region
   6 - Waiting for entering atomic region
   7 - Waiting for entering ordered region
       

OpenMP critical section kind values

::

   5 - Critical section region
   6 - Atomic region
   7 - Ordered region
       

OpenMP workshare kind values

::

   1 - Loop region
   2 - Sections region
   3 - Single region (executor)
   4 - Single region (waiting)
   5 - Workshare region
   6 - Distrubute region
   7 - Taskloop region
       

OpenMP dispatch kind values

::

   1 - Iteration
   2 - Section
