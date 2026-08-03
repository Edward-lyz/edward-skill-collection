# Stutter Analysis




Classification reference for stutter in graphics traces: game stutter (CPU present-to-present cadence), display stutter (flip-to-flip cadence), the relationship between them, the rolling-median detection method and its thresholds, the common causes, and the controlled mechanism vocabulary a finding attributes to. The investigation procedure itself lives in the [investigation_methodology](../curated/investigation_methodology.md) overlay; this note is the subject-matter reference it draws on. For the single term, see the [stutter](../glossary/graphics-glossary/stutter.md) glossary entry.

Use this when asked why a game is stuttering, what is causing frame-time spikes, hitching, or janky frames, or what the stutter root cause in a report is.

When analyzing stutters, always distinguish between **game stutters** and **display stutters**. They have different causes, different impacts, and require different data to diagnose.

## Game stutters (CPU present-to-present)

**What it is:** Variation in the interval between consecutive CPU Present() calls -- often measured from DXGI or DxgKrnl ETW start events, or WDDM present-queue submission events. This reflects the game engine's frame production cadence: how evenly the engine processes input, simulates, renders, and submits frames.

**Why it matters even if the display absorbs it:**
- **Input latency:** Uneven frame production means uneven input sampling intervals. Even if the display shows smooth output, the game may poll input at 13ms then 26ms then 13ms, making controls feel inconsistent.
- **Simulation consistency:** Variable frame times mean variable simulation delta-t, which can affect physics, animation, and gameplay feel.
- **Reflex end-to-end latency:** If Reflex is active, game-side frame pacing directly affects the input-to-render latency pipeline. A long game frame delays the entire chain (see [reflex_overview.md](reflex_overview.md)).

**Stutter detection -- rolling baseline method:**

Use a **rolling median baseline** (19-frame window, center-aligned) rather than a single global median. This adapts to scene changes and works across all framerates. The constants below are the detection rule; a report's frame-time classifier emits these values directly, so quote its output rather than recomputing.

**Stutter**: deviation from local rolling baseline exceeds **both**:
- **Absolute**: >4.0 ms deviation from local baseline
- **Relative**: >20% deviation from local baseline

**Micro-stutter**: deviation exceeds 5% of local baseline but falls below the stutter thresholds (either <4.0 ms absolute or <20% relative, and <8.0 ms absolute cap).

**Oscillation**: alternating long-short frame pattern with >1.0 ms absolute deviation and >5% relative deviation. Density >25% of frames = minor, >50% = major.

**Catch-up exclusion**: a frame with negative deviation that is also shorter than 0.5x the local baseline is the short half of an oscillation pair (common under DLSS Frame Generation), not an independent stutter. Exclude it from stutter counts.

**Severity classification:**
- Micro-stutters: minor if >=10% of frames, major if >=25%
- Stutters: minor if >=0.5% of frames, major if >=1.0%
- Max stutter severity: minor if worst stutter >=100% of avg frametime, major if >=200%

**Quick screening indicators** (for initial triage before full classification):
- Frame time stdev > 10% of median
- Long-short oscillation patterns (e.g. 26ms/13ms pairs)
- P99 > 1.3x median (investigation trigger) or P99 > 1.5x median (likely stutter)

## Display stutters (flip-to-flip)

**What it is:** Variation in the interval between consecutive display updates (hardware flips / scanouts). This is what the user actually sees.

**Why it matters:**
- Directly visible as judder, hitching, or held frames
- A single long flip (2x normal) is perceptible even if surrounding frames are smooth

Measured from display ETW events such as `MMIOFlipMultiPlaneOverlay3` (flip-to-flip intervals); see [display_pipeline_windows.md](display_pipeline_windows.md) for the present path.

**Stutter detection:** Apply the same rolling baseline method as game stutters (see above). For display flips, the rolling baseline adapts to VRR timing changes.

**Quick screening indicators** (SQLite-only):
- Any flip interval > 1.5x the local median flip interval
- Dropped frames: GPU present count > display flip count
- Flip intervals clustering at exact 2x multiples of normal (missed flip pattern)

## The relationship between game and display stutters

