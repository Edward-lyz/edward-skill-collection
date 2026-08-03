# DxgKrnl events

**Short:** ETW events emitted by ``Microsoft-Windows-DxgKrnl``, the DirectX graphics kernel; nsys subscribes to a subset of them to reconstruct GPU scheduling, dispatch, presentation, and video memory state on Windows.

## Provider basics

- Provider name: ``Microsoft-Windows-DxgKrnl``. GUID: ``{802EC45A-1E99-4B83-9920-87C98277BA9D}``.
- Events come from kernel-mode ``dxgkrnl.sys``; a real-time subscription requires admin (``SeSystemProfilePrivilege``).
- Timestamps are scheduler-accurate and independent of the application's user-mode call stack, which is what makes the provider the canonical ground truth for "what the GPU did and when".

## Keyword groups nsys enables

nsys exposes the dxgkrnl events under a few logical capture groups (VSync, VidMm, Wddm, Memory, FrameCoreEquivalent); on the wire these map to public manifest keywords:

| Keyword | Mask | Used for |
|---|---|---|
| ``Base`` | 0x00000001 | scheduler + dispatch packets, present |
| ``References`` | 0x00000004 | VidMm residency / paging detail |
| ``Resource`` | 0x00000040 | allocations, devices, contexts |
| ``Memory`` | 0x00000080 | VidMm budget / usage / commitment |
| ``GPUScheduler`` | 0x00008000 | software scheduler activity |
| ``HardwareSchedulingLog`` | 0x04000000 | WDDM 2.7+ HWS scheduler log |
| ``Present`` | 0x08000000 | present / vsync DPC |

## Scheduling: software queue (per-context)

The dxgkrnl scheduler maintains a per-context software queue. Each unit of work pushed onto it is a "queue packet".

- ``QueuePacket_Start`` - id 178, opcode ``Start``. Payload: ``hContext``, ``PacketType`` (Render, Paging, Wait, Signal, Device, ContextSwitch, MMIO flip, ...), ``SubmitSequence`` (per-context monotonic id), ``DmaBufferSize``, ``AllocationListSize``, ``PatchLocationListSize``, ``bPresent`` (set if this packet is tied to a flip), ``hDmaBuffer``, ``pQueuePacket``, ``ProgressFenceValue``. Newer versions (ids 244 / 245) add a ``Flags`` field, sync-object array, and an optional fence-value array.
- ``QueuePacket_Info`` - id 179. Same identification (``hContext``, ``PacketType``, ``SubmitSequence``); used for in-flight state updates.
- ``QueuePacket_Stop`` - id 180. Adds ``bPreempted`` and ``bTimeouted``; a cancelled packet sets ``bPreempted=TRUE``. Pair Start to Stop via ``hContext`` + ``SubmitSequence`` to get the software-queue lifetime.

## Dispatch: DMA packets on GPU engines

When the scheduler hands work to a GPU engine, it emits the ``DmaPacket`` family. These pair with ``QueuePacket`` events via ``ulQueueSubmitSequence`` and are what nsys renders as the GPU engine activity bar.

- ``DmaPacket_Start`` - id 175. Payload: ``hContext``, ``hQueuePacketContext``, ``PacketType``, ``uliSubmissionId``, ``ulQueueSubmitSequence``, ``pDmaBuffer``, ``QuantumStatus``. Marks the GPU-side start of execution on a specific engine node.
- ``DmaPacket_Info`` - id 177. Legacy combined form. Carries ``InterruptType`` (CompletedSync, Preemption, PageFault), ``QuantumStatus``, and on page-fault, ``FaultedVirtualAddress``, ``PageFaultFlags``, ``FaultedProcessHandle``.
- ``DmaPacket_Stop`` - id 176. Payload: ``hContext``, ``PacketType``, ``uliCompletionId``, ``ulQueueSubmitSequence``, ``bPreempted``. Fires when the kernel observes the packet has fully retired.

A complete GPU work item ties ``QueuePacket_Start -> DmaPacket_Start -> DmaPacket_Stop -> QueuePacket_Stop`` via ``hContext`` + sequence number.

## Hardware-scheduled GPU (HWS, WDDM 2.7+)

With Hardware-Accelerated GPU Scheduling enabled, quantum management and context switching move onto a GPU-resident scheduler. The CPU-side ``DmaPacket_*`` stream still exists but is sparser; the authoritative record is the HWS log.

