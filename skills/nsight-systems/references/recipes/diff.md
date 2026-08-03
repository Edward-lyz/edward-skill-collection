---
recipe: diff
display_name: Statistics Diff
source: installed-nsys/python/packages/nsys_recipe
---

# diff: Statistics Diff

## Live help at build time

```text
Per-recipe help is queried live at runtime with `nsys recipe <name> --help`.
```

## README

This script compares outputs from two runs of the same statistical recipe.

```yaml
moduleName: diff
displayName: Statistics Diff
description: |-
  This script compares outputs from two runs of the same statistical recipe.
arguments:
- name: INPUT
  cliOption: --input
  type: process_input
  title: Input
  description: Paths to recipe output directories to compare
  required: true
  mutuallyExclusiveGroup: Input
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
- name: PRINT_COMPAT_RECIPES
  cliOption: --print-compat-recipes
  type: flag
  default: false
  title: Print Compatible Recipes
  description: |-
    Print recipes that can be used to generate the outputs to diff.
  mutuallyExclusiveGroup: Input
- name: TOLERANCE
  cliOption: --tolerance
  type: int
  title: Tolerance
  default: 0
  description: Replace values smaller than the specified tolerance with 0
- name: DROP
  cliOption: --drop
  type: flag
  default: false
  title: Drop Rows
  description: Drop rows where all values are less than 0
- name: CSV
  cliOption: --csv
  type: flag
  default: false
  title: CSV format
  description: Additionally output data as CSV.
```