Game stutters and display stutters are **not the same thing** and do not always correlate:

| Scenario | Game stutter? | Display stutter? | User impact |
|---|---|---|---|
| GPU finishes on time, flip scheduling misses a beat | No | Yes | Visual hitch, but input latency unaffected |
| CPU present timing oscillates, flip queue absorbs it | Yes | No | Input feels inconsistent, but visually smooth |
| GPU overloaded, frame takes 2x normal | Yes | Yes | Both visual and input impact |
| Frame queue drains, GPU catches up | Compensating short frame | No (queue absorbs) | Short frame may feel like a "snap" |

## Classifier output rules

When reporting stutter classifier results:
- **Quote the output exactly** -- do not paraphrase or round numbers
- Include for each layer: severity grade, stutter count, stutter %, max stutter, avg frametime, micro-stutter %, and oscillation % (CPU only)
- Present as a table for easy comparison across layers
- These are deterministic values -- they must match between any two analyses of the same trace

## Analysis approach

When investigating stutters, **always measure both CPU and display layers** and **investigate both with equal depth**:

**CPU-side Present events are submission timing, not display timing.** Only assert display-visible stutter when confirmed by flip-to-flip data, or explicitly caveat: "These are CPU-side present intervals. Without display flip data, we cannot confirm whether these stutters are visible to the user."

**Locating a specific frame:** use the `frame_summary` report fact (`report-fact --intent frame_summary`, alias `frame_window`; `--frame <N>` for one frame). It returns each frame's `[start_ns, end_ns)` window and `frame_ms` (0-indexed, GUI order), auto-detecting the source (DXGI/Vulkan/OpenGL present rows, else DxgKrnl ETW Present). With DLSS Frame Generation active, CPU present cadence bunches, so the present index may not equal the displayed frame. Then scan that frame's window with `report-fact --intent frame_scan --frame <N>`: it returns in-window ETW event counts plus WDDM eviction/paging/DMA/context-switch counts (and per-ms rate) against a baseline neighbor frame. Those counts are evidence, not a verdict -- attribute the cause yourself with magnitude match and temporal ordering; see [sql_query_tips.md](sql_query_tips.md).

**Per-API call breakdown:** to quantify which DX12/Vulkan/OpenGL API calls dominate a frame, use the graphics-API report facts instead of hand-writing SQL against `DX12_API`/`VULKAN_API`/`OPENGL_API` (they auto-detect the active API and bake the `nameId`->`StringIds` join and the `end - start` duration). `report-fact --intent graphics_api_summary --frame <N>` returns each API's count and total/avg/max ms ranked by total time, with `pct_of_frame` and the paired GPU workload table; `--intent graphics_api_distribution` returns session-wide per-API duration percentiles (min/median/p95/p99/max); `--intent graphics_api_timeline --metric <api_name>` detects back-to-back serialized calls on the in-order command queue (the tiled-resource / allocation-churn pattern, e.g. `UpdateTileMappings` or `CreateCommittedResource` bursts).

**Thread blocking and callstacks:** to tell whether a thread is parked in a per-frame wait or busy on CPU, use the scheduling report facts instead of hand-writing the `SCHED_EVENTS` `LEAD` pairing, the `globalTid` decode, or the callchain joins. `report-fact --intent thread_scheduling` (add `--frame <N>` to scope to a frame) returns per-thread upper bounds for on-CPU and blocked (off-CPU) time, with `*_confirmed_pct` showing how much of each bound comes from confirmed sched-in/sched-out pairs. When confirmation is low, missing transitions have inflated the upper bound, so treat it as a ranking signal rather than an exact duration. The fact also returns the `dominant_block_reason` (UserRequest = voluntary fence/present wait, Resource/KeyedEvent = lock contention, NonBlocked/Preempted = oversubscription) and the top `OSRT_API` blocking waits (e.g. `WaitForSingleObjectEx` on Windows, `pthread_cond_wait` on Linux). Then `report-fact --intent callstack_summary --metric <globalTid>` (the `globalTid` from `thread_scheduling`) returns leaf-symbol `hotspots` (`cpuCycles=1` periodic samples) and `blocked_stacks` (`cpuCycles=0` scheduling event callstacks) so you can name the call the thread came off CPU in. Counts are evidence, not a verdict -- confirm with magnitude match and temporal ordering.

