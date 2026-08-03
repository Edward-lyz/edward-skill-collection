---
source_path: UserGuide/topics/d3d12-api-trace.rst
title: ## D3D12 API Trace
---
## D3D12 API Trace

Direct3D 12 is a low-overhead 3D graphics and compute API for Microsoft Windows. Information about Direct3D 12 can be found at the Direct3D 12 Programming Guide .

Nsight Systems can capture information about Direct3D 12 usage by the profiled process. This includes capturing the execution time of D3D12 API functions, corresponding workloads executed on the GPU, performance markers, and frame durations.

   :alt: D3D12 overview picture
   :class: image

The Command List Creation row displays time periods when command lists were being created. This enables developers to improve their application’s multi-threaded command list creation. Command list creation time period is measured between the call to ``ID3D12GraphicsCommandList::Reset`` and the call to ``ID3D12GraphicsCommandList::Close``.

   :alt: D3D12 commandlist creation
   :class: image

The GPU row shows a compressed view of the D3D12 queue activity, color-coded by the queue type. Expanding it will show the individual queues and their corresponding API calls.

   :alt: D3D12 GPU aggregated
   :class: image

A Command Queue row is displayed for each D3D12 command queue created by the profiled application. The row’s header displays the queue's running index and its type (Direct, Compute, Copy).

   :alt: D3D12 command queue overview
   :class: image

The DX12 API Memory Ops row displays all API memory operations and non-persistent resource mappings. Event ranges in the row are color-coded by the heap type they belong to (Default, Readback, Upload, Custom, or CPU-Visible VRAM), with usage warnings highlighted in yellow. A breakdown of the operations can be found by expanding the row to show rows for each individual heap type.

The following operations and warnings are shown:

-  Calls to ``ID3D12Device::CreateCommittedResource``, ``ID3D12Device4::CreateCommittedResource1``, and ``ID3D12Device8::CreateCommittedResource2``

   -  A warning will be reported if ``D3D12_HEAP_FLAG_CREATE_NOT_ZEROED`` is not set in the method's ``HeapFlags`` parameter.

-  Calls to ``ID3D12Device::CreateHeap`` and ``ID3D12Device4::CreateHeap1``

   -  A warning will be reported if ``D3D12_HEAP_FLAG_CREATE_NOT_ZEROED`` is not set in the ``Flags`` field of the method's ``pDesc`` parameter

-  Calls to ``ID3D12Resource::ReadFromSubResource``

   -  A warning will be reported if the read is to a ``D3D12_CPU_PAGE_PROPERTY_WRITE_COMBINE`` CPU page or from a ``D3D12_HEAP_TYPE_UPLOAD`` resource.

-  Calls to ``ID3D12Resource::WriteToSubResource``

   -  A warning will be reported if the write is from a ``D3D12_CPU_PAGE_PROPERTY_WRITE_BACK`` CPU page or to a ``D3D12_HEAP_TYPE_READBACK`` resource.

-  Calls to ``ID3D12Resource::Map`` and ``ID3D12Resource::Unmap`` will be matched into [Map, Unmap] ranges for non-persistent mappings. If a mapping range is nested, only the most external range (reference count = 1) will be shown.

   :alt: D3D12 memory operations and usage warning
   :class: image

The API row displays time periods where ``ID3D12CommandQueue::ExecuteCommandLists`` was called. The GPU Workload row displays time periods where workloads were executed by the GPU. The workload’s type (Graphics, Compute, Copy, etc.) is displayed on the bar representing the workload’s GPU execution.

   :alt: D3D12 API and Workload
   :class: image

In addition, you can see the PIX command queue CPU-side performance markers, GPU-side performance markers, and the GPU Command List performance markers, each in their row.

   :alt: D3D12 CPU marker
   :class: image

   :alt: D3D12 GPU marker
   :class: image

   :alt: D3D12 commandlist marker
   :class: image

Clicking on a GPU workload highlights the corresponding ``ID3D12CommandQueue::ExecuteCommandLists``, ``ID3D12GraphicsCommandList::Reset`` and ``ID3D12GraphicsCommandList::Close API`` calls, and vice versa.

   :alt: D3D12 correlation
   :class: image

Detecting which CPU thread was blocked by a fence can be difficult in complex apps that run tens of CPU threads. The timeline view displays the 3 operations involved:

-  The CPU thread pushing a signal command and fence value into the command queue. This is displayed on the DX12 Synchronization sub-row of the calling thread.

-  The GPU executing that command, setting the fence value and signaling the fence. This is displayed on the GPU Queue Synchronization sub-row.

-  The CPU thread calling a Win32 wait API to block-wait until the fence is signaled. This is displayed on the Thread's OS runtime libraries row.

Clicking one of these will highlight it and the corresponding other two calls.

   :alt: D3D12 fence sync
   :class: image

Nsight Systems D3D12 trace captures D3D12 Work Graphs dispatch calls to DispatchGraph and time boundaries of the GPU execution of the work graph.

   :alt: D3D12 Work Graphs API trace
   :class: image

The DX12 API row displays ``ID3D12GraphicsCommandList10::DispatchGraph`` calls. The GPU PIX Markers row marks graph execution by the GPU with a custom marker captioned "D3D12 graph execution."

   :alt: D3D12 API and Workload
   :class: image
