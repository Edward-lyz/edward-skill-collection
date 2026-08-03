---
source_path: UserGuide/topics/time-synchronization.rst
title: #### Time Synchronization
---
#### Time Synchronization

When multiple reports are loaded into a single timeline, timestamps between them
need to be adjusted, such that events that happened at the same time appear to
be aligned.

Nsight Systems can automatically adjust timestamps based on **UTC time**
recorded around the collection start time. This method is used by default when
other more precise methods are not available. This time can be seen as ``UTC
time at t=0`` in the *Analysis Summary* page of the report file. Refer to your
OS documentation to learn how to sync the software clock using the Network Time
Protocol (NTP). NTP-based time synchronization is not very precise, with the
typical errors on the scale of one to tens of milliseconds.

Reports collected on the same physical machine can use synchronization based on
**Timestamp Counter (TSC) values**. These are platform-specific counters,
typically accessed in user space applications using the RDTSC instruction on
x86_64 architecture, or by reading the CNTVCT register on Arm64. Their values
converted to nanoseconds can be seen as ``TSC value at t=0`` in the *Analysis
Summary* page of the report file. Reports synchronized using TSC values can be
aligned with nanoseconds-level precision.

TSC-based time synchronization is activated automatically, when Nsight Systems
detects that reports come from same target and that the same TSC value
corresponds to very close UTC times. Targets are considered to be the same when
either explicitly set environment variables ``NSYS_HW_ID`` are the same for both
reports or when target hostnames are the same and ``NSYS_HW_ID`` is not set for
either target. The difference between UTC and TSC time offsets must be below 1
second to choose TSC-based time synchronization.

To find out which synchronization method was used, navigate to the *Analysis
Summary* tab of an added report and check the ``Report alignment source``
property of a target. Note, that the first report won’t have this parameter.

   :alt: TODO
   :class: image

   :alt: TODO
   :class: image

When loading multiple reports into a single timeline, it is always advisable to
first check that time synchronization looks correct, by zooming into
synchronization or communication events that are expected to be aligned.


### vClock Plugin

When high-precision system-clock synchronization (such as PTP) is unavailable, the vClock
plugin can improve cross-system report alignment. It correlates timestamps in
profiling report files collected on different systems by measuring relative offsets between
system clocks without changing them. vClock targets clock-correlation error on
the order of tens of microseconds without requiring special operating system
privileges. Correlation accuracy is affected by network quality between vClock
providers.

The vClock plugin is available on the x86_64 and aarch64 Linux targets.

Note:

   The vClock plugin is experimental and is subject to change in future
   releases.

The plugin operates in two modes:

- A **provider** runs independently on each system and exchanges clock
  measurements with providers running on other systems.
- A **consumer** is started by Nsight Systems during profiling. It connects to
  the provider on the same system and records vClock correlation data in the
  report.

**Set up the providers**

Before profiling, start a vClock provider on each host whose profiling report will be
aligned, listing the other hosts as peers:


   <nsys-target-dir>/plugins/vclock/vclock_plugin --peers <peer-ip>[,<peer-ip>,...]

The providers exchange clock measurements while they run. Leave them running
until all profiling sessions are complete.

The providers communicate over UDP. Ensure that each provider's listening port
is reachable from its peers. Use ``--port`` to select the listening port.

After all providers are running, allow at least one second for them to exchange
initial clock measurements. 

**Collect vClock correlation data during profiling**

Enable the vClock plugin while profiling each application:


   nsys profile --enable "vclock" <application>

Supported arguments are:

   :name: table_vclock_plugin_arguments
   :class: table-compact
   :header-rows: 1
   :widths: 18 22 20 25 55

   * - Option
     - Mode
     - Parameter
     - Default
     - Description
   * - ``--peers``
     - Provider
     - ``HOST[:PORT],...``
     -
     - Required. Comma-separated addresses of peer providers.
       If a peer port is omitted, the local ``--port`` value is used.
   * - ``--listen``
     - Provider
     - ``IP``
     - ``0.0.0.0``
     - Local IPv4 address on which the provider listens.
   * - ``--port``
     - Provider
     - ``PORT``
     - ``54805``
     - UDP port on which the provider listens.
   * - ``--domain-id``
     - Provider and consumer
     - ``UUID``
     - Default vClock domain UUID
     - Shared correlation domain UUID. All participating providers and
       consumers must use the same UUID.
   * - ``--socket-dir``
     - Provider and consumer
     - ``DIR``
     - ``$NSYS_TMPDIR/nvidia/vclock``, or ``/tmp/nvidia/vclock`` when
       ``NSYS_TMPDIR`` is not set
     - Directory for the vClock Unix domain sockets. The consumer and the
       provider it connects to must use the same directory.
   * - ``--help``
## -
     -
     - Show the help message.

For general information about plugin discovery and argument syntax, refer to
Nsight Systems Plugins.

**View synchronized reports**

When reports contain vClock correlation data for the same domain, the GUI
multi-report view automatically aligns them by vClock. When vClock is selected
for report alignment, the ``Report alignment source`` property on the
*Analysis Summary* page shows ``VCLOCK``.

**Export vClock timestamps**

To export event timestamps in the report's vClock time domain, use the
``--ts-normalize`` option:


   nsys export --ts-normalize=true <report>.nsys-rep