- ``HwQueue_Start`` - id 422. Payload: ``hContext``, ``hHwQueue``, ``ParentDxgHwQueue``. A hardware-queue object has been created and bound to a user-mode context.
- ``HwSchedDmaPacket_Begin`` **/** ``_End`` - ids 450 / 451. Firmware-reported start and end of a DMA packet on a hardware queue. Payload includes ``hHwQueue``, ``ProgressFenceValue``, and at ``_Begin`` also ``pDmaBuffer``, ``ntStatus``, ``NumberOfQueuedPendingFlip``. These take the place of ``DmaPacket_Start`` / ``_Stop`` when HWS is in use.
- ``SchedulingLog`` - id 432. A rolling scheduler decision log delivered in bulk; payload includes adapter / node / engine ordinals, CPU and GPU calibration timestamps, and an opaque binary log of context-state entries. nsys decodes the log into per-state-change synthetic events and uses the CPU / GPU timestamps for clock calibration.

``HardwareSchedulingLog`` is very high volume; nsys enables it only when GPU context switching is requested.

## Presentation

- ``Present`` - id 184. Fires when a Present call from D3D9 / D3D11 / DXGI enters the kernel. nsys ties it to the swap chain and to the matching DXGI ``Present_Start`` / ``_Stop`` on the API thread.
- ``VSyncDPC`` - id 17. Payload: ``VidPnSourceId`` (screen), ``pDxgAdapter``. Fires once per scanout per monitor from the vsync DPC; nsys keys a per-screen frame counter on ``(adapter, VidPnSourceId)``, which is what frame-rate and frame-pacing rows are built from.

## Video memory (VidMm)

- ``VidMmProcessBudgetChange`` - id 366. Payload: ``NewBudget``, ``OldBudget``, ``pDxgAdapter``, ``ProcessId``, ``PhysicalAdapterIndex``, ``NewPriorityBand``, ``OldPriorityBand``, ``NewVisibilityState``, ``OldVisibilityState``, ``MemorySegmentGroup``. The OS just changed how much VRAM a process is allowed to keep resident.
- ``VidMmProcessUsageChange`` - id 367. Payload: ``NewUsage``, ``OldUsage``, adapter / process / segment-group identification. Real-time usage tracking; what task managers report as "GPU memory".
- ``VidMmProcessDemotedCommitmentChange`` - id 370. Payload: ``Commitment``, ``OldCommitment``, ``PriorityClass``. A background process exceeded its budget and was demoted.
- ``VidMmProcessCommitmentChange`` - id 371. Newer commitment-tracking variant.
- ``VidMmEvict`` - id 321. Allocation evicted from local video memory (complements ``EvictAllocation`` from the device side).
- ``TotalBytesResidentInSegment`` - id 274. Payload: ``DxgAdapter``, ``SegmentId``, ``TotalBytesResident``. Periodic census per memory segment.
- ``ReportSegment`` - id 78. Payload: ``pDxgAdapter``, ``Size``, ``MemorySegmentGroup``, ``ulSegmentId``, ``Flags``. Static segment metadata and capacity, emitted per process.
- ``PagingQueuePacket_Start`` **/** ``_Info`` **/** ``_Stop`` - ids 322 / 324 / 325. Payload: ``DxgAdapter`` or ``DxgDevice``, ``PagingQueue``, ``PagingQueuePacket``, ``SequenceId``, ``VidMmOpType``, ``PagingQueueType``; ``_Stop`` adds ``ExecutionTime100ns``. One entry per paging packet on the paging queue.
- **PagingOp events** - ids 306-314. Fine-grained memory ops (virtual transfer, virtual fill, init-context resource, update page table, flush TLB, update context allocation, notify residency, sysmem commit / uncommit). Gated by the ``VidMm`` group.

## Allocations

- ``AdapterAllocation_Start`` **/** ``_Stop`` **/** ``_DCStart`` - ids 33 / 34 / 35. Payload: ``hProcessId``, ``hDevice``, ``pDxgAdapter``, ``Flags``, ``allocSize``, alignment, read / write / preferred / eviction segment ids, ``Priority``, allocation handles, ``Format``, ``SwizzledFormat``, ``Width``, ``Height``, ``Pitch``, ``Depth``, ``SlicePitch``, ``BackingStoreWasPinned``, ``PhysicalAdapterIndex``, ``PageTableOrDirectory``. Adapter-wide allocations (shared system memory).
- ``DeviceAllocation_Start`` **/** ``_Stop`` **/** ``_DCStart`` - ids 36 / 37 / 38. Payload: ``hProcessId``, ``hDevice``, ``pDxgAdapter``, ``hVidMmAlloc``, ``hVidMmGlobalAlloc``, ``hDxgResource``, ``hDxgSharedResource``, thunk handles, ``pVirtualAddress``. Per-device allocations linked to VidMm and DxgKrnl handles.
- ``EvictAllocation`` - id 74. Payload: ``hGlobalAllocationHandle``. Allocation evicted from GPU memory; nsys uses it to detect memory pressure.
- ``AllocationFault`` **/** ``MarkAllocation`` **/** ``PageInAllocation`` - ids 71 / 72 / 73. Fine-grained allocation state changes (fault on access, mark dirty, demand page-in).
- ``MemoryTransfer`` - id 50. Payload: ``hProcessId``, ``hAllocationGlobalHandle``, ``pDmaBuffer``, offset, size, plus a transfer-kind enum that nsys surfaces as ``SystemToDevice``, ``DeviceToSystem``, ``AgpToDevice``, ``DeviceToAgp``, ``EvictToAlternateva``, ``RestoreFromAlternateva``, ``Discard``, or ``UnknownTransfer``. GPU memory transfer / copy / fill.

``_DCStart`` opcodes emit at trace start to rundown all live allocations; nsys treats them as if they were ``_Start``.

## Adapter, device, context

- ``DpiReportAdapter`` - id 110. Payload: ``pDxgAdapter``, ``ConfigSpaceSize``, ``ConfigSpace``, chain ids, ``BusType``, ``VendorID``, ``DeviceID``, ``SubVendorID``, ``SubSystemID``, ``RevisionID``, ``AdapterLuid``. GPU hardware identity; the LUID is how multiple adapters are disambiguated.
- ``Device_Start`` **/** ``_Stop`` - ids 27 / 28. Payload: ``hDevice``, ``pDxgAdapter``, optional ``hProcessId``. Logical device created or destroyed.
- ``Context_Start`` - id 30, ``Context_DCStart`` - id 32. Payload: ``hContext``, ``hDevice``, ``NodeOrdinal``, ``Flags``. Establishes which GPU engine a context targets; ``Start`` carries process id, ``DCStart`` does not.
- ``SelectContext`` **/** ``SelectContext2`` - ids 23 / 436. Payload: ``hContext``, ``pDxgAdapter``, ``NodeOrdinal``. Maps a context onto an engine at scheduling time; ``SelectContext2`` is the modern variant.
- ``AssociateDxgSchedulerObject`` - id 433. Payload: ``pDxgObject``, ``hOsHandle``. Maps OS handles to scheduler pointers, used to resolve context identity across event versions.

## Engine identity

- ``NodeMetadata`` - id 250. Payload: ``pDxgAdapter``, ``NodeOrdinal``, ``EngineType``, ``FriendlyName`` (variable length). One row per GPU engine node at trace start; the friendly name comes from the user-mode driver and is what nsys labels engine rows with. Engine types include 3D (graphics), Compute, Copy / DMA, Video Decode, Video Encode, Video Processing.

## Practical caveats

- Volume: with ``Base | Present`` plus the Performance channel a busy game emits hundreds of thousands of events per second. ``HardwareSchedulingLog`` and the VidMm paging stream add another order of magnitude.
- Elevation: real-time consumption of a kernel ETW provider needs admin.
- ``_DCStart`` opcodes emit at trace start to rundown live state (contexts, devices, hardware queues, allocations). nsys handles these as start events; a tool that only watches ``Start`` / ``Stop`` will see orphan stops.
- HWS and the legacy DMA stream can both fire on HWS-capable systems; the legacy stream is sparser and the HWS log is the authoritative record. Cross-correlate via ``hContext`` + submit sequence.
- nsys runs a two-pass parse: pass one builds the adapter / device / context maps from ``SelectContext``, ``NodeMetadata``, ``HwQueue_Start``, and the DC starts; pass two emits the timeline events that need those maps to resolve identities.

## See also

- [ETW](etw.md)
- [WDDM](wddm.md)
- [VidMm / VidSch](vidmm-vidsch.md)
- [DMA packet](dma-packet.md)
- [Queue packet](queue-packet.md)
- [GPU engine](gpu-engine.md)
