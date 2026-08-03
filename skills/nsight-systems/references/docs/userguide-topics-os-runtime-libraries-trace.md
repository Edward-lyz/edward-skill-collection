---
source_path: UserGuide/topics/os-runtime-libraries-trace.rst
title: OS Runtime Libraries Trace
---
# OS Runtime Libraries Trace

On Linux, OS runtime libraries can be traced to gather information about low-level userspace APIs. This traces the system call wrappers and thread synchronization interfaces exposed by the C runtime and POSIX Threads (pthread) libraries. This does not perform a complete runtime library API trace, but instead focuses on the functions that can take a long time to execute, or could potentially cause your thread be unscheduled from the CPU while waiting for an event to complete. OS runtime trace is not available for Windows targets.

OS runtime tracing complements and enhances sampling information by:

#. Visualizing when the process is communicating with the hardware, controlling resources, performing multi-threading synchronization or interacting with the kernel scheduler.

#. Adding additional thread states by correlating how OS runtime libraries traces affect the thread scheduling:

   -  **Waiting** — the thread is not scheduled on a CPU, it is inside of an OS runtime libraries trace and is believed to be waiting on the firmware to complete a request.

   -  **In OS runtime library function** — the thread is scheduled on a CPU and inside of an OS runtime libraries trace. If the trace represents a system call, the process is likely running in kernel mode.

#. Collecting backtraces for long OS runtime libraries call. This provides a way to gather blocked-state backtraces, allowing you to gain more context about why the thread was blocked so long, yet avoiding unnecessary overhead for short events.

      :alt: OS runtime libraries row
      :class: image

#. Collecting file access data for API calls that interact with files. This helps in identifying performance bottlenecks related to file I/O operations and provides insights into how file access patterns affect overall application performance.

    |os-runtime-file-access-flags-and-mode| |os-runtime-file-access-bytes-copied|

      :alt: OS runtime file access flags and mode
      :class: image

      :alt: OS runtime file access bytes copied
      :class: image

Note:
       File access data collection is not enabled by default.

To enable OS runtime libraries tracing from Nsight Systems:

**CLI** — Use the ``-t``, ``--trace`` option with the ``osrt`` parameter. See
Command Line Options  for more information.

**GUI** — Select the **Collect OS runtime libraries trace** checkbox.

      :alt: Configure OS runtime libraries trace
      :class: image

You can also use **Skip if shorter than**. This will skip calls shorter than the given threshold. Enabling this option will improve performances as well as reduce noise on the timeline. We strongly encourage you to skip OS runtime libraries call shorter than 1 μs.
