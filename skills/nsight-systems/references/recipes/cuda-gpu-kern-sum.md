---
recipe: cuda_gpu_kern_sum
display_name: CUDA GPU Kernel Summary
source: installed-nsys/python/packages/nsys_recipe
---

# cuda_gpu_kern_sum: CUDA GPU Kernel Summary

## Live help at build time

```text
Per-recipe help is queried live at runtime with `nsys recipe <name> --help`.
```

## README

This recipe provides a summary of CUDA kernels and their execution times.

```yaml
moduleName: cuda_gpu_kern_sum
displayName: CUDA GPU Kernel Summary
description: |-
  This recipe provides a summary of CUDA kernels and their execution times.
type: stats
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
- name: CSV
  cliOption: --csv
  type: flag
  default: false
  title: CSV format
  description: Additionally output data as CSV.
- name: FILTER_TIME
  mutuallyExclusiveGroup: Filter
  cliOption: --filter-time
  type: int/int
  title: Time Filter
  description: Filter by time range in nanoseconds.
- name: FILTER_NVTX
  mutuallyExclusiveGroup: Filter
  cliOption: --filter-nvtx
  type: string[@string][/int]
  title: NVTX Filter
  description: |-
    Filter by NVTX range using only the start and end times of the matching ranges.
    Specify the domain only when the range is not in the default domain, or use '*' to include all domains. Any '@' or '/' in the names should be escaped with a backslash.
    The index is zero-based and is used to select the nth range. If no index is specified, all ranges will be used.
```
