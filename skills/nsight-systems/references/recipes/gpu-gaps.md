---
recipe: gpu_gaps
display_name: GPU Gaps
source: installed-nsys/python/packages/nsys_recipe
---

# gpu_gaps: GPU Gaps

## Live help at build time

```text
Per-recipe help is queried live at runtime with `nsys recipe <name> --help`.
```

## README

This recipe identifies time regions where a GPU is idle for longer than a set
 threshold. For each process, each GPU device is examined, and gaps are found
 within the time range that starts with the beginning of the first GPU
 operation on that device and ends with the end of the last GPU operation on
 that device. Profiling overheads are taken into account to exclude GPU gaps
 that cannot be addressed by the user.

```yaml
moduleName: gpu_gaps
displayName: GPU Gaps
description: |-
  This recipe identifies time regions where a GPU is idle for longer than a set threshold. For each process, each GPU device is examined, and gaps are found within the time range that starts with the beginning of the first GPU operation on that device and ends with the end of the last GPU operation on that device. Profiling overheads are taken into account to exclude GPU gaps that cannot be addressed by the user.
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
- name: NVTX
  cliOption: --nvtx
  type: string[@string]
  title: Filter by NVTX
  description: Filter by NVTX range.
- name: ROWS
  cliOption: --rows
  type: int
  default: -1
  title: Rows limit
  description: Maximum number of rows per input file.
- name: FILTER_TIME
  cliOption: --filter-time
  type: int/int
  title: Time Filter
  description: Filter by time range in nanoseconds.
- name: GAP
  cliOption: --gap
  type: int
  default: 500
  title: Gap iteration threshold
  description: Minimum duration of GPU gaps in milliseconds
```
