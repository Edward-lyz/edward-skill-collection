---
recipe: gpu_time_util
display_name: GPU Time Utilization
source: installed-nsys/python/packages/nsys_recipe
---

# gpu_time_util: GPU Time Utilization

## Live help at build time

```text
Per-recipe help is queried live at runtime with `nsys recipe <name> --help`.
```

## README

This recipe identifies time regions with low GPU utilization. For each
 process, each GPU device is examined, and a time range is created that starts
 with the beginning of the first GPU operation on that device and ends with the
 end of the last GPU operation on that device. This time range is then divided
 into equal chunks, and the GPU utilization is calculated for each chunk. The
 utilization includes all GPU operations as well as profiling overheads that the
 user cannot address.


Note that the utilization refers to the 'time' utilization and not the
 'resource' utilization. This script does not take into account how many GPU
 resources are being used. Therefore, a single running memcpy is considered the
 same amount of 'utilization' as a huge kernel that takes over all the cores.
 If multiple operations run concurrently in the same chunk, their utilization
 will be added up and may exceed 100%.


Chunks with an in-use percentage less than the threshold value are displayed.
 If consecutive chunks have a low in-use percentage, the individual chunks are
 coalesced into a single display record, keeping the weighted average of
 percentages. This is why returned chunks may have different durations.

```yaml
moduleName: gpu_time_util
displayName: GPU Time Utilization
description: |-
  This recipe identifies time regions with low GPU utilization. For each process, each GPU device is examined, and a time range is created that starts with the beginning of the first GPU operation on that device and ends with the end of the last GPU operation on that device. This time range is then divided into equal chunks, and the GPU utilization is calculated for each chunk. The utilization includes all GPU operations as well as profiling overheads that the user cannot address.

  Note that the utilization refers to the 'time' utilization and not the 'resource' utilization. This script does not take into account how many GPU resources are being used. Therefore, a single running memcpy is considered the same amount of 'utilization' as a huge kernel that takes over all the cores. If multiple operations run concurrently in the same chunk, their utilization will be added up and may exceed 100%.

  Chunks with an in-use percentage less than the threshold value are displayed. If consecutive chunks have a low in-use percentage, the individual chunks are coalesced into a single display record, keeping the weighted average of percentages. This is why returned chunks may have different durations.
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
- name: THRESHOLD
  cliOption: --threshold
  type: int
  title: Utilization Threshold
  default: 50
  description: Maximum percentage of time the GPU is being used
- name: CHUNKS
  cliOption: --chunks
  type: int
  title: Number of chunks
  default: 30
  description: Number of equal-duration chunks
```
