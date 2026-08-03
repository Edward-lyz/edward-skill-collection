# NSYS SQL Schema




Structural reference for the SQLite database produced by ``nsys export``: timestamp semantics, ID encoding, ``SCHED_EVENTS`` and ``ENUM`` table shapes, the ``cpuCycles`` distinction, and ready-to-use query patterns. Pair with the SQLite Schema Pitfalls in ``Rst/AnalysisGuide/topics/sqlite-schema-pitfalls.rst`` for the gotchas, attribution rules, and anti-patterns.

Always discover tables and columns from the live file -- do not assume their presence. Schema is discovered on demand, not handed to you up front:

- call ``nsys_skill_cli report-describe`` to get a table's columns.
- ```nsys_skill_cli report-query`` accepts only ``SELECT`` / ``WITH`` (``DESCRIBE`` and ``PRAGMA`` are rejected), and ``nsys_skill_cli report-context`` lists table names and row counts but **not** columns. Get a table's columns with ``nsys_skill_cli report-query --sql "SELECT * FROM <TABLE> LIMIT 1"`` and read the returned ``columns`` list -- once per table you need, not one probe per round-trip. For the common Windows graphics tables, use the quick schema under "Key query patterns" below and skip it entirely.

For the catalog of tables and what each one represents, see ``glossary/nsys-glossary/export-tables.md``.

## Timestamp model

All event timestamps are **trace-relative nanoseconds** where 0 = trace start. ``ANALYSIS_DETAILS.duration`` (or the ``TraceDurationInNs`` key on schemas that store details as key/value) gives the valid capture length in ns. Valid analysis window is ``[0, duration]``.

- Events with **negative timestamps** are pre-capture warm-up -- exclude them.
- For report time axes: ``t = timestamp_ns / 1e9`` (seconds from trace start).

```sql
-- Apply to all time-based queries.
-- COALESCE handles all known ANALYSIS_DETAILS layouts: a ``duration``
-- column, a ``TraceDurationInNs`` column, or a key/value row with
-- ``key='TraceDurationInNs'``. Drop the branches that don't match your
-- schema if the unused columns don't exist.
WHERE e.timestamp >= 0
  AND e.timestamp <= COALESCE(
      (SELECT duration FROM ANALYSIS_DETAILS),
      (SELECT TraceDurationInNs FROM ANALYSIS_DETAILS),
      (SELECT CAST(value AS INTEGER) FROM ANALYSIS_DETAILS WHERE key = 'TraceDurationInNs')
  )
```

## globalTid / globalPid encoding

``globalTid`` and ``globalPid`` are NSYS composite IDs -- **not** raw OS PIDs/TIDs.

```text
globalTid = (internal_process_id << 24) | os_tid
```

```sql
(globalTid & 0xFFFFFF) as tid          -- extract OS thread ID
(globalTid >> 24)      as process_id   -- extract internal process identifier
```

Thread names come from ``ThreadNames`` joined to ``StringIds``; process names from ``PROCESSES``.

## SCHED_EVENTS structure

- Columns: ``start``, ``cpu``, ``isSchedIn``, ``globalTid``, ``threadState``, ``threadBlock``.
- ``isSchedIn = 1`` means scheduled **onto** a CPU (starts running). ``isSchedIn = 0`` means scheduled **off** (stops running).
- ``threadBlock`` is meaningful only on ``isSchedIn = 0`` events. Join to ``ENUM_SCHEDULING_THREAD_BLOCK`` for the reason name.

#### Block-reason + thread-state combinations

The (block reason, thread state) pair on an ``isSchedIn = 0`` event tells you why the thread came off CPU:

| Block reason | Thread state | What happened | Investigation direction |
|---|---|---|---|
| ``NonBlocked`` | ``Running`` | Quantum expiry or scheduler preemption. The thread was actively running and the OS descheduled it. | Check who else is running. Count threads competing for cores. Rapid migration across many cores = thread-pool oversubscription. |
| ``Preempted`` | ``Running`` | Explicit preemption by a higher-priority thread (DPC, interrupt handler, real-time priority). | Identify the preempting thread/DPC on the same core at the same timestamp. |
| ``UserRequest`` | ``Waiting`` | Voluntary wait (WaitForSingleObject, Sleep, ...). | Identify what it's waiting on. Check OSRT_API for the wait call. |
| ``Resource`` | ``Waiting`` | Kernel-resource contention (spinlock, pushlock, critical section inside the kernel). | Identify which kernel subsystem (VidMm, DxgKrnl) from the callstack. |
| ``Executive`` | ``Waiting`` | Kernel I/O or driver wait. | Check disk I/O, network, driver completion. |
| ``KeyedEvent`` | ``Waiting`` | SRWLOCK or condition variable. | Look for convoy patterns. |
| ``DelayExecution`` | ``Waiting`` | Voluntary sleep. | Usually intentional throttling. |
| ``YieldExecution`` | ``Running`` | Thread called SwitchToThread / yielded. | Check if spin-waiting in a loop. |

See the SQLite Schema Pitfalls in ``Rst/AnalysisGuide/topics/sqlite-schema-pitfalls.rst`` for the attribution rule on this pair (in short: ``NonBlocked``/``Running`` is not lock contention).

## ENUM tables

All ``ENUM_*`` tables have columns ``id``, ``name``, ``label``. Join on ``id``; filter or display by ``name``:

```sql
JOIN ENUM_SCHEDULING_THREAD_BLOCK b ON se.threadBlock = b.id
WHERE b.name = 'Resource'
```

## COMPOSITE_EVENTS / SAMPLING_CALLCHAINS / cpuCycles

``COMPOSITE_EVENTS.cpuCycles`` distinguishes two fundamentally different callstack types:

| ``cpuCycles`` | Type | Use for |
|---|---|---|
| **1** | Periodic CPU sample (PMU timer) | Time attribution and hotspot identification -- statistically representative; more samples = more time spent. |
| **0** | Event callstack (scheduling event) | Thread state transitions, wake/block reasons -- NOT representative of time spent. |

Hotspot query (periodic samples only):

```sql
SELECT s.value as symbol, COUNT(*) as samples
FROM SAMPLING_CALLCHAINS sc
JOIN COMPOSITE_EVENTS ce ON sc.id = ce.id
JOIN StringIds s ON sc.symbolId = s.id
WHERE ce.globalTid = <target_globalTid>
  AND ce.cpuCycles = 1
  AND sc.depth = 0
  AND ce.start BETWEEN <start_ns> AND <end_ns>
