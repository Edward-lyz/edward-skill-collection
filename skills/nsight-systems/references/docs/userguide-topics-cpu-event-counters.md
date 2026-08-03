---
source_path: UserGuide/topics/cpu-event-counters.rst
title: ## CPU Events and Metrics
---
## CPU Events and Metrics

#### Core Events and Metrics

Nsight Systems can access and make available information about activities on the
CPU. What exact data is available varies by the CPU and by the architecture.

   :name: table_coreeventcounters_table
   :class: table-compact

   +----------------------------+-----------+---------------------+------------+----------+---------------------------+
   | nsys profile/start command | Grace CPU | Future NVIDIA CPUs  | Intel CPUs | AMD CPUs | Non-NVIDIA Arm-based CPUs |
   +============================+===========+=====================+============+==========+===========================+
   | ``--cpu-core-events``      | full      | n/a                 | extended   | basic    | basic                     |
   +----------------------------+-----------+---------------------+------------+----------+---------------------------+
   | ``--cpu-core-metrics``     | full      | n/a                 | n/a        | n/a      | n/a                       |
   +----------------------------+-----------+---------------------+------------+----------+---------------------------+
   | ``--cpu-metrics`` (new)    | full      | full                | extended   | basic    | basic                     |
   +----------------------------+-----------+---------------------+------------+----------+---------------------------+

Events Support:

-  basic - only standard perf_event_open architecture-independent CPU core events
-  extended - basic + a few common architecture-specific CPU core events
-  full - basic + some architecture-specific CPU core events

Metrics Support:

-  full - metrics derived from architecture-specific CPU core events

The ``--cpu-metrics=help`` command will print grammar describing how to list
supported core events and metrics for your CPU.
The selected events and metrics can be fed into the ``--cpu-metrics`` switch by
name or by alias.

Future versions of Nsight Systems will provide full event and metric support for
other x86 and Arm architectures.

#### Uncore Events and Metrics

Nsight Systems can access and make available information about activities on the
CPU uncore/SoC. What exact data is available varies by SoC.

   :name: table_uncoreeventcounters_table
   :class: table-compact

   +----------------------------+-----------+---------------------+
   | nsys profile/start command | Grace CPU | Future NVIDIA CPUs  |
   +============================+===========+=====================+
   | ``--cpu-socket-events``    | yes       | no                  |
   +----------------------------+-----------+---------------------+
   | ``--cpu-socket-metrics``   | yes       | no                  |
   +----------------------------+-----------+---------------------+
   | ``--cpu-metrics`` (new)    | yes       | yes                 |
   +----------------------------+-----------+---------------------+

The ``--cpu-metrics=help`` command will print grammar describing how to list
supported uncore events, event filters, and metrics for your SoC.
The selected events (with/without filters) and metrics can be fed into the
``--cpu-metrics`` switch by name or by alias.


#### Event Multiplexing

There are hardware limitations on how many CPU counters can be collected at one
time. If you need to collect more counters than are available, you can either
perform multiple runs (as in the Arm Topdown methodology below) or you can take
advantage of Nsight Systems's support for event multiplexing.

To multiplex events, you need to define event groups. An event group can be
defined in any of the following switches: ``--cpu-metrics``, ``--os-events``,
``--cpu-core-events``, ``--cpu-core-metrics``, ``--cpu-socket-events``,
or ``--cpu-socket-metrics``.

One new switch is added to support this feature but is not required. It is
``--event-sampling-multiplex-interval``. If this switch is not set, the
default interval is 2000 ms (i.e. 2 seconds). This switch defines when event
group scheduling changes are made. The minimum
``--event-sampling-multiplex-interval`` is 250ms.

An event group is a group of events to be sampled concurrently. Use the '%'
delimiter to define an event group. For example;


   --cpu-core-events=1,2,3%4,5,6

In this case, Nsight Systems will sample events 1,2, and 3 for 2 seconds, then
switch the events 4,5, and 6 for 2 seconds, then switch back to events 1,2, and
3, etc. assuming the ``--event-sampling-multiplex-interval`` switch was not set.


   nsys profile --os-events %3,2%% --cpu-socket-metrics 6,11%%14,15%
   --cpu-core-events %%67,68%64,65,85,77,81 --event-sample system-wide
   --event-sampling-interval 100 --event-sampling-multiplex-interval 500
   --cpuctxsw system-wide -s none -t none -o five ../../ClockBenchmark

In this case, the following event groups were defined by the command line
switches. The event groups were switched every 500ms. So, after 2 seconds, all
of the events have been sampled and nsys reschedules group 0 to be sampled again.

*  group 0 - events used by socket-metrics 6 and 11
*  group 1 - os events 2 and 3
*  group 2 - events used by socket-metrics 14 and 15, core events 67 and 68
*  group 3 - core events 64,65,85,77, and 81

There is no limit to the number of event groups that can be defined. If an event
group is empty, the command line will return an error. The events defined for an
event group must fit in the available hardware PMUs as documented by the
individual event switch help output. There is no limit on the number of
concurrent os events.

      :alt: Timeline with multiplexed event counters.
      :class: image

The new ``--cpu-metrics`` switch also supports event multiplexing using the same
syntax. For example, the following command line defines two event groups, each
collecting 2 core metrics and 1 uncore metric, using the default event sampling
interval and a multiplex interval set to 250 ms:


   nsys profile --cpu-metrics branch_mpki,branch_misprediction_ratio,
   PCIe_RP_read_bandwidth%l1d_tlb_mpki,l1d_tlb_miss_ratio,
   PCIe_RP_write_bandwidth --event-sample system-wide
   --event-sampling-multiplex-interval 250 . . .


