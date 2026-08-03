---
source_path: UserGuide/topics/cli-start-command-switch-options.rst
title: #### CLI Start Command Switch Options
---
#### CLI Start Command Switch Options

After choosing the ``start`` command switch, the following options are available. Usage:

::

   nsys [global-options] start [options]

   :name: table_start_table
   :class: table-compact table-expandable


   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | Option                        | Available Parameters  | Switch Description                                                                                      |
   |                               | (default in bold)     |                                                                                                         |
   +===============================+=======================+=========================================================================================================+
   | ``--accelerator-trace``       | **none**,             | Collect other accelerators workload trace from the hardware engine units. Available in Nsight Systems Embedded Platforms Edition     |
   |                               | tegra-accelerators    | only. This option will also enable collection of hardware accelerator related ftrace events.            |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--after-collection-start``  | < command >           | Execute a command after the collection starts. The command will be reused for subsequent starts until   |
   |                               |                       | it is reset or cleared. Pass the option with no value to clear the previously set command. The executed |
   |                               |                       | process receives the following environment variables: ``NSYS_SESSION_NAME``, ``NSYS_CALLBACK_NAME``.    |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |    NSYS_SESSION_NAME   - the current session name                                                       |
   |                               |                       |    NSYS_CALLBACK_NAME  - the current callback name                                                      |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--after-report-ready``      | < command >           | Execute a command after the report is ready. The command is reused for subsequent stops until it is     |
   |                               |                       | reset or cleared. Pass the option with no value to clear the previously set command. The executed       |
   |                               |                       | process receives the following environment variables: ``NSYS_SESSION_NAME``, ``NSYS_CALLBACK_NAME``,    |
   |                               |                       | ``NSYS_REPORT_PATH``.                                                                                   |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |    NSYS_SESSION_NAME   - the current session name                                                       |
   |                               |                       |    NSYS_CALLBACK_NAME  - the current callback name                                                      |
   |                               |                       |    NSYS_REPORT_PATH    - the path to the generated report file                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--backtrace``               | auto, **fp**, lbr,    | Select the backtrace method to use while sampling. The option ``lbr`` uses Intel(c) Corporation's Last  |
   | or ``-b``                     | dwarf, none           | Branch Record registers, available only with Intel(c) CPUs codenamed Haswell and later. The option      |
   |                               |                       | ``fp`` is frame pointer and assumes that frame pointers were enabled during compilation                 |
   |                               |                       | (``-fno-omit-frame-pointer``). The option ``dwarf`` uses DWARF's CFI (Call Frame Information). Setting  |
   |                               |                       | the value to ``none`` can reduce collection overhead. Default is ``fp`` on Linux.                       |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--capture-range``           | **none**,             | When ``--capture-range`` is used, profiling will start only when an appropriate start API or hotkey is  |
   | or ``-c``                     | cudaProfilerApi,      | invoked. If ``--capture-range`` is set to none, start/stop API calls and hotkeys will be ignored.       |
   |                               | hotkey, nvtx          |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |     Hotkey works for graphic applications only.                                                         |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--capture-range-end``       | none, stop,           | Default is stop-shutdown. Specify the desired behavior when a capture range ends. Applicable only when  |
   |                               | **stop-shutdown**,    | used along with the ``--capture-range`` option. If ``none``, capture range end will be ignored. If      |
   |                               | repeat[:N][:mode],    | ``stop``, collection will stop at the capture range end. Any subsequent capture ranges will be ignored. |
   |                               | repeat-shutdown:N     | The target app will continue running. If ``stop-shutdown``, collection will stop at the capture range   |
   |                               | [:mode]               | end and session will be shutdown. If ``repeat[:N][:mode]``, collection will stop at capture range end   |
   |                               |                       | and subsequent capture ranges will trigger more collections. The optional ``:N`` specifies the max      |
   |                               |                       | number of capture ranges to be honored. Any subsequent capture ranges will be ignored once N capture    |
   |                               |                       | ranges are collected. The optional ``:mode`` specifies how result files are generated. Possible values  |
   |                               |                       | for mode are:                                                                                           |
   |                               |                       |                                                                                                         |
   |                               |                       | ``defer`` (default) -- Generate result files only after all capture ranges end, when the app exits, or  |
   |                               |                       | when Ctrl+C is pressed, whichever comes first.                                                          |
   |                               |                       |                                                                                                         |
   |                               |                       | ``sync`` -- Generate the result file immediately after each range and block the application thread      |
   |                               |                       | until complete.                                                                                         |
   |                               |                       |                                                                                                         |
   |                               |                       | ``async`` -- Generate the result file immediately after each range without blocking the application     |
   |                               |                       | thread.                                                                                                 |
   |                               |                       |                                                                                                         |
   |                               |                       | If ``repeat-shutdown:N[:mode]``, the same behavior as ``repeat:N[:mode]`` but session will be shutdown  |
   |                               |                       | after N ranges. For ``stop-shutdown`` and ``repeat-shutdown:N``, use the ``--kill`` option to specify   |
   |                               |                       | the signal to be sent to the target app when shutting down the session.                                 |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cpu-core-events``         | 0x11,0x13,...,        | Collect per-core PMU counters. Multiple values can be selected, separated by commas only (no spaces).   |
   | (Nsight Systems Embedded Platforms Edition)                | **none**              | Use the ``--cpu-core-events=help`` switch to see the full list of values.                               |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cpu-core-events``         | 'help' or the end     | Default is Instructions Retired. Select the CPU Core events to sample. Use the                          |
   | (not Nsight Systems Embedded Platforms Edition)            | users selected events | ``--cpu-core-events=help`` switch to see the full list of events and the number of events that can be   |
   |                               | in the format 'x,y',  | collected simultaneously. Multiple values can be selected, separated by commas only (no spaces). Use    |
   |                               | **2**                 | the ``--event-sample`` switch to enable.                                                                |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cpu-core-metrics``        | 0,1,2,..., **none**   | Collect metrics on the CPU core. Multiple values can be selected, separated by commas only (no spaces). |
   |                               |                       | Use the ``--cpu-core-metrics=help`` switch to see the full list of values.  Use the ``--event-sample``  |
   |                               |                       | switch to enable.                                                                                       |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |    Only available on NVIDIA Arm-based CPUs.                                                             |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cpu-metrics``             | 'help' or a comma     | Choose the CPU core events and metrics desired. Use name or alias. Not available on Nsight Systems Embedded Platforms Edition.       |
   |                               | separated list        |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cpu-socket-events``       | 0x2a,0x2c,...,        | Collect per-socket Uncore PMU counters. Multiple values can be selected, separated by commas only (no   |
   | (Nsight Systems Embedded Platforms Edition)                | **none**              | spaces). Use the ``--cpu-socket-events=help`` switch to see the full list of values. Available in       |
   |                               |                       | Nsight Systems Embedded Platforms Edition only.                                                                                      |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cpu-socket-events``       | 'help' or the users   | Select the Uncore CPU Socket events to sample. Use the ``--cpu-socket-events=help`` switch to see the   |
   | (not Nsight Systems Embedded Platforms Edition)            | selected events as    | full list of events and the number of events that can be collected simultaneously. Multiple values can  |
   |                               | 'x,y', **none**       | be selected, separated by commas only (no spaces). Use the ``--event-sample`` switch to enable.         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cpu-socket-metrics``      | 0,1,2,..., **none**   | Collect Uncore metrics on the CPU socket. Multiple values can be selected, separated by commas only (no |
   |                               |                       | spaces). Use the ``--cpu-socket-metrics=help`` switch to see the full list of values. Use the           |
   |                               |                       | ``--event-sample`` switch to enable.                                                                    |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |    Only available on NVIDIA Arm-based CPUs.                                                             |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cpuctxsw``                | **process-tree**,     | Trace OS thread scheduling activity. Select ``none`` to disable tracing CPU context switches.           |
   |                               | system-wide, none     | Depending on the platform, some values may require admin or root privileges.                            |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |   If the ``--sample`` switch is set to a value other than ``none``, the ``--cpuctxsw`` setting is       |
   |                               |                       |   hardcoded to the same value as the ``--sample``  switch. If ``--sample=none`` and a target            |
   |                               |                       |   application is launched, the default is ``process-tree``, otherwise the default is ``none``. Requires |
   |                               |                       |   ``--sampling-trigger=perf`` switch in Nsight Systems Embedded Platforms Edition                                                    |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--debug-symbols``           | <directory paths>     |  A list of directories with symbol files, separated by ``;`` on Windows or ``:`` on Linux and QNX.      |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--discard-environment``     | true, **false**       | When false, Nsight Systems will collect the environment variables of the launched process. When true,   |
   |                               |                       | the environment variables will not be collected.                                                        |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |   Available on Linux only.                                                                              |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--dts-api-port``            | integer, **9117**     | Specify the server port number when collecting NIC metrics using the DOCA Telemetry Service API.        |
   |                               |                       | Allowed only when ``--nic-metrics=hf-via-dts`` is set.                                                  |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--enable``                  | <plugin_name>         | Use the specified plugin. The option can be specified multiple times to enable multiple plugins.        |
   |                               |   [,arg1,arg2,...]    | Plugin arguments are separated by commas only (no spaces). On non-Windows platforms, commas can be      |
   |                               |                       | escaped with a backslash ``\\``, and the backslash itself can be escaped by another backslash ``\\\\``. |
   |                               |                       | On Windows, use the caret ``^`` as the escape character, and ``^^`` for a literal caret. To include     |
   |                               |                       | spaces in an argument, enclose the argument in double quotes ``"``. To list all available plugins,      |
   |                               |                       | use the ``nsys plugins list`` command.                                                                  |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--etw-provider``            | "<name>,<guid>", or   | Add custom ETW trace provider(s). If you want to specify more attributes than Name and GUID, provide a  |
   |                               | path to JSON file     | JSON configuration file as as outlined below. This switch can be used multiple times to add multiple    |
   |                               |                       | providers. Note: Only available for Windows targets.                                                    |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--event-sample``            | system-wide, **none** | Use the ``--cpu-core-events=help`` and the ``--os-events=help`` switches to see the full list of        |
   |                               |                       | events. If event sampling is enabled and no events are selected, the CPU Core event 'Instructions       |
   |                               |                       | Retired' is selected by default. Not available on Nsight Systems Embedded Platforms Edition.                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--event-sampling-interval`` | Integers from 1       | The interval between each event sample collection. Minimum event sampling interval is 1 mSec. Maximum   |
   |                               | to 1000 milliseconds, | event sampling interval is 1000 mSec. Not available in Nsight Systems Embedded Platforms Edition.                                    |
   |                               | **10**                |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--event-sampling``          | Time in milliseconds, | The interval sampling an event group before switching to the next group when using event multiplexing.  |
   | ``-multiplex-interval``       | **2000**              | is set with the ``--event-sampling-multiplex-interval`` option.                                         |
   |                               |                       | The minimum multiplexed event sampling interval is 250 mSec. Not available in Nsight Systems Embedded Platforms Edition.             |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--event-sampling-frequency``| N/A                   | WARNING: This switch is no longer supported. Please use the ``--event-sampling-interval`` switch        |
   |                               |                       | instead. Available on Linux only. Not available in Nsight Systems Embedded Platforms Edition.                                        |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--export``                  | arrow, arrowdir, hdf, | Create additional output file(s) based on the data collected. This option can be given more than once.  |
   |                               | jsonlines, sqlite,    |                                                                                                         |
   |                               | parquetdir, text,     | .. warning::                                                                                            |
   |                               | **none**              |   If the collection captures a large amount of data, creating the export file may take several          |
   |                               |                       |   minutes to complete.                                                                                  |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--flush-on``                | **true**, false       | If ``--flush-on-cudaprofilerstop`` is set to true, any call to ``cudaProfilerStop()`` will cause the    |
   | ``-cudaprofilerstop``         |                       | CUDA trace buffers to be flushed. Note that the CUDA trace buffers will be flushed when the collection  |
   |                               |                       | ends, regardless of the value of this switch.                                                           |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--force-overwrite``         | true, **false**       | If true, overwrite all existing result files with same output filename (.nsys-rep, .sqlite, .h5, .txt,  |
   | or ``-f``                     |                       | .jsonl, .arrows, _arwdir, _pqtdir).                                                                     |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--ftrace``                  |                       | Collect ftrace events. Argument should list events to collect as: subsystem1/event1,subsystem2/event2.  |
   |                               |                       | Requires root. No ftrace events are collected by default.                                               |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--ftrace-keep-user-config`` |                       | Skip initial ftrace setup and collect already configured events. Default resets the ftrace              |
   |                               |                       | configuration.                                                                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--gds-libs-path``           | < directory path >    | Specify a directory containing GDS (GPUDirect Storage) libraries (must contain libcufile.so). Use this  |
   |                               |                       | argument if the GDS libraries are located in a different path than the default. This argument is used   |
   |                               |                       | together with ``--gds-metrics``. This option is only supported on Linux x64 and SBSA targets.           |
   |                               |                       | Default is ``/usr/local/cuda/lib64``.                                                                   |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--gds-metrics``             | true, **false**       | When true, collect GDS (GPUDirect Storage) metrics. This option is only supported on Linux x64 and      |
   |                               |                       | SBSA targets.                                                                                           |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--gpu-metrics-devices``     | help, <id,...>,       | Collect GPU Metrics from specified devices. Possible values are ``none``, ``cuda-visible``, ``all``,    |
   |                               | all, cuda-visible,    | or a comma-separated list of GPU IDs reported by ``--gpu-metrics-devices=help``. Default is ``none``.   |
   |                               | **none**              |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--gpu-metrics-frequency``   | integer[,...],        | Specify GPU Metrics sampling frequency. Accepts a single value (assigned to all selected GPUs) or a     |
   |                               | **10000**             | comma-separated list with one value per GPU in the same order as ``--gpu-metrics-devices``.             |
   |                               |                       | Abbreviated suffixes ``k`` and ``M`` are accepted. Minimum supported frequency is 10 (Hz). Maximum      |
   |                               |                       | supported frequency is 200000 (Hz).                                                                     |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--gpu-metrics-set``         | help, alias[,...],    | Specify metric set for GPU Metrics. Accepts a single value (assigned to all selected GPUs) or a         |
   |                               | file:<file name>      | comma-separated list with one value per GPU in the same order as ``--gpu-metrics-devices``. The         |
   |                               |                       | argument must be one of the aliases reported by ``--gpu-metrics-set=help`` switch, or a path to a       |
   |                               |                       | metric config file prefixed by ``file:``. The default is the first metric set that supports all         |
   |                               |                       | selected GPUs.                                                                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--gpu-video-devices``       | help, <id1,id2,...>,  | Analyze video devices. ``--help`` gives a list of supported devices, reason for unsupported devices and |
   |                               | all, **none**         | IDs. ``<id1,id2,...>`` turns on the feature for the specified devices only.                             |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--gpuctxsw``                | true, **false**       | Trace GPU context switches. See the GPU Context Switch  topic for    |
   |                               |                       | details.                                                                                                |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--help``                    | <tag>, **none**       | Print the help message. The option can take one optional argument that will be used as a tag. If a tag  |
   |                               |                       | is provided, only options relevant to the tag will be printed.                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--ib-net-info-devices``     | <NIC names>, **none** | A comma-separated list of NIC names. The NICs which ``ibdiagnet`` will use for networks discovery. This |
   |                               |                       | option creates the ibdiagnet files to be used for collecting network information. Example value:        |
   |                               |                       | ``mlx5_0,mlx5_1``. If the ``--ib-net-info-output`` option is set then Nsight Systems will store the     |
   |                               |                       | network information at that path. Otherwise it will be created at a temporary path and will be          |
   |                               |                       | discarded after processing. If more than one NIC was specified, only the last network information file  |
   |                               |                       | will be saved. Note that this option should not be used together with the ``--ib-net-info-files``       |
   |                               |                       | option.                                                                                                 |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--ib-net-info-files``       | <file paths>,         | A comma-separated list of file paths. Paths of an existing ibdiagnet db_csv files, containing networks  |
   |                               | **none**              | information data. Nsight Systems will read the networks' information from these files. Don't use ``~``  |
   |                               |                       | alias within the path. Note that this option should not be used together with the                       |
   |                               |                       | ``--ib-net-info-devices`` option.                                                                       |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--ib-net-info-output``      | <directory path>,     | Sets the path of a directory into which ibdiagnet network discovery data will be written. Use this      |
   |                               | **none**              | option together with the ``--ib-net-info-devices`` option. Don't use ``~`` alias within the path.       |
   +-------------------------------+-----------------------+---------+-----------------------------------------------------------------------------------------------+
   | ``--ib-switch-congestion``    | <IB switch GUIDs>,    | The ``--ib-switch-congestion-devices`` switch takes a comma-separated list of InfiniBand switch GUIDs.  |
   | ``-devices``                  | **none**              | Collect InfiniBand switch congestion events from switches identified by the specified GUIDs. This       |
   |                               |                       | option can be used multiple times. System scope. Use the ``--ib-switch-congestion-nic-device``,         |
   |                               |                       | ``--ib-switch-congestion-percent``, and ``--ib-switch-congestion-threshold-high`` switches to further   |
   |                               |                       | control how congestion events are collected.                                                            |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--ib-switch-congestion``    | <NIC name>            | ``--ib-switch-congestion-nic-device`` gives the name of the NIC (HCA) through which InfiniBand switches |
   | ``-nic-device``               |                       | will be accessed. By default, the first active NIC will be used. One way to find a NIC's name is via    |
   |                               |                       | the ``ibnetdiscover --Hca_list | grep"$(hostname)"`` command.                                           |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--ib-switch-congestion``    | 1 <= integer <= 100,  | Set the percent of InfiniBand switch congestion events to be collected using the                        |
   | ``-percent``                  | **50**                | ``--ib-switch-congestion-percent`` option. This option enables reducing the network bandwidth consumed  |
   |                               |                       | by reporting congestion events.                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--ib-switch-congestion``    | 1 < integer <= 1023,  | The ``--ib-switch-congestion-threshold-high`` option sets the high threshold percentage for InfiniBand  |
   | ``-threshold-high``           | **75**                | switch egress port buffer size. Before a packet leaves an InfiniBand switch, it is stored at an egress  |
   |                               |                       | port buffer. The buffer's size is checked and if it exceeds the given threshold percentage, a           |
   |                               |                       | congestion event is reported. The percentage can be greater than 100.                                   |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--ib-switch-metrics``       | <IB switch GUIDs>     | Add comma-separated list of InfiniBand switch GUIDs by using the ``--ib-switch-metrics-devices``.       |
   | ``-devices``                  |                       | Collect metrics from the specified InfiniBand switches. This switch can be used multiple times. System  |
   |                               |                       | scope.                                                                                                  |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--ib-switch-metrics-nic``   | <NIC name>            | ``--ib-switch-metrics-nic-device`` gives the name of the NIC (HCA) through which InfiniBand switches    |
   | ``-device``                   |                       | will be accessed for performance metrics. By default, the first active NIC will be used. One way to     |
   |                               |                       | find a NIC's name is via the ``ibstat -l`` command.                                                     |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--isr``                     | true, **false**       | Trace Interrupt Service Routines (ISRs) and Deferred Procedure Calls (DPCs). Requires administrative    |
   |                               |                       | privileges. Available only on Windows devices.                                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--nic-metrics``             | lf, hf, hf-via-dts,   | Collect metrics from NIC/HCA devices. The 'hf' option collects high frequency metrics but lacks RoCE,   |
   |                               | **none**              | IPoIB, and 'Send Waits' metrics. The 'hf' option requires elevated user privileges. The 'hf-via-dts'    |
   |                               |                       | option collects high frequency metrics using the DOCA Telemetry Service (DTS) API and does not require  |
   |                               |                       | elevated privileges. The 'lf' option collects all available metrics but at a lower sampling frequency.  |
   |                               |                       | The deprecated 'true' option is accepted for backwards compatibility and corresponds to 'lf'. The       |
   |                               |                       | 'true' option will be removed in a future release. System scope. Not available on Nsight Systems Embedded Platforms Edition.         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--os-events``               | 'help' or the end     | Select the OS events to sample. Use the ``--os-events=help`` switch to see the full list of events.     |
   |                               | users selected events | Multiple values can be selected, separated by commas only (no spaces). Use the ``--event-sample``       |
   |                               | in the format 'x,y'   | switch to enable. Not available on Nsight Systems Embedded Platforms Edition.                                                        |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--output`` or ``-o``        | < filename >,         | Set the report file name. Any ``%q{ENV_VAR}`` pattern in the filename will be substituted with the      |
   |                               | **report#**           | value of the environment variable. Any ``%h`` pattern in the filename will be substituted with the      |
   |                               |                       | hostname of the system. Any ``%p`` pattern in the filename will be substituted with the PID of the      |
   |                               |                       | target process or the PID of the root process if there is a process tree. Any ``%%`` pattern in the     |
   |                               |                       | filename will be substituted with ``%``. Default is report#{.nsys-rep,.sqlite,.h5,.txt,.arrows,         |
   |                               |                       | _arwdir,_pqtdir,.jsonl}  in the working directory.                                                      |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--process-scope``           | **main**, system-wide | Select which process(es) to trace. Available in Nsight Systems Embedded Platforms Edition only. Nsight Systems Workstation Edition will always       |
   |                               | process-tree,         | trace system-wide in this version of the tool.                                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--reflex-events``           | true, **false**       | Collect Reflex SDK ETW events. Available only on Windows.                                               |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--retain-etw-files``        | true, **false**       | Retain ETW files generated by the trace, merge and move the files to the output directory.              |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--sample``                  | **process-tree**,     | Select how to collect CPU IP/backtrace samples. If ``none`` is selected, CPU sampling is disabled.      |
   | or ``-s``                     | system-wide, xhv,     | Depending on the platform, some values may require admin or root privileges. Select``xhv`` or           |
   |                               | xhv-system-wide, none | ``xhv-system-wide`` to enable Cross-Hypervisor (XHV) sampling, requires root privileges. If a target    |
   |                               |                       | application is launched, the default is ``process-tree``; otherwise, the default is ``none``.           |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |   ``system-wide`` is not available on all platforms.                                                    |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |   If set to ``none``, CPU context switch data will still be                                             |
   |                               |                       |   collected unless the ``--cpuctxsw`` switch is set to ``none``.                                        |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--samples-per-backtrace``   | integer <= 32,        | The number of CPU IP samples collected for every CPU IP/backtrace sample collected. For example,        |
   |                               | **1**                 | if set to 4, on the fourth CPU IP sample collected, a backtrace will also be collected. Lower           |
   |                               |                       | values increase the amount of data collected. Higher values can reduce collection overhead and          |
   |                               |                       | reduce the number of CPU IP samples dropped. If DWARF backtraces are collected, the default is 4,       |
   |                               |                       | otherwise the default is 1. This option is not available on Nsight Systems Embedded Platforms Edition or on non-Linux targets.       |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--sampling-frequency``      | 100 < integers < 8000,| Specify the sampling/backtracing frequency. The minimum supported frequency is 100 Hz. The maximum      |
   |                               | **1000**              | supported frequency is 8000 Hz. This option is supported only on QNX, Linux for Tegra, and Windows      |
   |                               |                       | targets.                                                                                                |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--sampling-period``         | integer               | Default is determined dynamically. The number of CPU Cycle events counted before a CPU instruction      |
   | (Nsight Systems Embedded Platforms Edition)                |                       | pointer (IP) sample is collected. If configured, backtraces may also be collected. The smaller the      |
   |                               |                       | sampling period, the higher the sampling rate. Note that smaller sampling periods will increase         |
   |                               |                       | overhead and significantly increase the size of the result file(s). Requires the                        |
   |                               |                       | ``--sampling-trigger=perf`` switch.                                                                     |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--sampling-period``         | integer               | Default is determined dynamically. The number of events counted before a CPU instruction pointer (IP)   |
   | (not Nsight Systems Embedded Platforms Edition)            |                       | sample is collected. The event used to trigger the collection of a sample is determined dynamically.    |
   |                               |                       | For example, on Intel based platforms, it will probably be "Reference Cycles" and on AMD platforms,     |
   |                               |                       | "CPU Cycles". If configured, backtraces may also be collected. The smaller the sampling period, the .   |
   |                               |                       | higher the sampling rate Note that smaller sampling periods will increase overhead and significantly    |
   |                               |                       | increase the size of the result file(s). This option is available only on Linux targets.                |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--sampling-trigger``        | **timer**, **sched**, | Specify backtrace collection trigger. Multiple APIs can be selected, separated by commas only           |
   |                               | perf, cuda            | (no spaces). Available on Nsight Systems Embedded Platforms Edition targets only.                                                    |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--session``                 | session identifier,   | Start the collection in the indicated session. The option argument must represent a valid session name  |
   |                               | **none**              | or ID as reported by ``nsys sessions list``. Any ``%q{ENV_VAR}`` pattern will be substituted with the   |
   |                               |                       | value of the environment variable. Any ``%h`` pattern will be substituted with the hostname of the      |
   |                               |                       | system. Any ``%%`` pattern will be substituted with ``%``.                                              |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--session-new``             | [a-Z][0-9,a-Z,spaces] | Default is profile-<id>-<application>. Name the session created by the command. Name must start with an |
   |                               |                       | alphabetical character followed by printable or space characters. Any ``%q{ENV_VAR}`` pattern will be   |
   |                               |                       | substituted with the value of the environment variable. Any ``%h`` pattern will be substituted with the |
   |                               |                       | hostname of the system. Any ``%%`` pattern will be substituted with ``%``.                              |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--show-source-info``        | **true**, false       | Show source file and line information, when available, for CPU sampling, CUDA API, OS runtime, and      |
   |                               |                       | Python backtraces. This option is supported on Linux targets and can increase report generation time.   |
   |                               |                       | Set to ``false`` to reduce report generation time.                                                      |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--soc-metrics``             | true, **false**       | Collect SoC Metrics. Available in Nsight Systems Embedded Platforms Edition only.                                                    |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--soc-metrics-frequency``   | integer,              | Specify SoC Metrics sampling frequency. Minimum supported frequency is '100' (Hz). Maximum supported    |
   |                               | **10000**             | frequency is '1000000' (Hz). Available in Nsight Systems Embedded Platforms Edition only.                                            |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--soc-metrics-set``         | alias,                | Specify metric set for SoC Metrics. The argument must be one of the aliases reported by                 |
   |                               | file:<file name>      | ``--soc-metrics-set=help`` switch, or a path to a metric config file prefixed by ``file:``.             |
   |                               |                       | Available in Nsight Systems Embedded Platforms Edition only.                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--stats``                   | true, **false**       | Generate summary statistics after the collection.                                                       |
   |                               |                       |                                                                                                         |
   |                               |                       | .. warning::                                                                                            |
   |                               |                       |    When set to true, an SQLite database will be created after the collection. If the collection         |
   |                               |                       |    captures a large amount of data, creating the  database file may take several minutes to complete.   |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--stop-on-exit`` or ``-x``  | **true**, false       | If true, stop collecting automatically when the launched process has exited or when the duration        |
   |                               |                       | expires - whichever occurs first. If false, duration must be set and the collection stops only when     |
   |                               |                       | the duration expires. Nsight Systems does not officially support runs longer than 5 minutes.            |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--storage-metrics``         |                       | Collect throughput and operations metrics from storage devices. See:                                    |
   |                               |                       | Network Storage Profiling<network-storage-profiling>                                             |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--syscall`` (beta)          | process-tree,         | Collect system calls. The value defines the collection scope: ``process-tree`` makes it tracing the     |
   |                               | pid-namespace,        | application processes only, ``pid-namespace`` - all processes in the current PID namespace and its      |
   |                               | **none**              | child namespaces (similar to the ``system-wide`` mode of other features).                               |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--vsync``                   | true, **false**       | Collect vsync events. If collection of vsync events is enabled, display/display_scanline ftrace         |
   |                               |                       | events will also be captured. Available in Nsight Systems Embedded Platforms Edition only.                                           |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--xhv-trace``               | < filepath pct.json > | Collect hypervisor trace. Available in Nsight Systems Embedded Platforms Edition only.                                               |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--xhv-trace-events``        | **all**, none, core,  | Available in Nsight Systems Embedded Platforms Edition only.                                                                         |
   |                               | sched, irq, trap      |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--xhv-vm-symbols``          | <filepath             | XHV sampling config file. Available in Nsight Systems Embedded Platforms Edition only.                                               |
   |                               | kernel_symbols.json>  |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
