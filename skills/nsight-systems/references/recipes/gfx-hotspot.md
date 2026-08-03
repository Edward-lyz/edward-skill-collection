---
recipe: gfx_hotspot
display_name: Graphics Hotspot Analysis
source: installed-nsys/python/packages/nsys_recipe
---

# gfx_hotspot: Graphics Hotspot Analysis

## Live help at build time

```text
Per-recipe help is queried live at runtime with `nsys recipe <name> --help`.
```

## README

This recipe analyzes graphical applications' CPU activity and attempts
 to locate performance hotspots based on it. Frames are selected in one
 of four methods:

 * Longest Frame time (Slow Frames)

 * Time-based sampling (Periodic Frames)

 * Frames with highest transfer activity (Bar1 Reads)

 * Frames with least GPU activity (GR Idle)

The report view then allows comparing the selected frames to each other
 and to the median frame in the same metric, helping identify the main
 differences and possible problem areas in each one.

```yaml
moduleName: gfx_hotspot
displayName: Graphics Hotspot Analysis
description: |
  This recipe analyzes graphical applications' CPU activity and attempts to locate performance hotspots based on it. Frames are selected in one of four methods:
   * Longest Frame time (Slow Frames)
   * Time-based sampling (Periodic Frames)
   * Frames with highest transfer activity (Bar1 Reads)
   * Frames with least GPU activity (GR Idle)
   The report view then allows comparing the selected frames to each other and to the median frame in the same metric, helping identify the main differences and possible problem areas in each one.
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
- name: LOG
  cliOption: --log
  type:
  - NONE
  - ERROR
  - WARNING
  - INFO
  - DEBUG
  title: Log Level
  description: |
    Display logging for the recipe processing steps in the console.
    Possible values: NONE (default), ERROR, WARNING, INFO, DEBUG.
  default: NONE
- name: EXPORT_CACHE
  cliOption: --export-cache
  type:
  - 'yes'
  - 'no'
  - force
  default: 'yes'
  title: Export Cache
  description: |
    Cache the exported sqlite report from the nsys-rep file.
    Possible values:
      yes   - (default) Will generate a sqlite report if
              one does not exist.
      no    - Will not generate a sqlite report.
              Requires '--sqlite-path' to be set.
      force - Will always generate a report.
- name: EXPORT_CACHE_PATH
  cliOption: --export-cache-path
  type: string
  title: Export Cache Path
  description: |-
    Path of cached sqlite report. If '--export-cache' is 'no', this value is required.
- name: RUN_VIEWER
  cliOption: --run-viewer
  type: flag
  default: false
  cliOnly: true
  title: Run Viewer
  description: Will run the viewer in a localhost web server.
- name: VIEWER_SERVER_PORT
  cliOption: --viewer-server-port
  type: int
  default: 4200
  cliOnly: true
  title: Viewer Server Port
  description: Server port for the localhost viewer.
- name: OPEN_VIEWER
  cliOption: --open-viewer
  type: flag
  default: false
  title: Open Viewer
  cliOnly: true
  description: |-
    Will automatically open the viewer in the default web browser. Requires '--run-viewer' to be set.
```
