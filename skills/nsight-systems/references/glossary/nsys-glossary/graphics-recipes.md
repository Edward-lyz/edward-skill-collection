# Graphics-focused recipes

**Short:** Catalog of ``nsys recipe`` analyses most useful for graphics performance investigation — frame spikes, VRAM exhaustion, GPU idleness, DX12 / Vulkan memory churn.

All run via ``nsys recipe <name> --input <report.nsys-rep>``; see ``--help`` per recipe for parameters.

## gfx_hotspot — Graphics Hotspot Analysis

Web-app frame-comparison view for graphics apps. Selects "interesting" frames by four strategies (Slow Frames / Periodic / Bar1 Reads / GR Idle), then lets you compare two of them side-by-side: frame info, performance-issue indicators, GPU metrics, ETW / DxgKrnl breakdown, per-thread CPU utilization, sampled call stacks (merged or chronological), modules, DX12 / Vulkan API breakdown, known problematic symbols (e.g. ``CreateCommittedResource``), and PIX markers. Best with resolved symbols. View with ``--run-viewer --show-viewer`` or re-launch later via ``run_viewer.py``.

## gpu_vram_usage_trace — GPU VRAM Usage Trace (preview)

Per-frame VRAM and SYSMEM usage / commitment / budget, resource migrations between VRAM↔SYSMEM, allocation / deallocation timing, and dual-frame comparison. Targeted at VRAM exhaustion, memory thrashing, and frame spikes caused by residency churn. **Windows only**, DX12 or Vulkan. Requires WDDM trace: ``--trace=wddm`` with ``--wddm-memory-trace=true`` (or ``--wddm-additional-events=true``). Optionally add ``dx12-annotations`` / ``vulkan-annotations`` to get resource debug names. Output is an interactive Jupyter notebook (``stats.ipynb``) with global process / GPU selectors, synchronized timeline charts, resident-resources diff tables, per-resource details (callstacks + perf markers), and an all-allocations table. **Single report only.**

## dx12_mem_ops — DX12 Memory Operations

Flags problematic DX12 memory operations with warnings (Trace / Expert-System recipe). Pairs well with ``gpu_vram_usage_trace`` when investigating VRAM / residency issues.

## gpu_gaps — GPU Gaps

Identifies GPU idle regions longer than a threshold. Excludes profiler-overhead gaps and leading / trailing gaps. Same logic as the ``gpu_gaps`` / GPU Starvation expert-system rule.

## gpu_time_util — GPU Time Utilization

Identifies time chunks of low GPU utilization (time-based; doesn't account for resource utilization, so one memcpy counts as much as a huge kernel).

## cuda_gpu_time_util_map — GPU Time Utilization Heatmap

Heatmap of % time CUDA kernels were running.

## gpu_metric_util_map — GPU Metric Utilization Heatmap

Heatmap of GPU counter utilization (SM Active, SM Issue, Tensor Active) over time. Requires GPU metrics collection.

## gpu_metric_util_sum — GPU Metrics Utilization Summary

Summary of different GPU metrics across the run. Based on binary inclusion — ranges without at least one sampling point are excluded from the output. Requires GPU metrics collection.

**See also:**

- [Recipe](recipe.md)
- [Expert system](expert-system.md)
- [Export tables](export-tables.md)
- *Recipe output keywords* (Summary / Trace / Pace / Heatmap / Histogram / Expert System / Stats System) — see the keywords table in [Rst/AnalysisGuide/topics/available-recipes.md](https://docs.nvidia.com/nsight-systems/AnalysisGuide/)
