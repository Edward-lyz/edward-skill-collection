---
source_path: UserGuide/topics/cuda-trace.rst
title: CUDA Trace
---
# CUDA Trace


## Basic CUDA trace

Nsight Systems is capable of capturing information about CUDA execution in the
profiled process.

The following information can be collected and presented on the timeline in the
report:

-  CUDA API trace — trace of CUDA Runtime and CUDA Driver calls made by the application.

   -  CUDA Runtime calls typically start with ``cuda`` prefix (e.g. ``cudaLaunch``).

   -  CUDA Driver calls typically start with ``cu`` prefix (e.g. ``cuDeviceGetCount``).

-  CUDA workload trace — trace of activity happening on the GPU, which includes
   memory operations (e.g., Host-to-Device memory copies) and kernel executions.
   Within the threads that use the CUDA API, additional child rows will appear
   in the timeline tree.

-  On Nsight Systems Workstation Edition, cuDNN and cuBLAS API tracing and OpenACC tracing.

   :alt: CUDA thread rows
   :class: image

Near the bottom of the timeline row tree, the GPU node will appear and contain
a CUDA node. Within the CUDA node, each CUDA context used within the process
will be shown along with its corresponding CUDA streams. Steams will contain
memory operations and kernel launches on the GPU. Kernel launches are
represented by blue, while memory transfers are displayed in red.

   :alt: CUDA GPU rows
   :class: image

The easiest way to capture CUDA information is to launch the process from
Nsight Systems, and it will set up the environment for you. To do so, simply set
up a normal launch and select the **Collect CUDA trace** checkbox.

For Nsight Systems Workstation Edition this looks like:

      :alt: Configure CUDA trace
      :class: image

For Nsight Systems Embedded Platforms Edition this looks like:

      :alt: Configure CUDA trace
      :class: image

#### CUDA trace methods

By default, Nsight Systems uses CUDA hardware trace, also called Hardware Event
System (HES) trace, when CUDA tracing is enabled on a supported system. In the
CLI, ``--trace=cuda`` selects this default trace method. Hardware trace usually
has lower overhead than the legacy software-instrumented trace, especially for
workloads that launch many short kernels.

If CUDA hardware trace cannot be collected, Nsight Systems may automatically use
the legacy software-instrumented trace instead. The Diagnostics Summary page
reports which CUDA trace method was collected and whether a fallback occurred.

Use the legacy software trace when CUDA hardware trace is unsupported or when
you need to compare results against the previous CUDA trace method. In the CLI,
use ``--trace=cuda-sw`` to request software trace explicitly.

Additional configuration parameters are available:


- **System-wide CUDA trace** - collect CUDA trace from eligible processes across
  the system that are launched after collection starts. By default, CUDA trace is
  captured from the target process and its descendants only. Select this option
  to switch to system-wide trace mode.

  System-wide CUDA trace requirements:

  - Processes running as a different user are not traced.
  - POSIX root Nsight Systems sessions trace CUDA processes running as root
    without additional setup.
  - POSIX non-root Nsight Systems sessions trace same-user CUDA processes only
    when ``CUDA_INJECTION_SHM_ALLOWED=TRUE`` is set in the target process
    environment before launch.
  - Windows elevated Nsight Systems sessions trace same-user CUDA processes
    without additional setup.
  - Windows non-elevated Nsight Systems sessions trace non-elevated same-user
    CUDA processes only when ``CUDA_INJECTION_SHM_ALLOWED=TRUE`` is set in the
    target process environment before launch.

  Only one session can collect system-wide CUDA trace at a time on the entire
  system; other sessions will fall back to process-tree scope.
  
- **CUDA trace method** - by default, CUDA trace uses hardware trace on supported
  GPUs, beginning with Blackwell. Use the legacy software trace for MPS
  workloads, MIG partitions, vGPU or virtual machine environments, Confidential
  Compute systems, unsupported GPUs or drivers, or when you need to compare
  against the previous CUDA trace method. In the CLI, use ``--trace=cuda-sw`` to
  request software trace explicitly.

-  **Collect backtraces for API calls longer than X seconds** - turns on
   collection of CUDA API backtraces and sets the minimum time a CUDA API event
   must take before its backtraces are collected. Setting this value too low can
   cause high application overhead and seriously increase the size of your
   results file.

-  **Flush data periodically** — specifies the period after which an attempt to
   flush CUDA trace data will be made. Normally, in order to collect full CUDA
   trace, the application needs to finalize the device used for CUDA work (call
   ``cudaDeviceReset()``, and then let the application gracefully exit (as
   opposed to crashing).

   This option allows flushing CUDA trace data even before the device is
   finalized. However, it might introduce additional overhead to a random CUDA
   Driver or CUDA Runtime API call.

-  **Skip some API calls** — avoids tracing insignificant CUDA Runtime API calls
   (namely, ``cudaConfigureCall()``, ``cudaSetupArgument()``,
   ``cudaHostGetDevicePointers()``). Not tracing these functions allows
   Nsight Systems to significantly reduce the profiling overhead, without losing
   any interesting data.

-  **Collect GPU Memory Usage** - collects information used to generate a graph
   of CUDA allocated memory across time. Note that this will increase overhead.
   See CUDA GPU Memory Allocation Graph.

-  **Collect Unified Memory CPU page faults** - collects information on page
   faults that occur when CPU code tries to access a memory page that resides on
   the device. See  Unified Memory CPU Page Faults.

-  **Collect Unified Memory GPU page faults** - collects information on page
   faults that occur when GPU code tries to access a memory page that resides on
   the CPU. See Unified Memory GPU Page Faults.

-  **Collect CUDA Graph trace** - by default, CUDA tracing will collect and
   expose information on a whole graph basis. The user can opt to collect on a
   node per node basis. See CUDA Graph Trace.
   
-  **Collect CUDA Event trace** - track device-side CUDA Event (the
   synchronization mechanism) completion, and get better correlation support
   among CUDA Event APIs. CUDA Event Trace. 

-  For Nsight Systems Workstation Edition, **Collect cuDNN trace**, **Collect cuBLAS trace**,
   **Collect OpenACC trace** - selects which (if any) extra libraries that
   depend on CUDA to trace.

   OpenACC versions 2.0, 2.5, and 2.6 are supported when using PGI runtime
   version 15.7 or greater and not compiling statically. In order to differentiate
   constructs, a PGI runtime of 16.1 or later is required. Note that
   Nsight Systems Workstation Edition does not support the GCC implementation of OpenACC at this
   time.

Note:

   If your application crashes before all collected CUDA trace data has been
   copied out, some or all data might be lost and not present in the report.

Note:

   Nsight Systems will not have information about CUDA events that were still in
   device buffers when analysis terminated. It is a good idea, if using
   cudaProfilerAPI to control analysis to call cudaDeviceReset before ending
   analysis.
