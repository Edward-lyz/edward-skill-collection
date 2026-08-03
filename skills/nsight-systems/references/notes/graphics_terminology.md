# Graphics and System Terminology




Terminology and API-to-event naming references for graphics applications captured with Nsight Systems. The naming-difference rule is universal (API names != trace-event names); the platform-specific tables follow.

> **Note**
>
> **Platform scope.** The API-vs-event-name principle and the engine-thread patterns apply on both Windows and Linux. Windows-specific Direct3D 12 / WDDM tables are clearly marked; Linux / Vulkan equivalents are stubbed under "Vulkan / Linux notes" pending population.

## API terminology vs trace-event terminology

The same concept often has different names in the application-level API and in the kernel-level / driver event records. **When describing behaviour from a trace, report what the trace events show, not API-level terminology.**

### Windows (DXGI / D3D12 -> ETW)

| Concept | DXGI / D3D12 API term | ETW event term | Notes |
|---|---|---|---|
| Tearing present | ``DXGI_PRESENT_ALLOW_TEARING`` | ``RedirectedFlip`` with ``FlipTrueImmediate=1`` | "ALLOW_TEARING" never appears in ETW |
| VSync interval | ``SyncInterval`` parameter | ``FlipInterval`` field | Same meaning, different name |
| Present model | ``DXGI_SWAP_EFFECT_FLIP_DISCARD`` | ``D3DKMT_PM_REDIRECTED_FLIP`` | PresentHistory model field |
| Independent flip | (not directly visible) | ``IndependentFlip`` event | Indicates bypass of DWM compositor |

### Vulkan / Linux notes

*To be expanded once we have representative Linux traces.* The analogous Vulkan-to-trace-event naming differences (e.g. ``VkPresentModeKHR`` enum vs. the driver / DRM event names) follow the same pattern: report the trace-event names in findings.

## Common engine thread naming patterns

Engine threading is cross-platform; the same names appear on both Windows and Linux traces.

### Unreal Engine

| Thread name | Role |
|---|---|
| ``GameThread`` / ``MainThrd`` | Game logic, simulation, input |
| ``RenderThread`` / ``RenderThread 0`` | Render command generation |
| ``RHIThread`` / ``RHISubmissionThread`` | Graphics API submission (D3D12, Vulkan, etc.) |
| ``PSOPrecompilePool #N`` | Pipeline state compilation (shader warmup) |
| ``FAsyncLoadingThread2`` | Async asset deserialization |
| ``FAsyncPurge`` | Deferred object destruction |
| ``IoDispatcher`` / ``IoService`` | I/O dispatch and completion |
| ``Background Worker #N`` / ``Foreground Worker #N`` | Task graph workers |
| ``D3D Background Thread #N`` | NVIDIA driver async shader work (Windows) |

### Common middleware threads

| Thread name | Module | Role |
|---|---|---|
| ``DirectStorage Worker`` | ``dstoragecore.dll`` (Windows) | GPU-direct asset loading |
| ``DirectStorage Submit`` | ``dstoragecore.dll`` (Windows) | I/O submission |

Streamline threads (``sl.pacer``, ``sl.dlssg``, ``sl.log``, etc.) ship cross-platform; the module names use ``.dll`` on Windows and ``.so`` on Linux but the thread names match. For what each ``sl.*`` module means and how to tell whether DLSS Frame Generation is actually active rather than merely loaded, see [streamline_detection.md](streamline_detection.md).

### System threads

| Thread name | Platform | Role |
|---|---|---|
| ``csrss.exe Desktop Thread`` | Windows | Window manager, can contend with Present |
| ``dwm.exe`` (DWM) | Windows | Desktop compositor, GPU context user |
| ``dxgmms2.sys`` | Windows | GPU memory manager (kernel) |

*To be expanded: Linux equivalents (compositor threads on X11 / Wayland, DRM scheduler kthreads).*

## D3D12 resource-management APIs -- blocking behaviour (Windows)

These API calls can block the calling thread for significant durations. Durations are ``[MODEL KNOWLEDGE]`` -- verify against actual trace data (``DX12_API`` wall-clock durations) before citing specific values.

| API | Blocking behaviour |
|---|---|
| ``CreateCommittedResource`` | Synchronous -- allocates VRAM, may trigger MakeResident, page-table updates, TLB flush. Can block 10-100 ms under VRAM pressure. |
| ``CreatePlacedResource`` | Usually fast (<1 ms) -- uses pre-allocated heap. Can still trigger page-table work. |
| ``UpdateTileMappings`` | Synchronous on the command queue -- serialises with ``ExecuteCommandLists``. Can hold kernel locks that block other threads. |
| ``Evict`` / ``MakeResident`` | May trigger WDDM paging (page-table updates, data transfers, TLB flush). Duration scales with transfer size and VRAM pressure. |

API call durations from ``DX12_API`` / ``DXGI_API`` / ``VULKAN_API`` are **wall-clock**, not CPU time. See the wall-clock pitfall in [GPU Performance Analysis Pitfalls](https://docs.nvidia.com/nsight-systems/AnalysisGuide/).

### Vulkan / Linux notes

*To be expanded once we have representative Linux Vulkan traces.* The Vulkan equivalents to the D3D12 blocking-call table (e.g. ``vkAllocateMemory``, ``vkBindBufferMemory``, ``vkMapMemory``, ``vkQueueWaitIdle``) follow similar wall-clock-vs-CPU-time distinctions; specific blocking ranges differ by driver.

## WDDM VidMm operation names (Windows)

These show up on ``WDDM_PAGING_QUEUE_PACKET_*`` and related tables in the trace.

| Operation | What it does |
|---|---|
| ``MakeResident`` | Makes a GPU allocation accessible -- may trigger page-table updates and data transfer |
| ``AllocationFault`` | GPU accessed a non-resident page -- triggers synchronous MakeResident |
| ``PagingOpUpdatePageTable`` | Remaps GPU virtual address space |
| ``PagingOpFlushTlb`` | Flushes GPU TLB after page-table changes |
| ``Evict`` / ``TerminateAllocation`` | Removes allocation from VRAM -- frees space for other resources |

### Vulkan / Linux notes

Linux GPU memory management goes through the DRM subsystem (TTM, GEM) rather than WDDM. *To be expanded with the relevant kernel-event names once Linux fixtures are available.*

## See also

- API wall-clock vs CPU-time pitfall: [GPU Performance Analysis Pitfalls](https://docs.nvidia.com/nsight-systems/AnalysisGuide/).
- Windows display pipeline (DXGI / DWM / flip path): [display_pipeline_windows.md](display_pipeline_windows.md).
- Glossary terms: [dx12](../glossary/graphics-glossary/dx12.md), [vulkan](../glossary/graphics-glossary/vulkan.md), [vidmm-vidsch](../glossary/graphics-glossary/vidmm-vidsch.md), [wddm](../glossary/graphics-glossary/wddm.md).
