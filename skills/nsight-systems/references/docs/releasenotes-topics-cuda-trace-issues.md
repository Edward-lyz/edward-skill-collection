---
source_path: ReleaseNotes/topics/cuda-trace-issues.rst
title: ## CUDA Trace Issues
---
## CUDA Trace Issues


-  CUDA hardware trace, also called Hardware Event System (HES) trace, is the
   default CUDA trace method on supported systems. Hardware trace is not
   supported for MPS workloads, MIG partitions, vGPU or virtual machine
   environments, some Confidential Compute configurations, unsupported GPUs, or
   incompatible driver or CUPTI combinations. In these cases, Nsight Systems may
   automatically fall back to the legacy software-instrumented CUDA trace and
   report the trace method in the Diagnostics Summary page. Use
   ``--trace=cuda-sw`` to request software CUDA trace explicitly.

-  If a system is in the CC-DevTools mode (CC stands for Confidential Compute)
   and Nsight Systems is used to trace CUDA in an application using libcrypto,
   Nsight Systems may crash when the application exits. The crash occurs during
   the application teardown and causes profiler data loss. To avoid losing CUDA
   tracing data in this situation, a few options exist.

   1. Add a cudaDeviceSynchronize call to the application immediately before the
   application exits. Nsight Systems flushes all available data on a
   synchronization and data loss will be avoided.

   2. Add a cudaProfilerStop call to the application immediately before the
   application exits and set the Nsight Systems ``--flush-on-cudaprofilerstop``
   switch to true.  In this case, Nsight Systems will flush all available data
   at this point.

   3. End the profile before the application exits using one of many Nsight Systems
   mechanisms to end a profile. For example;

      -  Set a collection duration that ends before the application exits (see
         the ``--duration`` switch).

      -  Use a capture range to only collect data during a specific period of the
         application's execution (see the ``--capture-range`` switch).

      -  Set the CUDA flush interval to frequently flush data during a profile. Any
         data collected after the last flush and before the application's exit will
         likely be lost. Note that frequent CUDA flushes will increase profiling
         overhead.

      -  Use the Nsight Systems CLI's ``start``, ``launch``, ``stop`` commands
         to manually start and stop a collection before the application exits.

-  The `cudaMemPrefetchAsync()` API allows the user to specify a stream to
   enqueue a memory prefetch operation. However, Nsight Systems does not get the
   stream information for UVM page migrations from the UVM backend. Thus,
   Nsight Systems cannot show stream information correctly correlated with a
   `cudaMemPrefetchAsync()` API call. This will be fixed in a future version.

-  When using CUDA Toolkit 10.X, tracing of DtoD memory copy operations may
   result in a crash. To avoid this issue, update CUDA Toolkit to 11.X or the
   latest version.

-  Nsight Systems will not trace kernels when a CDP (CUDA Dynamic Parallelism)
   kernel is found in a target application on Volta devices or later.

-  On Tegra platforms, CUDA trace requires root privileges. Use the
   **Launch as root** checkbox in project settings to make the profiled
   application run as root.

-  If the target application uses multiple streams from multiple threads,
   CUDA event buffers may not be released properly. In this case, you will see
   the following diagnostic error:


      Couldn't allocate CUPTI bufer x times. Some CUPTI events may
             be missing.

   Please contact the Nsight Systems team.

-  In this version of Nsight Systems, if you are starting and stopping profiling
   inside your application using the interactive CLI, the CUDA memory allocation
   graph generation is only guaranteed to be correct in the first profiling
   range. This limitation will be removed in a future version of the product.

-  CUDA GPU trace collection requires a fraction of GPU memory. If your
   application utilizes all available GPU memory, CUDA trace might not work or
   can break your application. As an example cuDNN application can crash with
   ``CUDNN_STATUS_INTERNAL_ERROR`` error if GPU memory allocation fails.

-  For older Linux kernels, prior to 4.4, when profiling very short-lived
   applications (~1 second) that exit in the middle of the profiling session, it
   is possible that Nsight Systems will not show the CUDA events on the timeline.

-  When more than 64k serialized CUDA kernels and memory copies are executed in
   the application, you may encounter the following exception during profiling:

   ::

      InvalidArgumentException: "Wrong event order detected"

   Please upgrade to the CUDA 9.2 driver at minimum to avoid this problem. If
   you cannot upgrade, you can get a partial analysis, missing potentially a
   large fraction of CUDA events, by using the CLI.

-  On Vibrante, when running a profiling session with multiple targets that are
   guest VMs in a CCC configuration behind a NAT, you may encounter an error
   with the following text during profiling:

   ::

      Failed to sync time on device.

   Please edit the group connection settings, select **Targets on the same SoC**
   checkbox there and try again.

-  When using the 455 driver, as shipped with CUDA Tool Kit 11.1, and tracing
   CUDA with Nsight Systems you many encounter a crash when the application
   exits. To avoid this issue, end your profiling session before the application
   exits or update your driver.
