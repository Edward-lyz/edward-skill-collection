---
source_path: UserGuide/topics/analysis-summary-view.rst
title: ## Analysis Summary View
---
## Analysis Summary View

This view shows a summary of the profiling session. It can be used
to review the various configurations used to generate this report. Depending on
the features used, different subsections may be shown, but they may include

*  **Profiling session information** - including information about the capture
   time, duration, report file, and host information.
*  **Target information** - including OS and driver versions.
*  **Process summary** - processes run during analysis, arguments, and CPU
   utilization.
*  **Module summary** - modules used including name and CPU time (overall and
   per-process). **Note** - Module percentage in Analysis Summary page is
   calculated based on the cpu cycles logged in an IP sample for that module.
   When cpu cycles is inaccurate or absent (as is the case on x86_64 target),
   the module percentage is inaccurate.
*  **Thread summary** - including process ID, name, and CPU utilization
*  **CPU information** - information about all CPUs on the system
*  **GPU information** - information about all GPUs on the system
*  **Network hardware info** - information about NICs/Switches/Storage devices
   analyzed in the run.
*  **Analysis options** - information about which Nsight Systems options were
   used when generating this report.
*  **Nsight Systems** - information about the version used to collect and
   display the results.
   
   


Information from this view can be selected and copied using the mouse cursor.
