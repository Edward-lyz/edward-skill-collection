---
source_path: AnalysisGuide/topics/sqlite-schema-pitfalls.rst
title: ## SQLite Schema Pitfalls
---
## SQLite Schema Pitfalls

Common SQL traps and misinterpretations when querying the ``.sqlite`` database
produced by ``nsys export``. Read these alongside the sqlite-schema
(table columns, ID encoding, timestamps, and query patterns) and the GPU
performance analysis pitfalls above.

### Timestamp filtering

- ``startTime`` / ``stopTime`` in metadata are **wall-clock** times, **not** event-timestamp references -- never use them to filter events. Filter against the trace-relative ``timestamp`` column (in nanoseconds) instead. See the sqlite-schema for the timestamp model.

### SCHED_EVENTS gotchas

- **No** ``end`` **or** ``duration`` **column.** Compute on-CPU intervals with ``LEAD(start) OVER (PARTITION BY globalTid ORDER BY start)``.
- ``threadBlock`` is only meaningful when ``isSchedIn = 0``. Reading it on a sched-in event gives a stale value from the previous off-CPU transition.

#### Attribution rule (block reason vs thread state)

Interpret the (block reason, thread state) **pair**, not the block reason alone -- the value lists are in SQLite Schema Event Values. Before concluding lock contention, verify the stalled thread's ``threadBlock`` shows a blocking reason (``Resource``, ``UserRequest``, ``KeyedEvent``) during the specific window. ``NonBlocked`` / ``Running`` means the thread was actively computing and got preempted -- that is **not** lock contention.

### ENUM tables: do not use ``value``

All ``ENUM_*`` tables have columns ``id``, ``name``, ``label`` -- there is **no** ``value`` **column**. Filtering by ``b.value = '…'`` fails with a SQLite column error:


   -- Right
   JOIN ENUM_SCHEDULING_THREAD_BLOCK b ON se.threadBlock = b.id
   WHERE b.name = 'Resource'

   -- Wrong (no `value` column)
   JOIN ENUM_SCHEDULING_THREAD_BLOCK b ON se.threadBlock = b.id
   WHERE b.value = 'Resource'

### cpuCycles attribution

**Always filter** ``cpuCycles = 1`` when attributing CPU time.
``cpuCycles`` is the value of the ``CpuCycles`` PMU event carried by a composite event: a periodic CPU-cycle sample is tagged with value ``1``, and any callstack captured for another reason (a scheduling / context-switch transition) carries no such event and exports as ``0``.
This holds on both Linux and Windows. On Linux, only ``PERF_RECORD_SAMPLE`` records are stamped ``CpuCycles=1`` (context-switch records become ``SCHED_EVENTS``), and on Windows only single-frame stackwalks bearing a ``CpuCycles`` event count as samples (CSwitch / ReadyThread stackwalks do not).
Including ``cpuCycles = 0`` therefore distorts hotspot results by over-counting functions that coincide with frequent scheduling events. ``cpuCycles = 0`` callstacks are non-sample (scheduling-event) stacks -- they belong with scheduling-event analysis (wake / block reasons), not with hotspot identification. Equivalently, weight by ``SUM(cpuCycles)``, which counts non-samples as ``0`` (this is what the shipped flat / bottom-up views do).

#### No periodic CPU samples in the capture

If periodic CPU-cycle sampling was not enabled for the capture, then such samples will not be collected -- a count of 0 samples is then a data-absence artifact, **not** confirmation of inactivity.
