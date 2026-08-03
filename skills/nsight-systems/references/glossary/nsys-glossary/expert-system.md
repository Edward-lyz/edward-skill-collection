# Expert system

**Short:** Rule-based analyzer behind ``nsys analyze``. Queries the SQLite export, finds known performance anti-patterns, and prints a short advice summary plus the top 50 offenders per rule.

**Details:**

- CUDA synchronization rules: ``cuda_memcpy_async`` (async memcpy on pageable memory; fix: pinned memory), ``cuda_memcpy_sync`` (synchronous memcpy; fix: ``cudaMemcpy*Async``), ``cuda_memset_sync`` (synchronous memset; fix: ``cudaMemset*Async``), ``cuda_api_sync`` (host-blocking sync APIs; fix: prefer stream-ordered synchronization — use ``cudaStreamWaitEvent`` together with events recorded via ``cudaEventRecord`` to coordinate device-side waits between streams, and avoid host-blocking ``cudaEventSynchronize`` in performance-critical paths).
- GPU utilization rules: ``gpu_gaps`` (a.k.a. GPU Starvation — idle regions over a threshold, default 500 ms, profiler-overhead gaps excluded) and ``gpu_time_util`` (a.k.a. GPU Low Utilization — time-chunks below a utilization threshold; time-based, not resource-based).
- Graphics rule: ``dx12_mem_ops`` flags problematic DX12 memory operations.
- ``nsys analyze`` auto-generates the SQLite export from the ``.nsys-rep`` if one isn't already present.
- Most rules also exist as ``nsys recipe`` scripts of the same name, often with extended behavior or multi-report support.

**See also:**

- [Recipe](recipe.md)
- [SQLite export](sqlite-export.md)
- *Recipe output keywords* (Summary / Trace / Pace / Heatmap / Histogram / Expert System / Stats System) — see the keywords table in [Rst/AnalysisGuide/topics/available-recipes.md](https://docs.nvidia.com/nsight-systems/AnalysisGuide/)
