# Investigation methodology

> Curated overlay: release-reviewed synthesis. Source inputs: QuadD/Docs/Rst/AnalysisGuide; Reviewed Nsight Systems trace-investigation methodology. Official generated docs, live CLI/recipe help, and report-tool evidence remain authoritative when facts differ.




This reference gives the investigation approach for Nsight Systems traces. It explains how to start from a reported symptom, use report data to check what happened, compare event sizes and timings, and stop when the evidence is strong enough to answer. It is guidance only. Exact facts must come from loaded report data, live `nsys` help, installed recipe metadata, or generated docs. Packaged scripts control what the agent may read, query, or run.

## Provenance tagging



Base every finding on queried data and cite the source: table name, column, thread, metric, and time window, with enough detail for a reader to reproduce the query.

Do not label plain observations. "RenderThread ran for 37ms" is self-evidently observed from query data and needs no tag.

Do label causal and explanatory claims, because that is where hallucinations hide:

- `[INFERRED]` -- a conclusion derived from data but not directly stated. Use on every "therefore", "because", "this caused", or "this explains" claim.
- `[KB: id]` -- domain knowledge from a knowledge-base document driving your interpretation, for example `[KB: windows_kernel_scheduling]`.
- `[MODEL KNOWLEDGE]` -- explanation from training knowledge that is not verifiable in this trace. It lowers confidence. Use it when you explain why a mechanism works, for example "DxgKrnl serialises GPU context switches [MODEL KNOWLEDGE]".
- `[ESTIMATED]` -- a value calculated from incomplete data; state the inputs and the uncertainty.

The goal is to distinguish "we saw X" (no tag) from "we believe X causes Y because..." (needs `[INFERRED]`) and "X behaves this way because of how the OS works" (needs `[KB:]` or `[MODEL KNOWLEDGE]`). For critical derived values, track lineage from raw source through transformations to the value you cite.

## Top-down investigation



Work from symptoms to causes, never the reverse.

1. **Classify** -- establish severity. Quote exact values from data.
2. **Locate** -- find where in the trace the problem occurs. Use the analysis window(s); widen only when the comparison requires it.
3. **Scan** -- before forming hypotheses, do a broad differential scan across all available dimensions. Surface all changed signals, not just the first one found.
4. **Hypothesize** -- form two or three candidate causes from the scan results. Use domain knowledge to guide queries, not as evidence.
5. **Verify** -- query data to test each hypothesis. Run at least one disconfirming check per hypothesis. Compare against a clean reference window of equal duration when one is available.
6. **Converge** -- build the full causal chain: trigger event -> mechanism -> pipeline effect -> user-visible symptom. Every link must be data-supported or explicitly labeled.

## Recursive "why?" and mandatory drill depth



Every observation invites the question "why?" Each answer becomes the next question. Follow the chain until you reach either a **generator** you can name (a specific function, lock holder, wait target, data-driven input change, or OS scheduling decision) or the **trace data limit** (unresolved symbols, missing CPU samples, no GPU metrics).

Stopping at an intermediate layer is not acceptable. "VRAM events elevated", "paging burst detected", and "thread X has a high scheduling rate" are symptoms, not causes. Keep drilling.

The why-chain passes through these layers:

| Layer | Type | Example | Acceptable to stop here? |
|---|---|---|---|
| 0 | Symptom | "Frame 101 is 110ms (7x baseline)" | No |
| 1 | Phase | "Simulation marker is 95ms of 110ms" | No |
| 2 | Activity | "GameThread continuously on-CPU, no blocking waits" | No |
| 3 | Evidence | "Scheduling callstacks show module X at 70%; block reason NonBlocked/Running" | No -- keep going |
| 4 | Mechanism | "30 worker threads saturate 32 cores, preempting GameThread ~100 times in 5ms" | Yes -- if data exhausted |
| 5 | Generator | "Thread pool sized to core count without reserving main-thread capacity" | Yes -- ideal stopping point |

Minimum depth is Layer 3: reach at least Layer 3 before treating anything as a finding. Layer 4 or deeper is the target.

Investigation notes should track drill depth explicitly so it is obvious when you are not yet ready to conclude:

```text
### Current Drill Depth
Layer 2 -> Activity: TID 18772 has 83K sched-outs at 16.7/ms
Next question: What IS TID 18772? What process owns it? What's it doing?
Queries needed: thread name lookup, callstack samples for TID 18772
```

Update this every turn. If you are at Layer 0-2, you are not ready to conclude; keep querying.

## Drill-down checklist for every lead signal



