---
recipe: ucx_gpu_time_util_map
display_name: UCX and GPU Time Utilization Heatmap
source: installed-nsys/python/packages/nsys_recipe
---

# ucx_gpu_time_util_map: UCX and GPU Time Utilization Heatmap

## Live help at build time

```text
Per-recipe help is queried live at runtime with `nsys recipe <name> --help`.
```

## README

This recipe calculates the percentage of time that CUDA kernels were running
 and UCX communication was active, as well as their overlap. Note that this
 refers to time utilization and does not account for the actual hardware
 resource utilization.

```yaml
moduleName: ucx_gpu_time_util_map
displayName: UCX and GPU Time Utilization Heatmap
description: |-
  This recipe calculates the percentage of time that CUDA kernels were running and UCX communication was active, as well as their overlap. Note that this refers to time utilization and does not account for the actual hardware resource utilization.
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
- name: BINS
  cliOption: --bins
  type: int
  title: Number of bins
  default: 30
  description: |
    Number of bins (default: 30).
- name: DISABLE_ALIGNMENT
  cliOption: --disable-alignment
  type: flag
  default: false
  title: Disable Alignment
  description: |-
    Disable automatic session alignment. By default, session times are aligned based on the epoch time of the report file collection. This option will instead use relative time, which is useful for comparing individual sessions.
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
