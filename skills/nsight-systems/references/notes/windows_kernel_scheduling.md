# Windows Kernel Scheduling Model




Understanding how the Windows kernel schedules threads, handles interrupts, and serialises GPU submissions is essential for diagnosing performance root causes that are invisible to standard CPU sampling and scheduling event analysis.

> **Note**
>
> **Platform scope.** This doc is Windows-only -- DPCs / IRQL / WDDM are all Windows kernel concepts. A future ``linux_kernel_scheduling.rst`` will cover the Linux-side equivalents (softirqs, irqbalance, DRM scheduler, eBPF / perf_events).

## Deferred Procedure Calls (DPCs)

DPCs are a critical but invisible-to-most-dimensions source of thread stalling.

#### How DPCs preempt game threads

- DPCs run at **elevated IRQL** (Interrupt Request Level) on the core where the interrupt lands. They preempt whatever thread is scheduled on that core **without generating a sched-out event** -- the thread is stalled for the DPC's duration, but ``SCHED_EVENTS`` will not show it.
- The preempted thread appears "on-CPU" in scheduling data and CPU sample counts, but it is not doing useful work during the DPC.
- DPC duration is only visible via **DxgKrnl Profiler events** (ETW ``etwEventId`` 105/106 start/stop pairs).

#### GPU interrupt affinity

- On most Windows systems, **GPU interrupts are affinitised to core 0 by default**. The GPU driver's interrupt service routine (ISR) and its deferred DPC handler run on core 0 unless the affinity has been explicitly changed.
- The DPC Delegate Thread mapping (visible in ``ThreadNames`` as ``DPC Delegate Thread [N]``) shows which logical core processes DPCs, but the ISR itself (``DpiFdoMessageInterruptRoutine``) fires in any thread's context on that core.
- When a game's critical-path thread (e.g. the last ``Job.Worker`` to finish a parallel-for barrier) happens to run on core 0, DPC preemption directly extends the frame.

#### DPC duration decomposition

DPC duration scales with child work -- the DPC handler processes GPU completions and resubmits commands. More completions = more ``DdiSubmitCommandToHwQueue`` calls inside the DPC. This is normal scaling.

To determine whether elevated DPC duration is a **symptom** (backlog) or closer to a **root cause** (contention), decompose on three axes:

| Axis | Signal | Interpretation |
|---|---|---|
| **Child count scaling** | DPC has more children than in clean frame | Backlog -- completions piled up while the CPU was busy. The DPC is processing the queue; it is an *effect* of the extended frame. |
| **Per-child duration scaling** | Each ``DdiSubmitCommandToHwQueue`` takes longer (e.g. 6.6 us vs 0.17 us = 34x) | Kernel-side contention -- lock contention, VidMm serialisation, or memory pressure in the DxgKrnl path. Closer to root cause. |
| **Temporal ordering** | DPC storm begins *before* vs *after* the frame extension trigger | DPCs after the sim overrun = cleanup. DPCs before the frame extends that block the submission path = potential cause. |

#### Critical-path impact

If a ``Job.Worker`` on core 0 is the last to finish a parallel-for chunk, and DPCs steal 2-3 ms from it, the barrier waits for that worker -- extending the frame. The DPC time is invisible to CPU sample counts (the worker appears "on-CPU") but the worker is not doing useful work during the DPC.

#### Investigation steps

For each problem frame:

1. Which game threads run on DPC-heavy cores? (per-core ``SCHED_EVENTS`` sched-in counts)
2. Total DPC time interrupting those threads (pair ``DdiNotifyDpc`` / ``DpiDpcForIsr`` start/stop via DxgKrnl Profiler events).
3. Per-call DPC duration vs clean -- contention signal.
4. Whether the stalled thread is on the critical path (barrier dependency from scheduling data).

## WDDM queue submission serialisation

Multiple threads submitting to the same D3D12 / WDDM engine queue serialise in the kernel (``dxgkrnl.sys``). This affects both:

- **DPC submissions** (``DdiSubmitCommandToHwQueue`` -- called from within the interrupt handler).
- **User-mode submissions** (``DxgkSubmitCommandToHwQueue`` -- called from the Present Thread, D3D12 Submission Thread).

When both paths hit the same engine queue simultaneously, they contend on the kernel queue lock.

#### Symptoms

- DPC per-submission duration spikes (e.g. 6.6 us vs 0.17 us normal = 34x).
- DPC total duration scales with submission count x per-submission delay.
- GPU context switches during submission add preemption handshake latency to each call.

#### Investigation

When a DPC shows per-call slowdown (per-call ratio diff against the clean reference), check ``DxgkSubmitCommandToHwQueue`` events from other threads during the same window. If the Present Thread or D3D12 Submission Thread is also submitting to the same 3D engine context, lock contention is the likely cause.

## Core-level scheduling topology

When investigating frame extensions, check the core-level scheduling picture -- not just per-thread CPU samples.

#### Key metrics

1. **Active cores per time bin** -- ``COUNT(DISTINCT cpu) FROM SCHED_EVENTS WHERE isSchedIn=1`` in small bins (10-50 ms) around the problem region. Sudden jumps (e.g. 11 -> 24) indicate a scheduling regime change.
2. **Peak simultaneous on-CPU threads** -- sweep-line on sched-in / sched-out events. Distinguishes "many cores touched by rapid migration" from "many threads genuinely concurrent".
3. **Migration rate** -- core-to-core transitions per thread per unit time. If the migration rate is the same in clean and affected windows, core spreading is not the cause.
4. **HT sibling activation** -- on machines with hyperthreading, HT siblings share physical resources. Threads on HT siblings get ~60-70% throughput. But verify actual simultaneous contention -- a thread briefly touching an HT core during migration is not the same as two threads sharing a physical core for the duration of the frame.

#### OS scheduling context (P-core only, no E-cores)

The Windows scheduler prioritises physical cores, then E-cores, then HT siblings. On a machine with only P-cores and HT, threads should stay on physical cores unless total concurrent thread count exceeds the physical core count. If HT siblings are used with fewer concurrent threads than physical cores, the scheduler has lost affinity (e.g. after a mass-wake from a barrier).

## Cross-process thread identification

When investigating scheduling anomalies (core spreading, long thread runs, migration spikes), always check whether third-party processes changed behaviour or are just measuring the game's idle time.

A non-game thread showing an anomalous long run during a problem region is usually a **symptom indicator** -- it measures how long the game was idle -- not a cause. Verify by checking:

1. Run durations trace-wide -- is the long run genuinely unusual, or is it explained by game threads not preempting it?
2. Whether the thread's sched-out reason is ``NonBlocked`` (preempted) in clean frames but the run extends in the problem region because preemptions stop.
3. Whether the thread's run duration scales inversely with game thread activity (longer runs when game is idle = symptom, not cause).

## See also

- Schema gotchas for ``SCHED_EVENTS`` and the block-reason ENUM tables: [SQLite Schema Pitfalls](https://docs.nvidia.com/nsight-systems/AnalysisGuide/).
- Common pitfalls when attributing CPU stalls: [GPU Performance Analysis Pitfalls](https://docs.nvidia.com/nsight-systems/AnalysisGuide/).
- Windows display pipeline (where many DPCs originate from): [display_pipeline_windows.md](display_pipeline_windows.md).
- Glossary: [gpu-context-switch](../glossary/graphics-glossary/gpu-context-switch.md), [wddm](../glossary/graphics-glossary/wddm.md), [thread-state](../glossary/nsys-glossary/thread-state.md).
