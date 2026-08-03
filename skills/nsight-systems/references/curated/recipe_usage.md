# Recipe usage guidance

> Curated overlay: release-reviewed synthesis. Source inputs: NSYS_PATH/python/packages/nsys_recipe; live nsys recipe --help from build/validation nsys binary. Official generated docs, live CLI/recipe help, and report-tool evidence remain authoritative when facts differ.

Recipes are post-processing workflows that summarize or transform Nsight Systems report data. Recipe names and options must be discovered from the installed Nsight Systems recipe tree when available.

Use recipes when the user asks for a supported summary such as CUDA API time, GPU utilization, GPU gaps, MPI/NCCL overlap, network traffic, or statistics diffs.

Do not guess recipe options. Check live recipe help or generated recipe references before naming an option.

## CUDA bottleneck first-pass workflow




For a first-pass CUDA application bottleneck review, use both CPU-side API and GPU-side kernel evidence:

- `cuda_api_sum` summarizes CUDA Runtime API calls. Use it to identify expensive or high-count API calls such as graph launches, synchronization calls, allocation/free calls, and other CPU-side overhead.
- `cuda_gpu_kern_sum` summarizes CUDA kernel durations. Use it to identify slow kernels or whether very little GPU kernel work was captured.

When a report is loaded, combine recipe recommendations with measured report facts or bounded SQL. Distinguish total API time, mean per-call API time, and longest single API call; those can point to different candidates.
