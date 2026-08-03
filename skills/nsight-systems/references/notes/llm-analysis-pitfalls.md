# LLM Analysis Pitfalls





These pitfalls concern how an automated analysis agent (LLM) reports findings and conducts an investigation -- terminology discipline, citation accuracy, and knowing when to keep digging.

## Timing and measurement

### "Slow region" is ambiguous -- frame rate and scene complexity are inversely related

- **Wrong**: "The ~35 FPS region is slow, suggesting CPU bottleneck."
- **Correct**: Low FPS means **high** scene complexity (more work per frame). High FPS means low complexity. "Slow" without qualification is ambiguous. Always label regions by workload characteristic first: "heavy workload region (~35 FPS)", "high scene complexity (~35 FPS)".

### GPU time is not wall-clock for overlapped work

- **Wrong**: "Pass A takes 5 ms and Pass B takes 3 ms, so together they take 8 ms."
- **Correct**: If passes overlap (e.g. async compute running alongside graphics), their wall-clock contribution is max(A, B) or some overlap, not A + B. Always check whether work overlaps on the GPU timeline before summing individual pass durations.

## Table and source citations

### Cite the actual table, not a plausible-sounding name

- **Wrong**: Citing `DXGI_API` or `DX12_API` as the source for a measurement when those tables aren't in the database for this capture.
- **Correct**: The set of SQLite tables present depends on what was collected during the capture. Before citing a table, verify it actually exists in the database (for example, run `.tables` in `sqlite3` or query `sqlite_master`).

### Symbol resolution is partial -- check the specific symbol, not the top-N

- **Wrong**: Querying the top 20 leaf symbols, seeing hex addresses for ntoskrnl.exe / ntdll.dll, and concluding "symbols are unresolved -- function name citations are invalid."
- **Correct**: Symbol resolution is **module-dependent**. Kernel symbols and some OS DLLs often remain as hex addresses because symbol servers weren't available. Meanwhile, the application binary, D3D12 / Vulkan runtimes, vendor UMDs, and many user-mode DLLs resolve successfully. Before concluding a cited function name is wrong, search for that specific name in `SAMPLING_CALLCHAINS` -> `StringIds`. Resolved and unresolved frames coexist in the same database.

## Investigation discipline

### A threshold gates severity, not investigation depth

- **Wrong**: "0 frames exceed the threshold. This is LOW severity / LOW opportunity. No further investigation is warranted."
- **Correct**: A threshold classifies severity -- it does not determine whether to investigate. Identifiable variance with concrete root causes (CoV >10%, P99 >1.3x median, visible tails or clusters) is always worth investigating because: (a) it may worsen under different conditions, (b) it affects input-sampling consistency, (c) the underlying causes (streaming, pipeline compilation, scheduling) are directly actionable by the developer. Stopping at "0 frames exceed threshold" leaves actionable findings on the table.

### A count of 0 samples is not a confirmation of inactivity

- **Wrong**: "0 CPU samples were found for thread X, confirming the thread was inactive."
- **Correct**: If periodic CPU-cycle sampling was not enabled for the capture, then such samples were not collected -- so a count of 0 samples may reflect absent data, not an idle thread. Any finding that cites "0 CPU samples for thread X" in that situation must be qualified, and inactivity must instead be established from `SCHED_EVENTS` behavioral signals. Module proportions across the available callstacks remain approximately valid for comparison; absolute sample counts are not.

## SQLite output and query directives

### globalTid presentation

**Always present decoded OS TID/PID in output**, never raw `globalTid` values. Write `"RenderThread (TID 10460)"` not `"globalTid 281728446910460"`. Use `(globalTid & 0xFFFFFF)` to decode.

### Anti-patterns

- **Never query a table without verifying it exists** in the database -- absent tables produce confusing errors, not empty results.
- **Never output raw** `globalTid` **values** -- always decode to OS TID with `(globalTid & 0xFFFFFF)`.
- **Never use** `startTime` **/** `stopTime` as event time references -- they are wall-clock, not trace-relative ns.
- **Never mix** `cpuCycles=0` **and** `cpuCycles=1` when counting samples for time attribution.
- **Always normalize to rates** when comparing windows of different duration -- a longer window accumulates more events at the same rate even if nothing changed.
- **Never reference an ENUM table's** `value` **column** -- the columns are `id`, `name`, `label`.