1. CPU present-to-present (game frame time) -- for engine/input health
2. Display flip-to-flip (MMIOFlip timing) -- for visual smoothness
3. GPU present completion-to-completion -- to isolate GPU vs CPU vs display causes
4. Frame drop count: `GPU presents - display flips` = frames the GPU rendered but the user never saw

Then compare: if game stutters exist but display doesn't show them, the flip queue is absorbing them (good for visuals, but input latency may still be affected). If display stutters exist but game timing is clean, the issue is in the flip scheduling path (driver, display controller, compositor).

### Equal investigation depth -- do not deprioritize game frame stutters

Display stutters are user-visible, but **game frame stutters are where the actionable root causes live**. A display stutter caused by the flip scheduling path is often unfixable by the game developer. A game frame stutter caused by DirectStorage, PSO compilation, or asset streaming is directly actionable.

**Both layers must receive full root cause investigation.** Do not stop at "0 frames exceed 1.5x median" for game frame timing. Also investigate:

1. **Tail analysis**: What causes the P95-P99 tail? Even if no frame crosses the 1.5x threshold, a P99 at 1.35x median with a clear cause (e.g. streaming bursts) is a meaningful finding.
2. **Short frame analysis**: Frames significantly below the median (e.g. <0.7x median) often pair with subsequent long frames. Identify these and check if they form long-short oscillation patterns. Measure the pattern's periodicity and correlate with engine activity. Do they correlate to DLSS FG pacing with flip metering as described in [display_pipeline_windows.md](display_pipeline_windows.md)?
3. **Per-thread differential**: Compare CPU periodic samples per thread during tail frames vs median frames. Look for threads with >2x differential activity. Follow differentially active threads to their callstacks.
4. **Streaming/loading correlation**: Check DirectStorage Worker, IOSubmitThread, and async copy engine activity during tail frames. Asset streaming is one of the most common causes of game frame variance.
   - **Metric normalization**: When comparing any metric (GPU counters, CPU sample counts, event counts, byte totals) between stutter and non-stutter windows, check whether values are rates/percentages (already normalized) or cumulative counts/sums. Unnormalized values must be divided by window duration before comparison -- a longer frame naturally accumulates more at the same rate. Signs of unnormalized data: "Throughput %" values exceeding 100, raw cycle counts, event totals.
5. **PSO compilation correlation**: Check AsyncPsoQueue threads during tail frames. Runtime shader compilation causes frame-time spikes that can persist for the life of a game session.
6. **GPU memory allocation activity**: Always check ETW events for GPU memory management -- this is a standard investigation step regardless of whether streaming is suspected. Compare event counts between stutter and clean windows of equal duration:
   - **Allocation events**: `DeviceAllocation`, `AdapterAllocation`, `ProcessAllocationDetails` -- new GPU resources being created
   - **Residency events**: `VidMmMakeResident`, `VidMmTryOperation`, `VidMmSelectOperation`, `AllocationFault`, `PageInAllocation` -- pages being made GPU-accessible
   - **Page table events**: `PagingOpUpdatePageTable`, `PagingOpFlushTlb`, `GpuVirtualAddressRange`, `GpuVirtualAddressRangeMapping` -- GPU VA space remapping
   - **Eviction events**: `TerminateAllocation`, `PagingOpDiscard`, `SetAllocationPriority` -- old resources being evicted under vidmem pressure
   - A burst (5-10x above baseline) during stutter frames indicates vidmem pressure or heavy resource churn. This can come from streaming, but also from scene transitions, LOD changes, or any workload that creates/destroys GPU resources.
   - **BAR1 promotion/demotion**: With BAR1 (resizable BAR) enabled, the NV driver promotes sysmem allocations to BAR1 vidmem. Under vidmem pressure, these promoted allocations should be among the first demoted back to sysmem -- returning to the original intended placement. This usually isn't problematic, but it's difficult to determine exactly what was demoted from the ETW events alone. Be aware that demotion activity during stutter windows may be BAR1 promotions being reclaimed (benign) or critical vidmem allocations being spilled (problematic). Report the activity without assuming severity.
