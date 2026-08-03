---
source_path: UserGuide/topics/target-sampling-options-on-windows.rst
title: #### Target Sampling Options on Windows
---
#### Target Sampling Options on Windows

      :alt: Target sampling options
      :class: image

Nsight Systems can sample one process tree. Sampling here means interrupting each processor periodically. The sampling rate is defined in the project settings and is either 100Hz, 1KHz (default value), 2Khz, 4KHz, or 8KHz.

      :alt: Thread activity option
      :class: image

On Windows, Nsight Systems can collect thread activity of one process tree. Collecting thread activity means that each thread context switch event is logged and (optionally) a backtrace is collected at the point that the thread is scheduled back for execution. Thread states are displayed on the timeline.

If it was collected, the thread backtrace is displayed when hovering over a region where the thread execution is blocked.
