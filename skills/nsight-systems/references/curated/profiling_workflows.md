# Profiling workflow guidance

> Curated overlay: release-reviewed synthesis. Source inputs: QuadD/Docs/Rst/UserGuide; QuadD/Docs/Rst/AnalysisGuide; Installed nsys --help recorded indirectly through release validation. Official generated docs, live CLI/recipe help, and report-tool evidence remain authoritative when facts differ.

Use Nsight Systems first when the question is about where time goes across CPU threads, GPU work, CUDA API calls, NVTX ranges, MPI or NCCL behavior, I/O, or host-device serialization.

Use Nsight Compute after Nsight Systems has identified a kernel or kernel family that needs kernel-level analysis.

Good Nsight Systems questions include launch overhead, pipeline bubbles, GPU gaps, Python-side stalls, multi-rank imbalance, and CPU-GPU overlap.

For Nsight Compute handoff, keep the boundary clear: Nsight Systems can provide candidate kernel names, timing, report labels, GPU/context/stream metadata, and the surrounding NVTX or CUDA API context when those facts are present in the report. It cannot replace a kernel-counter profiler. Do not infer occupancy, register pressure, memory-pipe stalls, SASS/source behavior, or Nsight Compute metric meanings from an Nsight Systems trace alone.

## Multi-GPU and distributed profiling



Nsight Systems can profile applications that use multiple GPUs and report GPU activity by logical GPU/device in the timeline and exported report tables. When collecting sampled GPU metrics, choose the device-selection behavior with the installed `nsys profile` help; releases commonly expose a GPU-metrics device selection option such as `--gpu-metrics-devices`. Verify the exact values and defaults with live help for the user's installed build before giving a command.

For distributed or multi-rank workloads, collect one report per rank or selected rank when that matches the launcher/runtime workflow, then analyze the directory of `.nsys-rep` files with multi-report SQL or installed recipes. Per-rank conclusions should group by the report label/source, not collapse all reports into one unlabeled aggregate.

## Common collection workflows



Start with `nsys profile` for the common single-command workflow: it launches the target application, collects a focused trace, and writes a `.nsys-rep` report. Keep the first capture short and representative; add NVTX ranges when you can so later analysis maps back to application phases.

For controlled or interactive collection, use the `nsys launch` / `nsys start` / `nsys stop` workflow: launch the application under Nsight Systems control, start collection around the region of interest, then stop collection before finalizing the report. Verify exact command syntax and flags with live help for the installed version because capture-range, duration, delay, and output options can vary by release.

After collection, open the `.nsys-rep` in `nsys-ui` for timeline triage and use `nsys stats` or Advanced Analysis recipes for repeatable numerical summaries.
