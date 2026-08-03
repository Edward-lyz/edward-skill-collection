---
source_path: UserGuide/topics/wddm-hw-scheduler.rst
title: WDDM HW Scheduler
---
# WDDM HW Scheduler

When GPU Hardware Scheduling is enabled in Windows 10 or newer, the Windows Display Driver Model (WDDM) uses the ``DxgKrnl`` ETW provider to expose report of NVIDIA GPUs' hardware scheduling context switches.

Nsight Systems can capture these context switch events, and display under the GPUs in the timeline rows titled WDDM HW Scheduler - [HW Queue type]. The ranges under each queue will show the process name and PID assoicated with the GPU work during the time period.

The events will be captured if GPU Hardware Scheduling is enabled in the Windows System Display settings, and "Collect WDDM Trace" is enabled in the Nsight Systems Project Settings.

      :alt: WDDM HW Scheduler row for 3D HW Queue
      :class: image
