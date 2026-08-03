---
source_path: UserGuide/topics/profiling-qnx-targets-from-the-gui.rst
title: ## Profiling QNX Targets from the GUI
---
## Profiling QNX Targets from the GUI

Profiling on QNX devices is similar to the profiling on Linux devices. Please
refer to the Profiling Linux Targets from the GUI 
section for the detailed documentation. The major differences on the platforms
are listed below:

-  Backtrace sampling is not supported. Instead backtraces are collected for
   long OS runtime libraries calls. Please refer to the `OS Runtime Libraries
   Trace <index.html#os-runtime-libraries-trace>`__ section for the detailed
   documentation.

-  CUDA support is limited to CUDA 9.0+.

-  Filesystem on QNX device might be mounted read-only. In that case Nsight Systems
   is not able to install target-side binaries, required to run the profiling
   session. Please make sure that target filesystem is writable before connecting
   to QNX target. For example, make sure the following command works:

   ::

      echo XX > /xx && ls -l /xx