#### Arm Topdown Analysis

Arm Topdown methodology supports performance analysis, workload characterization,
and microarchitecture exploration. You can find details on the technique at
`Arm Topdown Methodology
<https://developer.arm.com/documentation/109542/0100/Arm-Topdown-methodology>`__.


Nsight Systems provides scripting to support running this analysis for the Grace
(TM) and DGX Spark (TM) systems.

In your target-linux-sbsa-armv8/CpuProfiling directory, look for a script named
``collect_cpu_topdown.sh``. This script simplifies collecting all PMU core
event and metric data needed to perform a traditional CPU Topdown analysis of
the workload's CPU performance.

The script runs multiple system-wide ``nsys profile`` commands sequentially to
collect the data. You can add additional Nsight Systems options to the command
line as per usual, with the following exceptions:

*  ``--event-sample``, ``--event-sampling-interval``, ``--cpu-core-events``, and
   ``--cpu-core-metrics`` switches are set by the script for Topdown analysis.
*  ``-f``, ``--force-overwrite`` switch is set to true by the script
*  ``-o``, ``--output`` switch is set by the script to generate a list of
   predefined output nsys-rep files.
*  ``--kill`` switch is set to the default value of ``sigterm``

If an application is to be launched by the script, place a ``--`` between the nsys
switches and the application command line.

Example command line:


   collect_cpu_topdown.sh --trace=osrt,nvtx,cuda -- myApp arg1 arg2

Output files will be written to the current working directory. The output
consists of a collection of .nsys-rep files that contain the metric data
required to do a Topdown analysis of the workload. These files can be opened
in the Nsight Systems GUI to view the metric results on the timeline.

You can futher use the NVTX CPU Topdown recipe
(``nsys recipe nvtx_cpu_topdown --input .``) that will process the data from
the .nsys-rep files and generate an output with CPU Topdown Methodology metrics
computed for NVTX ranges. For details and use cases of this recipe, see
nvtx_cpu_topdown Recipe.

Note:

   Arm Topdown analysis requires multiple system-wide collections and may take
   a significantly long time to run and post-process.

## Common Issues

-  **Reducing Overhead Caused By Sampling**

   There are several ways to reduce overhead caused by sampling.

   -  Disable sampling (i.e., use the ``--sampling=none`` switch).
   -  Increase the sampling period (i.e., reduce the sampling rate) using the
      ``--sampling-period`` switch.
   -  Stop collecting backtraces (i.e., use the ``--backtrace=none`` switch) or
      collect more efficient backtraces - if available, use the
      ``--backtrace=lbr`` switch.
   -  reduce the number of backtraces collected per sample. See documentation
      for the ``--samples-per-backtrace`` switch.

-  **Throttling**

   The Linux operating system enforces a maximum time to handle sampling
   interrupts. This means that if collecting samples takes more than a specified
   amount of time, the OS will throttle (i.e., slow down) the sampling rate to
   prevent the perf subsystem from causing too much overhead. When this occurs,
   sampling data may become irregular even though the thread is very busy.

      :alt: Throttling see in GUI
      :class: image

   The above screenshot shows a case where CPU IP / backtrace sampling was
   throttled during a collection. Note the irregular intervals of sampling
   tickmarks on the thread timeline. The number of times a collection throttled
   is provided in the Nsight Systems GUI's Diagnostics messages. If a collection
   throttles frequently (e.g., 1000s of times), increasing the sampling period
   should help reduce throttling.

Note:

      When throttling occurs, the OS sets a new (lower) maximum sampling rate in
      the procfs. This value must be reset before the sampling rate can be
      increased again. Use the following command to reset the OS' max sampling
      rate ``echo '100000' | sudo tee /proc/sys/kernel/perf_event_max_sample_rate``

-  **Sample intervals are irregular**

   My samples are not periodic - why? My samples are clumped up - why? There are
   gaps in between the samples - why? Likely reasons:

   -  Throttling, as described above.
   -  The paranoid level is set to 2. If the paranoid level is set to 2, anytime
      the workload makes a system call and spends time executing kernel mode
      code, samples will not be collected and there will be gaps in the sampling
      data.
   -  The sampling trigger itself is not periodic. If the trigger event is not
      periodic, for example, the Instructions Retired. event, sample collection
      will primarily occur when cache misses are occurring.

-  **No CPU profiling data is collected**

   There are a few common issues that cause CPU profiling data to not be collected:

   -  System requirements are not met. Check your system settings with the
      ``nsys status --environment`` command and see the System Requirements
      section above.
   -  I profiled my workload in a Docker container but no sampling data was
      collected. By default, Docker containers prevent the perf_event_open
      syscall from being utilized. To override this behavior, launch the Docker
      with the ``--privileged`` switch or modify the Docker's
      ``seccomp`` settings.
   -  I profiled my workload in a Docker container running Ubuntu 20+ running on
      top of a host system running CentOS with a kernel version < 3.10.0-693.
      The ``nsys status --environment`` command indicated that CPU profiling was
      supported. The host OS kernel version determines if CPU profiling is
      allowed and a CentOS host with a version < 3.10.0-693 is too old. In this
      case, the ``nsys status --environment`` command is incorrect.