When you find an elevated signal, drill through all of these before moving on. Adapt your queries to the available tables: check the report's available tables and table schemas first.

1. **Which thread?** Use per-thread on-CPU time (scheduling events) or per-thread event counts to find which thread(s) own the activity. Use `report-fact --intent thread_scheduling` (add `--frame <N>` to scope to a frame) for per-thread on-CPU vs blocked time with the global thread id already decoded and thread names resolved, rather than hand-writing the `SCHED_EVENTS`/`ThreadNames` joins.

2. **What is that thread doing?** Use whichever data source exists in the trace:
   - CUDA API tables: which runtime/driver calls are longest for that thread?
   - Graphics API calls (DX12/Vulkan/OpenGL): which calls dominate? Use `report-fact --intent graphics_api_summary` (add `--frame <N>` to scope to a frame) rather than hand-writing SQL; `--intent graphics_api_timeline --metric <api_name>` shows back-to-back serialized calls.
   - Sampling callchains: which modules/functions dominate the leaf frames? Use `report-fact --intent callstack_summary --metric <globalTid>` (the `globalTid` from `thread_scheduling`) for leaf-symbol hotspots and the blocked-stacks that name the call a thread parked in.
   - GPU metrics: is the GPU busy or starved (GR Active %, SM Active %)?
   - NVTX ranges: which game/application phase is extended?
   - ETW events: paging, shader compilation, or device events?
   - Scheduling block reasons: is the thread running (NonBlocked), waiting on a resource, or voluntarily blocked (UserRequest)? The `dominant_block_reason` from `thread_scheduling` reports this per thread.

3. **Which thread is blocked?** Find the thread that stalls. Compare its on-CPU and blocked-time upper bounds in your window against the clean reference with `report-fact --intent thread_scheduling`. Treat each `*_confirmed_pct` as confidence in that upper bound: near 100% means the value is backed by observed sched-in/sched-out pairs, while a low value means missing transitions inflated the bound. Read its top block reasons and `OSRT_API` blocking waits, then attribute the stall with `report-fact --intent callstack_summary --metric <globalTid>`.

4. **Per-call or per-count scaling?** Compare the per-event average duration between your window and the clean reference. If per-call duration scales with concurrency, suspect a serialised resource. If it is flat, the cost is volume-driven.

5. **What triggers it?** Trace backward from the effect to the initiator. Candidates include a blocking API call, a synchronous shader compilation, a VRAM paging burst, a CPU overrun, GPU-bound work, or an external process visible in scheduling events.

6. **Magnitude match in milliseconds.** Find the specific blocked-thread duration and compare it to the effect delta. Event counts and rates are not magnitude matches; you need a duration from API call intervals, scheduling on/off-CPU intervals, or NVTX marker durations.

## Convergence checks before concluding



All of these must hold before treating a finding as complete:

- **Magnitude match in milliseconds** -- a thread-level duration, not event counts. For example "GameThread on-CPU 57.2ms / 56.8ms frame delta = 100.7%".
- **Temporal ordering** -- the cause must start before the effect. State timestamps.
- **Entity attribution** -- name the specific thread (name and TID) and what it is doing (API call, module from callstack, scheduling state).
- **Drill past the symptom** -- GPU idle, paging bursts, fence waits, and elevated scheduling rates are consequences. Trace backward to the operation that initiated them.
- **Generator identified** -- name an operation a developer can change, such as "PhysX cooking on GameThread during the frame" or "synchronous shader compilation on the render path".

You do not need to reach Layer 5 (callstacks and function names) to conclude. With a magnitude match plus entity plus mechanism at Layer 3-4, conclude now and document what deeper data would add. A good Layer 3-4 finding with honest uncertainty is far more useful than an incomplete investigation.

## Scientific rigour, units, and integrity



State the sample size and flag `N=1`. Consider alternatives; correlation does not equal causation. A cause that explains more than 50% of the effect delta is high confidence, less than 25% is a "contributing factor". Bounds-check that a part does not exceed the whole, and validate data quality against a clean reference where one exists.

Report frame time in ms and FPS, durations in ms and percent of frame, and normalise to per-second rates when comparing windows of different duration. Avoid superlatives; state the value and the ratio.

Data integrity is non-negotiable: never fabricate values, verify that source names exist before citing them, cite explicit window boundaries for windowed comparisons, and verify arithmetic so breakdowns sum to their total.

A single performance problem often has a primary cause and exacerbating factors. Decompose it: state the primary cause, then separately quantify each exacerbating factor. Remember that GPU idle, paging bursts, and fence waits during a slow window are usually consequences, so trace backward to find the initiator.
