# Nsight Systems product overview

> Curated overlay: release-reviewed synthesis. Source inputs: QuadD/Docs/Rst/index.rst; QuadD/Docs/Rst/UserGuide; Installed nsys --version recorded in indexes/source_manifest.json at build time. Official generated docs, live CLI/recipe help, and report-tool evidence remain authoritative when facts differ.




NVIDIA Nsight Systems is a system-wide performance analysis tool. It combines statistical CPU sampling with timeline tracing so users can correlate CPU work, GPU work, OS runtime activity, CUDA API calls, graphics APIs, NVTX ranges, MPI, NCCL, and other events depending on platform and trace settings.

Use it to find bottlenecks across the whole application, such as launch overhead, CPU-GPU serialization, GPU gaps, pipeline bubbles, thread stalls, I/O delays, and multi-process or multi-rank imbalance.

Nsight Systems is different from Nsight Compute. Nsight Systems explains where time goes across the application timeline. Nsight Compute provides deeper per-kernel analysis after a kernel has been identified.

## Nsight tool boundaries

Use Nsight Systems evidence for timeline-level questions: which phases are expensive, which kernels or CUDA APIs dominate time, where CPU/GPU gaps appear, how NVTX/MPI/NCCL activity lines up, and which kernels are good candidates for deeper inspection.

Use Nsight Compute for kernel-level counter questions such as Speed Of Light sections, occupancy, register pressure, SASS/source correlation, roofline charts, replay modes, warp/PM sampling, or metric names such as `gpc__cycles_elapsed.max`. The Nsight Systems skill can identify candidate kernels and handoff metadata from an `.nsys-rep`, but it should not explain detailed Nsight Compute metric semantics or claim Nsight Compute counter values unless an Nsight Compute reference/tool has provided that evidence.
