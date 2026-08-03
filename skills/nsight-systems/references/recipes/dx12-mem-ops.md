---
recipe: dx12_mem_ops
display_name: DX12 Memory Operations
source: installed-nsys/python/packages/nsys_recipe
---

# dx12_mem_ops: DX12 Memory Operations

## Live help at build time

```text
Per-recipe help is queried live at runtime with `nsys recipe <name> --help`.
```

## README

This recipe identifies memory operations with the following warnings:

1. HEAP_CREATED_WITH_ZEROING

2. COMMITTED_RESOURCE_CREATED_WITH_ZEROING

3. NONEMPTY_MAP_FROM_UPLOAD_HEAP

4. NONEMPTY_MAP_TO_WRITE_COMBINE_PAGE

5. NONEMPTY_UNMAP_TO_READBACK_HEAP

6. NONEMPTY_UNMAP_FROM_WRITE_BACK_PAGE

7. READ_FROM_UPLOAD_HEAP_SUBRESOURCE

8. READ_FROM_SUBRESOURCE_TO_WRITE_COMBINE_PAGE

9. WRITE_TO_READBACK_HEAP_SUBRESOURCE

10. WRITE_TO_SUBRESOURCE_FROM_WRITE_BACK_PAGE

```yaml
moduleName: dx12_mem_ops
displayName: DX12 Memory Operations
description: |-
  This recipe identifies memory operations with the following warnings:
   1. HEAP_CREATED_WITH_ZEROING
   2. COMMITTED_RESOURCE_CREATED_WITH_ZEROING
   3. NONEMPTY_MAP_FROM_UPLOAD_HEAP
   4. NONEMPTY_MAP_TO_WRITE_COMBINE_PAGE
   5. NONEMPTY_UNMAP_TO_READBACK_HEAP
   6. NONEMPTY_UNMAP_FROM_WRITE_BACK_PAGE
   7. READ_FROM_UPLOAD_HEAP_SUBRESOURCE
   8. READ_FROM_SUBRESOURCE_TO_WRITE_COMBINE_PAGE
   9. WRITE_TO_READBACK_HEAP_SUBRESOURCE
   10. WRITE_TO_SUBRESOURCE_FROM_WRITE_BACK_PAGE
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
```
