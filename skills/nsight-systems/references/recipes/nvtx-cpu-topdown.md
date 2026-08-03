---
recipe: nvtx_cpu_topdown
display_name: CPU Topdown methodology metrics correlated to NVTX ranges
source: installed-nsys/python/packages/nsys_recipe
---

# nvtx_cpu_topdown: CPU Topdown methodology metrics correlated to NVTX ranges

## Live help at build time

```text
Per-recipe help is queried live at runtime with `nsys recipe <name> --help`.
```

## README

This recipe calculates CPU Topdown methodology metrics for NVTX 
push/pop ranges based on collected PMU core events for NVIDIA CPUs 
that feature Arm cores.

```yaml
moduleName: nvtx_cpu_topdown
displayName: CPU Topdown methodology metrics correlated to NVTX ranges
description: |-
  This recipe calculates CPU Topdown methodology metrics for NVTX  push/pop ranges based on collected PMU core events for NVIDIA CPUs  that feature Arm cores.
arguments:
- name: INPUT
  cliOption: --input
  type: process_input
  title: Input
  description: |-
    One or more paths to nsys-rep files or directories.
    Directories can optionally be followed by ':n' to limit the number of files.
  required: true
- name: MODE
  cliOption: --mode
  type:
  - unset
  - none
  - concurrent
  - dask-futures
  title: Mode
  description: |
    Recipe execution mode:
      - none: Sequential execution.
      - concurrent: Parallel execution.
      - dask-futures: Distributed execution.
  default: unset
- name: OUTPUT
  cliOption: --output
  type: process_output
  title: Output
  description: |-
    Output directory name.
    Any %q{ENV_VAR} pattern in the filename will be substituted with the value of the environment variable.
    Any %h pattern in the filename will be substituted with the hostname of the system.
    Any %p pattern in the filename will be substituted with the PID.
    Any %n pattern in the filename will be substituted with the minimal positive integer that is not already occupied.
    Any %% pattern in the filename will be substituted with %.
  group: Output
- name: FORCE_OVERWRITE
  cliOption: --force-overwrite
  type: flag
  default: false
  title: Force Overwrite
  description: Overwrite existing directory.
  group: Output
- name: EXPORT_DIR
  cliOption: --export-dir
  type: string
  title: Export Directory
  description: Directory where exported files will be saved.
  group: Output
- name: THREAD_NAME
  cliOption: --thread-name
  type: string
  title: Thread Name
  description: The name of the thread whose NVTX ranges will be analyzed.
  mutuallyExclusiveGroup: Thread
- name: AGGREGATE_PARALLEL_NVTX_RANGES
  cliOption: --aggregate-parallel-nvtx-ranges
  type: flag
  default: false
  title: Aggregate Parallel NVTX Ranges
  cliOnly: true
  description: Aggregate parallel NVTX ranges.
  mutuallyExclusiveGroup: Thread
- name: CSV
  cliOption: --csv
  type: flag
  default: false
  title: CSV format
  description: Additionally output data as CSV.
- name: SELECT_NVTX_BY
  cliOption: --select-nvtx-by
  type:
  - auto
  - index
  - median-duration
  - median-cpu-time
  title: Select NVTX By
  description: |
    Specify the strategy for selecting the instances of NVTX ranges to compute CPU metrics from each Nsight Systems report.

    Possible values:
      • 'auto': (default) Use 'median-cpu-time' strategy for reports with heterogeneous CPU cores, otherwise 'index' strategy.
      • 'index': Select NVTX range instances based on the median* duration from the first report, then use their indices in subsequent reports.
      • 'median-duration': Select NVTX range instances based on median* duration from each report.
      • 'median-cpu-time': Select NVTX range instances based on median* CPU time from each report.
     Note: median* is defined as the middle value in the sorted list. For an even number of elements, it is the second of the two middle values.
  default: auto
- name: MIN_PMU_SAMPLES_PER_NVTX
  cliOption: --min-pmu-samples-per-nvtx
  type: int
  title: Minimum PMU Samples Per NVTX
  description: |
    Minimum number of PMU samples within an NVTX range to consider the range for processing. NVTX ranges with fewer samples will be filtered out. Default is 3.
    WARNING: Decreasing this threshold may lead to less accurate results.
  default: 3
- name: DISTRIBUTE_ACROSS_ALL_THREADS
  cliOption: --distribute-across-all-threads
  type: flag
  default: false
  title: Distribute Across All Threads
  description: Distribute across all threads.
  cliOnly: true
- name: LOG_DETAILS
  cliOption: --log-details
  type: flag
  default: false
  title: Log Details
  description: Enable detailed logging for debugging purposes.
  cliOnly: true
```
