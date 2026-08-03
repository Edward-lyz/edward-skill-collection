---
recipe: gpu_vram_usage_trace
display_name: Graphics VRAM Usage
source: installed-nsys/python/packages/nsys_recipe
---

# gpu_vram_usage_trace: Graphics VRAM Usage

## Live help at build time

```text
Per-recipe help is queried live at runtime with `nsys recipe <name> --help`.
```

## README

This recipe helps developers analyze VRAM management in games and graphics
 applications in order to identify performance issues and optimize resource allocation.
 It shows frame duration and VRAM usage, resource residency tables
 for selected frames, and provides a detailed frames comparison.

```yaml
moduleName: gpu_vram_usage_trace
displayName: Graphics VRAM Usage
description: |-
  This recipe helps developers analyze VRAM management in games and graphics applications in order to identify performance issues and optimize resource allocation. It shows frame duration and VRAM usage, resource residency tables for selected frames, and provides a detailed frames comparison.
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
```