7. **Cross-tabulation**: For each candidate cause (streaming, PSO compilation, memory allocation, etc.), build a 2x2 table: cause present/absent x tail frame/normal frame. This distinguishes true contributors from concurrent-but-unrelated activity.

**The 1.5x-median threshold is for classifying severity, not for deciding whether to investigate.** Any frame time variance with an identifiable cause is worth reporting, because:
- The flip queue may not always absorb it (different GPU, different resolution, different scene)
- It affects input sampling consistency
- It may worsen under load in more demanding scenes
- It is actionable feedback for the game developer

## CPU-bound vs GPU-bound: GPU idle decomposition

To classify whether a stutter frame is CPU-bound or GPU-bound, decompose its frame time on the GPU timeline as `cpu_frametime ~= gpu_busy_ms + gpu_idle_ms`. `gpu_idle_ms` is the **largest contiguous GPU-idle gap** overlapping the stutter window -- wall-clock time where GR Active (3D + compute), compute warps, and the copy engines are *all* below ~5% (from `GPU_METRICS`); when GPU metrics are absent, fall back to the largest gap in the union of *all* WDDM packet engine types. Measuring a contiguous wall-clock gap (not a single logical frame) avoids the DLSS Frame Generation frame-alignment error, and counting only genuine GR/compute/copy idle avoids the 3D-packet-only trap of scoring async-compute / frame-generation work as "idle".

Classify against what is usual for **this** trace, not a fixed percentage. Take the baseline from the clean-reference window (median over clean frames), then decompose the stutter excess:

- `excess_idle_ms = frame_gpu_idle_ms - baseline_idle_ms`
- `excess_busy_ms = frame_gpu_busy_ms - baseline_busy_ms`

| Which term dominates the stutter delta | Classification | Action |
|---|---|---|
| `excess_idle_ms` is the dominant share of the delta | **CPU-bound** (GPU starved for submission) | Find the submit-path blocker (below) |
| `excess_busy_ms` dominates | **GPU-bound** (more GPU work) | Verify GPU packet duration vs clean; not a starvation story |
| neither dominates | Other (display, scheduling, noise) | Investigate elsewhere |

This is self-normalising: a trace that normally runs ~0% idle and spikes to 5% on a stutter frame is **anomalous** (the 5% is almost the entire excess); a trace that idles ~8% everywhere tells you nothing when one frame hits 9%. Judge by deviation from the clean baseline. The raw `gpu_idle_ms / cpu_frametime` fraction is only a sanity gate on top of the baseline test: above ~0.10 is confidently idle-driven, ~0.05-0.10 is an ambiguous band where you must run the GPU-context check before classifying CPU-bound, and below the trace noise floor is not idle-driven.

**`gpu_idle_ms` is a symptom, never the magnitude-match cause.** It quantifies *that* the frame is CPU-bound, not *why* submission stopped. The cited cause duration must be a single critical-path entity's wall-clock duration (a blocked thread's off-CPU time, a sync-compile thread's on-CPU time, a fence wait). A finding whose cause value is the idle gap, present gap, or frame delta at ~100% ratio is tautological -- reject it (see [Magnitude match](#magnitude-match-single-thread-wall-clock-only)).

**GPU-context check (mandatory in the 0.05-0.10 band, good practice always).** `gpu_idle_ms` measures *total* GPU idle, so a long frame with **low** idle does not by itself prove the game was busy: the GPU work may belong to **another context** while the game's own packets starved. Query the contexts active in the window and map each non-game context to its owning process (`WDDM_QUEUE_PACKET_START_EVENTS` -> submitting `globalTid` -> `PROCESSES`).

When idle is the dominant excess, there are three terminal outcomes:

