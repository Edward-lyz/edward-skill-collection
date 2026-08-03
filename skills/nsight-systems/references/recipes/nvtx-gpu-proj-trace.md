---
recipe: nvtx_gpu_proj_trace
display_name: NVTX GPU Projection Trace
source: installed-nsys/python/packages/nsys_recipe
---

# nvtx_gpu_proj_trace: NVTX GPU Projection Trace

## Live help at build time

```text
Per-recipe help is queried live at runtime with `nsys recipe <name> --help`.
```

## README

This recipe provides a trace of NVTX time ranges projected from the CPU onto
 the GPU. Each NVTX range contains one or more GPU operations. A GPU operation
 is considered to be 'contained' by an NVTX range if the CUDA API call used
 to launch the operation is within the NVTX range. Only ranges that start and
 end on the same thread are taken into account.


The projected range will have the start timestamp of the first enclosed GPU
 operation and the end timestamp of the last enclosed GPU operation, as well
 as the stack state and relationship to other NVTX ranges.

```yaml
moduleName: nvtx_gpu_proj_trace
displayName: NVTX GPU Projection Trace
description: |-
  This recipe provides a trace of NVTX time ranges projected from the CPU onto the GPU. Each NVTX range contains one or more GPU operations. A GPU operation is considered to be 'contained' by an NVTX range if the CUDA API call used to launch the operation is within the NVTX range. Only ranges that start and end on the same thread are taken into account.

   The projected range will have the start timestamp of the first enclosed GPU operation and the end timestamp of the last enclosed GPU operation, as well as the stack state and relationship to other NVTX ranges.
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
- name: PER_GPU
  mutuallyExclusiveGroup: Per
  cliOption: --per-gpu
  type: string
  title: Per GPU
  description: Group events by GPU.
- name: PER_STREAM
  mutuallyExclusiveGroup: Per
  cliOption: --per-stream
  type: string
  title: Per Stream
  description: Group events by stream within each GPU.
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
- name: FILTER_PROJECTED_NVTX
  mutuallyExclusiveGroup: Filter
  cliOption: --filter-projected-nvtx
  type: string[@string][/int]
  title: Filter by Projected NVTX
  description: |-
    Filter by projected NVTX range using only the start and end times of the matching ranges.
    Specify the domain only when the range is not in the default domain, or use '*' to include all domains. Any '@' or '/' in the names should be escaped with a backslash.
    The index is zero-based and is used to select the nth range. If no index is specified, all ranges will be used.
```
