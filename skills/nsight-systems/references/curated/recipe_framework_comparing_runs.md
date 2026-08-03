# Comparing Performance Across Runs

> Curated overlay: release-reviewed synthesis. Source inputs: QuadD/Docs/Rst/AnalysisGuide recipe and diff documentation; Installed nsys_recipe recipe metadata and README files; Installed nsys_recipe diff recipe implementation. Official generated docs, live CLI/recipe help, and report-tool evidence remain authoritative when facts differ.



## Overview




The `diff` recipe compares outputs from two runs of the same statistical recipe to identify performance regressions or improvements. It is the recommended way to do A/B testing, regression testing, and optimization validation.

## Recommended Workflow




### Step 1: Profile both runs

Collect Nsight Systems reports for the baseline and the comparison scenario:

```bash
nsys profile -o baseline.nsys-rep ./my_app --baseline-config
nsys profile -o optimized.nsys-rep ./my_app --optimized-config
```

### Step 2: Run the same statistical recipe on each

Choose a statistical (`_sum`) recipe and run it on both reports separately:

```bash
nsys recipe cuda_gpu_kern_sum --input baseline.nsys-rep --output baseline_stats
nsys recipe cuda_gpu_kern_sum --input optimized.nsys-rep --output optimized_stats
```

Both runs **must use the same recipe**, for example both `cuda_gpu_kern_sum` or both `nvtx_sum`.

### Step 3: Compare with diff

```bash
nsys recipe diff --input baseline_stats/ optimized_stats/ --csv
```

The diff recipe reads the statistical output from both directories and computes:
- **Absolute Diff**: Comparison − Baseline
- **Relative Diff %**: ((Comparison − Baseline) / Baseline) × 100
- **Status**: Improvement / Regression / No Change

## Compatible Recipes




Any `_sum` (statistical summary) recipe output works as input to `diff`:

`cuda_api_sum`, `cuda_gpu_kern_sum`, `cuda_gpu_mem_size_sum`, `cuda_gpu_mem_time_sum`, `mpi_sum`, `nccl_sum`, `nvtx_sum`, `osrt_sum`, `file_access_sum`, `network_sum`, `nvlink_sum`, `gpu_metric_util_sum`, `nccl_gpu_proj_sum`, and `nvtx_gpu_proj_sum`.

## Tips

- Use `--csv` to generate human-readable CSV output alongside parquet.
- For multi-rank MPI comparisons, run the same recipe on each rank's report directory, then diff the outputs.
- The diff recipe does not directly process `.nsys-rep` files: it works on recipe output directories.