1. **Game's context idle + blocker found** -> CPU-bound; name the generator (blocked thread, lock, fence, or sync shader compilation). Do not rule this out merely because GPU packets stay long elsewhere in the window -- that tests sustained GPU-busy, a different hypothesis.
2. **Another context filled the gap** -> `gpu_context_contention`. This is a real finding, not a dead end: root-cause the originating app -- name the process presenting on the competing context (compositor `dwm.exe`, an overlay, a capture tool, or a second 3D app) and report that it delayed the game's packets.
3. **Game's context idle + no blocker + no competing context** -> conclude **unattributed** (low confidence). Exhausting the hypotheses and saying the cause is undetermined is the correct result here.

### GPU busy during a CPU wait: fence-wait vs CPU-side barrier

When a thread shows `UserRequest` blocks and the wait target is unknown, GPU state during the wait is the strongest discriminator between the two opposite root causes above. Query the 3D-engine (`engineType = 1`) WDDM packets in the wait window and look for a gap between one packet's `end` and the next packet's `start` with no other engine work filling it:

- **Gap present (GPU idle during the wait)** -> the GPU was starved; the cause is CPU-side (a worker/task barrier or serialised submission), so reduce the CPU barrier.
- **No gap, packets back-to-back (GPU busy through the wait)** -> the thread blocked on a **GPU fence**; the render packet is longer than the target frame interval, so the frame is GPU-bound.

```sql
SELECT s.start, s.end, (s.end - s.start) / 1e6 AS packet_ms
FROM WDDM_QUEUE_PACKET_START_EVENTS s
WHERE s.engineType = 1
  AND s.start BETWEEN <win_start_ns> AND <win_end_ns>
ORDER BY s.start
```

Both patterns look identical in a CPU scheduling view (both produce `UserRequest` blocks); only the GPU timeline separates them. For the `SCHED_EVENTS` shape and `globalTid` decode these queries rely on, see [sql_query_tips.md](sql_query_tips.md).

## Magnitude match: single-thread wall-clock only

When computing the magnitude of a claimed cause and comparing it to the frame delta, use the **wall-clock excess of the single critical-path thread or phase**, never a sum of durations from multiple threads, multiple phases, or concurrent blocks. Concurrent work overcounts: if thread A takes 3ms and thread B takes 4ms in parallel, the wall-clock impact is `max(3, 4) = 4ms`, not 7ms, and summing them yields a ratio above 100% that is arithmetically invalid, not just imprecise.

**Valid comparisons:**
- A single thread's start-to-end duration for the stutter frame (NVTX phase start/end, or `SCHED_EVENTS` first-sched-in to last-sched-out for that thread) minus the same thread's median duration over clean frames.
- A single discrete blocking event (one off-CPU wait), compared directly against the frame excess.

**Invalid comparisons:**
- Summing all off-CPU blocks on a thread across a frame -- the blocks may span phases that run concurrently with GPU work; only the critical-path subset matters.
- Summing durations across multiple threads -- only the one on the critical path determines frame delivery time.
- Summing WDDM packet durations into an "aggregate GPU work" span. Packets run on parallel engines and overlap, so a summed GPU work-span larger than the frame itself is a measurement artifact, not a workload spike. Quantify GPU load by the contiguous GPU-busy wall-clock span and GR Active, never by the sum of packet durations.
- Any comparison producing a ratio above ~130% without an explicit explanation of why the cause duration can exceed the effect (for example, the measurement window extends beyond the frame boundary).

If you cannot isolate the single critical-path phase, state the ratio as `[ESTIMATED]` and explain that individual block durations were observed but the critical-path subset could not be isolated without callstack confirmation.

## Common stutter causes

A non-exhaustive reference of causes encountered in practice. For each, the key check is listed; the controlled mechanism tag each maps to is in the next section.

### Game engine / application

| Cause | What to look for |
|---|---|
| **Shader compilation (PSO)** | `PSOPrecompilePool` or D3D background threads active during stutter. Often a consequence of a pipeline stall, not the root cause -- check temporal ordering. |
| **Asset streaming / loading** | `IoDispatcher`, `FAsyncLoadingThread`, or similar I/O threads activating; `DeviceAllocation` / `VidMmMakeResident` bursts in ETW; copy engine activity spike. |
| **Main thread heavy work** | Render thread switches from bursty (short on-CPU runs with waits) to continuous on-CPU during the stutter frame. Callstacks reveal the subsystem (scene traversal, physics, script). |
| **Thread contention / lock convoy** | Multiple threads alternating between blocked and running on the same lock; elevated `WaitForSingleObjectEx` or `SRWLock` in callstacks. |
| **Scene complexity spike** | GPU workload per frame increases (longer GPU frame time) causing the CPU to wait longer at the present fence or swap chain. |

