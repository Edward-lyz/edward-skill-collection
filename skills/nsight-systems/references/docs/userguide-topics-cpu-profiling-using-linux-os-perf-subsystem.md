---
source_path: UserGuide/topics/cpu-profiling-using-linux-os-perf-subsystem.rst
title: CPU Profiling on Linux
---
# CPU Profiling on Linux

Nsight Systems on Linux targets, utilizes the Linux OS' perf subsystem to sample
CPU Instruction Pointers (IPs) and backtraces, trace CPU context switches, and
sample CPU and OS event counts. The Linux perf tool utilizes the same perf
subsystem.

Nsight Systems Embedded Platforms Edition on Linux kernel prior to v5.15 uses a custom kernel module to
collect the same data. The Nsight Systems CLI command
``nsys status --environment`` indicates when the kernel module is used instead
of the Linux OS' perf subsystem.

## Features

-  **CPU Instruction Pointer / Backtrace Sampling**

   Nsight Systems can sample CPU Instruction Pointers / backtraces periodically.
   The collection of a sample is triggered by a hardware event overflow - e.g., a
   sample is collected after every 1 million CPU reference cycles on a per thread
   basis. In the GUI, samples are shown on the individual thread timelines, in
   the Event Viewer, and in the Top Down, Bottom Up, or Flat views which provide
   histogram-like summaries of the data. IP / backtrace collections can be
   configured in process-tree or system-wide mode. In process-tree mode,
   Nsight Systems will sample the process, and any of its descendants, launched
   by the tool. In system-wide mode, Nsight Systems will sample all processes
   running on the system, including any processes launched by the tool.

-  **CPU Context Switch Tracing**

   Nsight Systems can trace every time the OS schedules a thread on a logical
   CPU and every time the OS thread gets unscheduled from a logical CPU. The
   data is used to show CPU utilization and OS thread utilization within the
   Nsight Systems GUI. Context switch collections can be configured in
   process-tree or system-wide mode. In process-tree mode, Nsight Systems will
   trace the process, and any of its descendants, launched by Nsight Systems.
   In system-wide mode, Nsight Systems will trace all processes running on the
   system, including any processes launched by the Nsight Systems.

-  **CPU Event Sampling**

   Nsight Systems can periodically sample CPU hardware event counts and OS event
   counts and show the event's rate over time in the Nsight Systems GUI. Event
   sample collections can be configured in system-wide mode only. In system-wide
   mode, Nsight Systems will sample event counts of all CPUs and the OS event
   counts running on the system. Event counts are not directly associated with
   processes or threads.

-  **CPU Core / Uncore Events and Metrics**

   Nsight Systems can access and make available information about CPU core /
   uncore events and metrics.
   The ``--cpu-metrics=help`` command will print grammar describing how to list
   supported core and uncore PMUs, their events and derived metrics, and
   supported uncore PMU event filters.
   The selected events (with/without filters) and metrics can be fed into the
   ``--cpu-metrics`` switch by name or by alias. These events and metrics can be
   used to determine how the CPU or SoC is oversubscribed. For example, see the
   `Grace Performance Tuning Guide
   <https://docs.nvidia.com/grace-performance-tuning-guide.pdf>`__. 
   
   In this version of Nsight Systems, ``--cpu-metrics`` is available only on
   Linux and only for NVIDIA Grace CPU, NVIDIA GB10 Grace Blackwell Superchip
   (for example, on NVIDIA DGX Spark), and NVIDIA Thor (for example, in NVIDIA
   Jetson AGX Thor). Support for uncore events and metrics is more limited.

## System Requirements

-  **Paranoid Level**

   The `system's paranoid level
   <https://www.kernel.org/doc/Documentation/sysctl/kernel.txt>`__ must be 2 or lower.

   :name: table_cpucoremetrics_table
   :class: table-compact

   +----------------+---------------------------------------------+--------------------------------------------+----------------------------------------------+---------------------------------------------+---------------------------------+
   | Paranoid Level | CPU IP/backtrace Sampling process-tree mode | CPU IP/backtrace Sampling system-wide mode | CPU Context Switch Tracing process-tree mode | CPU Context Switch Tracing system-wide mode | Event Sampling system-wide mode |
   +================+=============================================+============================================+==============================================+=============================================+=================================+
   | 3 or greater   | not available                               | not available                              | not available                                | not available                               | not available                   |
   +----------------+---------------------------------------------+--------------------------------------------+----------------------------------------------+---------------------------------------------+---------------------------------+
   | 2              | User mode IP/backtrace samples only         | not available                              | available                                    | not available                               | not available                   |
   +----------------+---------------------------------------------+--------------------------------------------+----------------------------------------------+---------------------------------------------+---------------------------------+
   | 1              | Kernel and user mode IP/backtrace samples   | not available                              | available                                    | not available                               | not available                   |
   +----------------+---------------------------------------------+--------------------------------------------+----------------------------------------------+---------------------------------------------+---------------------------------+
   | 0, -1          | Kernel and user mode IP/backtrace samples   | Kernel and user mode IP/backtrace samples  | available                                    | available                                   | hardware and OS events          |
   +----------------+---------------------------------------------+--------------------------------------------+----------------------------------------------+---------------------------------------------+---------------------------------+