GROUP BY s.value ORDER BY samples DESC
```

See the SQLite Schema Pitfalls in ``Rst/AnalysisGuide/topics/sqlite-schema-pitfalls.rst`` for the missing-CPU-samples caveat and the rule against mixing the two stack types.

## Key query patterns

#### Per-thread on-CPU time in a window

```sql
WITH runs AS (
    SELECT globalTid, start, isSchedIn,
           LEAD(start) OVER (PARTITION BY globalTid ORDER BY start) as next_start,
           LEAD(isSchedIn) OVER (PARTITION BY globalTid ORDER BY start) as next_sched
    FROM SCHED_EVENTS
    WHERE start BETWEEN <window_start_ns> AND <window_end_ns>
)
SELECT (globalTid & 0xFFFFFF) as tid,
       ROUND(SUM(next_start - start) / 1e6, 2) as on_cpu_ms
FROM runs WHERE isSchedIn = 1 AND next_sched = 0
GROUP BY globalTid ORDER BY on_cpu_ms DESC LIMIT 20
```

(Also available as the named query ``thread_cpu_time``.)

This pattern needs ``isSchedIn = 1`` (sched-in) events, which are **often absent on Windows CPU-sampling
traces** -- NSYS frequently captures only sched-out events for game threads, so the query returns 0 rows.
That is a structural trace limitation, not an idle thread: do not retry it. First confirm with
``SELECT COUNT(*) FROM SCHED_EVENTS WHERE isSchedIn = 1 AND start >= 0``; if that is 0, use sched-out
count as a CPU-activity proxy instead (or ``COMPOSITE_EVENTS`` periodic samples when ``HasCpuCycles`` is set):

```sql
SELECT s.value AS thread_name, (se.globalTid & 0xFFFFFF) AS tid, COUNT(*) AS sched_out_count
FROM SCHED_EVENTS se
JOIN ThreadNames tn ON tn.globalTid = se.globalTid
JOIN StringIds s ON tn.nameId = s.id
WHERE se.start BETWEEN <start_ns> AND <end_ns> AND se.isSchedIn = 0
GROUP BY se.globalTid ORDER BY sched_out_count DESC LIMIT 20
```

#### Long off-CPU (blocked) periods for a thread

```sql
WITH sched AS (
    SELECT start, isSchedIn,
           LEAD(start) OVER (ORDER BY start) as next_start,
           LEAD(isSchedIn) OVER (ORDER BY start) as next_sched
    FROM SCHED_EVENTS WHERE globalTid = <target_globalTid>
)
SELECT ROUND((next_start - start) / 1e6, 2) as blocked_ms, start
FROM sched WHERE isSchedIn = 0 AND next_sched = 1
ORDER BY blocked_ms DESC LIMIT 20
```

#### Event type counts in a window (ETW)

```sql
SELECT s.value as event_type, COUNT(*) as count
FROM ETW_EVENTS e
JOIN GENERIC_EVENT_TYPES gt ON e.typeId = gt.typeId
JOIN StringIds s ON gt.nameId = s.id
WHERE e.timestamp BETWEEN <start_ns> AND <end_ns>
GROUP BY s.value ORDER BY count DESC
```

## See also

- [SQLite Schema Pitfalls](https://docs.nvidia.com/nsight-systems/AnalysisGuide/) -- gotchas, attribution rules, and anti-patterns for the same tables.
- [glossary/nsys-glossary/export-tables.md](../glossary/nsys-glossary/export-tables.md) -- catalog of every SQLite / Parquet table produced by ``nsys export``.