### GPU / driver

| Cause | What to look for |
|---|---|
| **GPU starvation** | GR Active drops to near-zero during the stutter while CPU is late submitting work -- cause is CPU-side. Decompose the stutter excess into excess-idle vs excess-busy against the clean-reference baseline (see [GPU idle decomposition](#cpu-bound-vs-gpu-bound-gpu-idle-decomposition)): when excess idle dominates the frame is CPU-bound and you must name the submit-path blocker, confirm GPU-context contention, or conclude unattributed. GPU idle is a symptom, never the magnitude-match cause. |
| **GPU context contention** | The 3D-engine "idle" gap is actually filled by another GPU context. Map the competing context to its owning process (`WDDM_QUEUE_PACKET_START_EVENTS` -> submitting `globalTid` -> `PROCESSES`) and name the originating app (compositor, overlay, capture tool, second app). Maps to `gpu_context_contention`. |
| **VRAM pressure / paging** | `WDDM_EVICT_ALLOCATION_EVENTS`, paging queue packet spikes, copy engine bursts concurrent with GR Active drop. |
| **Clock frequency drop** | GPU or memory clocks drop during the stutter window (thermal throttle, power limit, PState change). |
| **WDDM present queue / flip scheduling** | Display flips are late or missed despite GPU delivering frames on time -- see [display_pipeline_windows.md](display_pipeline_windows.md). |

### OS / system

| Cause | What to look for |
|---|---|
| **DPC / ISR interference** | Long DPCs or ISRs on the core running the game's render thread (see [windows_kernel_scheduling.md](windows_kernel_scheduling.md)). Visible in NSYS or ETL DPC/ISR events. |
| **Core contention from other processes** | Another process (antivirus, overlay, telemetry) scheduled on the same core as the render thread during the stutter. Check `SCHED_EVENTS` for other PIDs on the affected core. |
| **NUMA / CCX / CCD migration** | Thread migrates across NUMA nodes or AMD CCX/CCD boundaries, incurring a cache-cold penalty. Check core ID changes in scheduling events. |
| **Power management** | CPU core enters a deep C-state and takes too long to wake; or P-state transitions cause a frequency dip. More common on laptops and power-save profiles. |
| **Disk I/O stall** | Blocking file I/O on the render thread (rare but catastrophic). Requires OS runtime tracing (`--trace osrt` in NSYS) to confirm. |
| **Memory commit / page fault storm** | Large allocation or working-set growth triggers hard page faults. Check `VirtualAlloc` / `NtAllocateVirtualMemory` in callstacks and page fault ETW events. |

### DLSS Frame Generation

When FG is active, CPU-present stutter counts are inflated. Key points:

- **Always confirm FG is actually active** before attributing stutter inflation to it. Streamline modules load regardless of in-game setting.

For the module/thread table, the two implementation versions, and the full "loaded is not active" verification procedure, see [streamline_detection.md](streamline_detection.md). Flip metering is display-side and is **not** a CPU-side stutter cause -- do not attribute a CPU-bound or starved frame to a "missed flip cycle".

## Controlled mechanism tags

A finding attributes the stutter to exactly one tag from this controlled set. The machine-readable form of the vocabulary lives in `domain_semantics.py`; this table is the human-readable meaning and the key evidence each tag requires. Emit `unknown` when the report lacks the evidence a specific tag needs -- never guess a tag.

| Tag | Meaning | Key evidence required |
|---|---|---|
| `pso_compile_stall` | Runtime PSO / shader compilation stall | `AsyncPsoQueue` / precompile threads continuously on-CPU across the long frames; absent in clean windows |
| `sim_thread_cpu_overrun` | Simulation/main thread CPU-bound during the stutter | Thread on-CPU for ~the full frame delta (ms-level magnitude match), not blocked |
| `sim_thread_lock_contention` | Thread blocked on a kernel lock (convoy) | `SCHED_EVENTS` block reason `Resource`; alternating blocked/running threads on one lock |
| `sim_thread_fence_wait` | Thread blocked waiting on a fence/present (GPU not done, or submit serialized) | Block reason `UserRequest` at a fence/present; wall-clock >> on-CPU on that thread |
| `paging_burst_makeresident` | Bulk residency / page-in burst (resource creation, streaming, scene load) | `VidMmMakeResident` / `MakeResident` + page-table ETW burst, 5-10x clean baseline, concurrent with the gap |
| `directstorage_decompress_stall` | DirectStorage decompression stalling the pipeline | DirectStorage worker / decompress activity concurrent with the stutter; copy-engine spike |
| `display_flip_scheduling_miss` | Flip scheduled late/missed despite GPU delivering on time | Flip-to-flip gap with GPU present on time; missed-flip 2x-multiple pattern |
| `vrr_settle` | VRR range/settle transition cadence artifact | Flip cadence transition at a VRR range boundary; not a CPU/GPU work spike |
| `gpu_workload_spike` | GPU work per frame spikes (scene complexity) | GPU_METRICS GR/SM Active elevated during the long frame (the only valid GPU-bound basis) |
| `gpu_context_contention` | The game's GPU context is starved because another context is running on the GPU during the long frame | Game packets stall while GR Active stays high; competing context mapped to its owning process (compositor, overlay, capture tool, second app) |
| `cpu_thread_oversubscription` | More busy threads than cores; render thread preempted | Other PIDs/threads on the render thread's core; block reason `NonBlocked` (preempted) |
| `dxgkrnl_profiler_overhead` | DxgKrnl Profiler ETW capture overhead inflating the trace | DxgKrnl Profiler events (etwEventId 105/106) correlating with the apparent stutter |
| `memory_transfer_burst` | DMA / copy-engine transfer burst stalling the pipeline | WDDM DMA packet burst concurrent with the gap (see [memory-transfer](../glossary/graphics-glossary/memory-transfer.md)) |
| `unknown` | Evidence insufficient to attribute a specific mechanism | Use whenever the required evidence above is absent |

A single-threaded submission path (all D3D12 submission funneled through one thread) is a structural finding, not a tag on its own: name the actual wait it exposes (usually `sim_thread_fence_wait` or `gpu_workload_spike`).

## Stating the conclusion (hedged)

Conclude with a suspected cause, not a proof. Stay within the report-analysis evidence rules: hedge the claim, cite the data (table, thread + TID, time window, magnitude in ms), and never state a single-report cause as proven.
- Good: "the load-time spikes are likely shader compilation (`pso_compile_stall`): the AsyncPsoQueue thread is continuously on-CPU across the long frames [INFERRED from SCHED_EVENTS]; the steady-state floor shows none of that activity, so it is a separate question."
- Avoid: "the cause is X", "this proves X", "the fix is X". Offer remedies as options. If init and steady-state have different causes, report them separately. Honest uncertainty beats a forced single root cause.

## Related

- Investigation procedure (drill ladder, convergence gate, provenance tags): [investigation_methodology](../curated/investigation_methodology.md).
- SQLite schema, `SCHED_EVENTS`, block reasons, `globalTid`: [sql_query_tips.md](sql_query_tips.md).
- Windows present path, ETW flip events, VRR / flip-metering: [display_pipeline_windows.md](display_pipeline_windows.md).
- DPCs, GPU interrupt affinity, WDDM queue serialization: [windows_kernel_scheduling.md](windows_kernel_scheduling.md).
- Glossary: [stutter](../glossary/graphics-glossary/stutter.md), [pso](../glossary/graphics-glossary/pso.md), [fence](../glossary/graphics-glossary/fence.md), [present-mode](../glossary/graphics-glossary/present-mode.md), [fps-frame-time](../glossary/graphics-glossary/fps-frame-time.md).