-  **Kernel Version**

   To support the CPU profiling features utilized by Nsight Systems, the kernel
   version must be greater than or equal to v4.3. RedHat has backported the
   required features to the v3.10.0-693 kernel. RedHat distros and their
   derivatives (e.g. CentOS) require a 3.10.0-693 or later kernel. Use the
   ``uname -r`` command to check the kernel's version.

-  **perf_event_open syscall**

   The perf_event_open syscall needs to be available. When running within a
   Docker container, the default seccomp settings will normally block the
   perf_event_open syscall. To workaround this issue, use the Docker
   ``run --privileged`` switch when launching the docker or modify the docker's
   seccomp settings. Some VMs (virtual machines), e.g. AWS, may also block the
   perf_event_open syscall.

-  **Sampling Trigger**

   In some rare case, a sampling trigger is not available. The sampling trigger
   is either a hardware or software event that causes a sample to be collected.
   Some VMs block hardware events from being accessed and therefore, prevent
   hardware events from being used as sampling triggers. In those cases,
   Nsight Systems will fall back to using a software trigger if possible.

-  **Checking Your Target System**

   Use the ``nsys status --environment`` command to check if a system meets the
   Nsight Systems CPU profiling requirements. Example output from this command
   is shown below. Note that this command does not check for Linux capability
   overrides - i.e., if the user or executable files have ``CAP_SYS_ADMIN`` or
   ``CAP_PERFMON`` capability. Also, note that this command does not indicate if
   system-wide mode can be used.

      :alt: environment status output
      :class: image

## Configuring a CPU Profiling Collection

When configuring Nsight Systems for CPU Profiling from the CLI, use some or all
of the following options: ``--sample``, ``--cpuctxsw``, ``--event-sample``,
``--backtrace``, ``--cpu-core-events``, ``--event-sampling-interval``,
``--os-events``, ``--samples-per-backtrace``, and ``--sampling-period``.

Details about these options, including examples can be found  at
cli-profiling.

When configuring from the GUI, the following options are available:

   :alt: GUI configuration for CPU profiling
   :class: image

The configuration used during CPU profiling is documented in the Analysis Summary:

   :alt: CPU profiling in analysis summary
   :class: image

As well as in the Diagnosics Summary:

   :alt: CPU profiling in diagnostics summary
   :class: image

#### Collecting Source File and Line Information

Starting with Nsight Systems 2026.4, CPU sampling can collect source file and
line information for the Top-Down and Bottom-Up function table modes. This adds
the Source File and Source Line columns to those views, which can help identify
the exact loop, conditional statement, or call site responsible for the most CPU
usage.

The **Collect source file and line information** option also applies to CUDA API,
OS runtime, and Python backtraces when available. This information is collected
by default on supported Linux targets. Disable it to reduce report generation
time.

To configure this information from the GUI, use the **Collect source file and
line information** option.

   :alt: Collect source file and line information option
   :class: image

To configure this information from the CLI, use ``--show-source-info`` with the
``profile`` or ``start`` command. For example, to disable the default source
file and line collection:

::

   ./nsys profile --show-source-info=false --backtrace=dwarf --trace=cuda,osrt,nvtx \
       --stats=true --cuda-memory-usage=true --export sqlite \
       --cuda-um-cpu-page-faults=true --force-overwrite=true \
       -o myReport /path/to/myApp

For an interactive session, set this option on ``nsys start``. It is not
configured by ``nsys launch``.

When this information is disabled, report generation is faster, but source file
and line information is not resolved for CPU samples or supported backtraces.

## Visualizing CPU Profiling Results

Here are example screenshots visualizing CPU profiling results. For details
about navigating the Timeline View and the backtraces, see the section on
Timeline View in the Reading Your Report in the GUI section of the User Guide .

Example of CPU IP/Backtrace Data

   :alt: Timeline showing CPU IP/backtrace information
   :class: image

In the timeline, yellow-orange marks can be found under each thread's timeline
that indicate the moment an IP / backtrace sample was collected on that thread
(e.g., see the yellow-orange marks in the Specific Samples box above). Hovering
the cursor over a mark will cause a tooltip to display the backtrace for that
sample.

Below the Timeline is a drop-down list with multiple options including Events
View, Top-Down View, Bottom-Up View, and Flat View. All four of these views can
be used to view CPU IP / back trace sampling data.

Example of Event Sampling

   :alt: CPU Event Sampling in GUI
   :class: image

Event sampling samples hardware or software event counts during a collection and
then graphs those events as rates on the Timeline. The above screenshot shows
four hardware events. Core and cache events are graphed under the associated CPU
row (see the red box in the screenshot) while uncore and OS events are graphed
in their own row (see the green box in the screenshot). Hovering the cursor over
an event sampling row in the timeline shows the event's rate at that moment.
