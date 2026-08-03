---
source_path: UserGuide/topics/cli-profile-command-switch-options.rst
title: #### CLI Profile Command Switch Options
---
#### CLI Profile Command Switch Options

After choosing the ``profile`` command switch, the following options are available. Usage:

::

   nsys [global-options] profile [options] [application] [application-arguments]


   :name: table_profile_table
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
   | ``--auto-report-name``        | true, **false**       | Derive report file name from collected data using details of the profiled graphics application. Format: |
   |                               |                       | ``[Process Name][GPU Name][Window Resolution][Graphics API] Timestamp .nsys-rep``. If true,             |
   |                               |                       | automatically generate report file names.                                                               |
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
   | ``--command-file``            | < filename >,         | Open a file that contains profile switches and parse the switches. Note additional switches on the      |
   |                               | **none**              | command line will override switches in the file. This flag can be specified more than once.             |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cpu-cluster-events``      | 0x16, 0x17, ...,      | Collect per-cluster Uncore PMU counters. Multiple values can be selected, separated by commas only (no  |
   |                               | **none**              | spaces). Use the ``--cpu-cluster-events=help`` switch to see the full list of values. Available in      |
   |                               |                       | Nsight Systems Embedded Platforms Edition only.                                                                                      |
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
   | ``--cuda-event-trace``        | auto, true, **false** | Trace CUDA Event completion on the device side, and get better correlation support among CUDA Event     |
   |                               |                       | APIs. Applicable only when CUDA tracing is enabled. "CUDA Event" refers to the synchronization          |
   |                               |                       | mechanism (cudaEventRecord, cudaStreamWaitEvent etc.). Enabling this feature may increase runtime       |
   |                               |                       | overhead and the likelihood of false dependencies across CUDA Streams, similar to CUDA Event's timing   |
   |                               |                       | functionality when cudaEventDisableTiming is not disabled. ``auto`` will automatically turn off the     |
   |                               |                       | trace if a target process has ``CUDA_DEVICE_MAX_CONNECTIONS`` set to 1.                                 |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cuda-flush-interval``     | milliseconds          | Set the interval when buffered CUDA data is automatically saved to storage in milliseconds. The CUDA    |
   |                               |                       | data buffer saves may cause profiler overhead. Buffer save behavior can be controlled with this switch. |
   |                               |                       | If the CUDA flush interval is set to 0 on systems running CUDA 11.0 or newer, buffers are saved when    |
   |                               |                       | they fill. If a flush interval is set to a non-zero value on such systems, buffers are saved only when  |
   |                               |                       | the flush interval expires. If a flush interval is set and the profiler runs out of available buffers   |
   |                               |                       | before the flush interval expires, additional buffers will be allocated as needed. In this case,        |
   |                               |                       | setting a flush interval can reduce buffer save overhead but increase memory use by the profiler. If    |
   |                               |                       | the flush interval is set to 0 on systems running older versions of CUDA, buffers are saved at the end  |
   |                               |                       | of the collection. If the profiler runs out of available buffers, additional buffers are allocated as   |
   |                               |                       | needed. If a flush interval is set to a non-zero value on such systems, buffers are saved when the      |
   |                               |                       | flush interval expires. A ``cuCtxSynchronize`` call may be inserted into the workflow before the        |
   |                               |                       | buffers are saved which will cause application overhead. In this case, setting a flush interval can     |
   |                               |                       | reduce memory use by the profiler but may increase save overhead. For collections over 30 seconds, an   |
   |                               |                       | interval of 10 seconds is recommended. Default is 10000 for Nsight Systems Embedded Platforms Edition and 0 otherwise.               |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cuda-graph-trace``        | ``graph``, ``node``   | Set the CUDA graph trace granularity, launch origin, and NVTX projection mode. Syntax:                  |
   |                               |                       | ``<granularity>[:<launch origin>][:<nvtx mode>]``. Applicable only when CUDA tracing is enabled.        |
   |                               | ``host-only``,        | Optional modifiers can appear in any order after the granularity.                                       |
   |                               | ``host-and-device``   | Use ``graph`` to trace whole CUDA graphs without node activities. This reduces overhead, requires CUDA  |
   |                               |                       | driver version 11.7 or higher, and is the default when available.                                       |
   |                               | ``nvtx-live``,        | Use ``node`` to collect node activities instead of whole-graph traces. This may cause significant       |
   |                               |                       | runtime overhead.                                                                                       |
   |                               | ``nvtx-precapture``   | Use ``host-only`` to trace CUDA graphs launched from host code only. Use ``host-and-device`` to also    |
   |                               |                       | trace CUDA graphs launched from device code.                                                            |
   |                               |                       | For ``graph``, ``host-and-device`` requires CUDA driver version 12.3 or higher and is the default when  |
   |                               |                       | available. For ``node``, ``host-and-device`` requires hardware trace with CUDA driver version 13.0 or   |
   |                               |                       | higher, and ``--trace=cuda`` without ``--trace=cuda-sw``.                                               |
   |                               |                       | Use ``nvtx-live`` to project NVTX for graphs constructed while profiling is active. This is the default |
   |                               |                       | and adds no overhead.                                                                                   |
   |                               |                       | Use ``nvtx-precapture`` to record CUDA API and NVTX events during graph construction before profiling   |
   |                               |                       | starts, enabling NVTX projection for graphs built before collection begins. This is experimental, adds  |
   |                               |                       | graph-construction overhead and memory use, and requires ``node``, CUDA tracing, and NVTX tracing. See  |
   |                               |                       | CUDA Graph Trace.                                                                                |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cuda-memory-usage``       | true, **false**       | Track the GPU memory usage by CUDA kernels. Applicable only when CUDA tracing is enabled.               |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |    This feature may cause significant runtime overhead.                                                 |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cuda-trace-all-apis``     | true, **false**       | By default, Nsight Systems skips CUDA APIs that are not critical for performance analysis. If enabled,  |
   |                               |                       | Nsight Systems will trace all CUDA APIs, including those less relevant to performance analysis.         |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |    This feature may cause significant runtime overhead.                                                 |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cuda-trace-scope``        | **process-tree**,     | Select ``process-tree`` to trace CUDA activities for the target process and its child processes. Select |
   |                               | system-wide           | ``system-wide`` to trace CUDA activities for all processes on the system.                               |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |    Only CUDA processes launched by the same user after the collection start will be traced.             |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cuda-um-cpu-page-faults`` | true, **false**       | This switch tracks the page faults that occur when CPU code tries to access a memory page that resides  |
   |                               |                       | on the device. Note that this feature may cause significant runtime overhead.                           |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cuda-um-gpu-page-faults`` | true, **false**       | This switch tracks the page faults that occur when GPU code tries to access a memory page that resides  |
   |                               |                       | on the host. Note that this feature may cause significant runtime overhead.                             |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--cudabacktrace``           | all, **none**,        | When tracing CUDA APIs, enable the collection of a backtrace when a CUDA API is invoked. Significant    |
   |                               | kernel, memory, sync, | runtime overhead may occur. Values may be combined using ``','``. Each value except ``none`` may be     |
   |                               | other                 | appended with a threshold after ``':'``. The threshold is duration, in nanoseconds, that CUDA APIs must |
   |                               |                       | execute before backtraces are collected; e.g., ``kernel:500``. The default value for each threshold is  |
   |                               |                       | 1000ns (1us).                                                                                           |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |   CPU sampling must be enabled.                                                                         |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--debug-symbols``           | <directory paths>     |  A list of directories with symbol files, separated by ``;`` on Windows or ``:`` on Linux and QNX.      |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--delay`` or ``-y``         | < seconds >, **0**    | Collection start delay in seconds.                                                                      |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--dts-api-port``            | integer, **9117**     | Specify the server port number when collecting NIC metrics using the DOCA Telemetry Service API.        |
   |                               |                       | Allowed only when ``--nic-metrics=hf-via-dts`` is set.                                                  |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--duration`` or ``-d``      | < seconds >           | Collection duration in seconds; duration must be greater than zero. The launched process will be        |
   |                               |                       | terminated when the specified profiling duration expires unless the user specifies the ``--kill`` none  |
   |                               |                       | option (details below).                                                                                 |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--duration-frames``         | 60 <= integer         | Stop the recording session after this many frames have been captured. When it is selected, command      |
   |                               |                       | cannot include any other stop options. If not specified, the default is disabled.                       |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--dx-force-declare``        | true, **false**       | Nsight Systems trace initialization involves creating and discarding a D3D device. Enabling this flag,  |
   | ``-adapter-removal-support``  |                       | ``--dx-force-declare-adapter-removal-support`` makes a call to ``DXGIDeclareAdapterRemovalSupport()``   |
   |                               |                       | before device creation. Requires DX11 orDX12 trace to be enabled.                                       |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--dx12-gpu-workload``       | true, false, batch,   | If individual or true, trace each DX12 workload's GPU activity individually. If batch, trace DX12       |
   |                               | **individual**,       | workloads' GPU activity in ``ExecuteCommandLists`` call batches. If none or false, do not trace DX12    |
   |                               | none                  | workloads' GPU activity. Note that this switch is applicable only when ``--trace=dx12`` is specified.   |
   |                               |                       | This option is only supported on Windows targets.                                                       |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--dx12-wait-calls``         | **true**, false       | If true, trace wait calls that block on fences for DX12. Note that this switch is applicable only when  |
   |                               |                       | ``--trace=dx12`` is specified. This option is only supported on Windows targets.                        |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--xhv-vm-symbols``          | <filepath             | XHV sampling config file. Available in Nsight Systems Embedded Platforms Edition only.                                               |
   |                               | kernel_symbols.json>  |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--env-var``                 | A=B                   | Set environment variable(s) for the application process to be launched. Environment variables should be |
   | or ``-e``                     |                       | defined as A=B. Multiple environment variables can be specified as A=B,C=D.                             |
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
   | ``--hotkey-capture``          | 'F1' to 'F12',        | Hotkey to trigger the profiling session. Note that this switch is applicable only when                  |
   |                               | **F12**               | ``--capture-range=hotkey`` is specified.                                                                |
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
   | ``--inherit-environment``     | **true**, false       | When true, the current environment variables and the tool’s environment variables will be specified     |
   | or ``-n``                     |                       | for the launched process. When false, only the tool’s environment variables will be specified for the   |
   |                               |                       | launched process.                                                                                       |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--discard-environment``     | true, **false**       | When false, Nsight Systems will collect the environment variables of the launched process. When true,   |
   |                               |                       | the environment variables will not be collected.                                                        |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |   Available on Linux only.                                                                              |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--injection-use-detours``   | **true**, false       | Use detours for injection. If false, process injection will be performed by windows hooks which         |
   |                               |                       | allows it to bypass anti-cheat software. Equivalent to setting the ``--system-wide`` option to the      |
   |                               |                       | inverse value. Only available for Windows platforms.                                                    |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--isr``                     | true, **false**       | Trace Interrupt Service Routines (ISRs) and Deferred Procedure Calls (DPCs). Requires administrative    |
   |                               |                       | privileges. Available only on Windows devices.                                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--kill``                    | none, sigkill,        | Send signal to the target application's process group. Can be used with ``--duration`` or range         |
   |                               | **sigterm**,          | markers.                                                                                                |
   |                               | signal number         |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--mpi-impl``                | **openmpi**, mpich    | When using ``--trace=mpi`` to trace MPI APIs, use ``--mpi-impl`` to specify which MPI implementation    |
   |                               |                       | the application is using. If no MPI implementation is specified, nsys tries to automatically detect     |
   |                               |                       | it based on the dynamic linker's search path. If this fails, ``openmpi`` is used. Calling               |
   |                               |                       | ``--mpi-impl`` without ``--trace=mpi`` is not supported.                                                |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--nccl-trace``              | none, all, **api**,   | Comma-separated list of NCCL events to record, takes priority over ``--trace``. Default is ``api``,     |
   |                               | api-coll, api-group,  | ``ce-coll``, ``group``, ``gpu`` if ``nccl`` is in ``--trace``, otherwise ``none``. All proxy events     |
   |                               | api-p2p, ce-batch,    | are experimental, ``proxy-op`` and ``proxy-step`` are only for specialized analysis and thus            |
   |                               | **ce-coll**, ce-sync, | not included in ``all``.                                                                                |
   |                               | coll, default, rt,    |                                                                                                         |
   |                               | **gpu**, **group**,   |                                                                                                         |
   |                               | kernel-launch, p2p,   |                                                                                                         |
   |                               | proxy-counters,       |                                                                                                         |
   |                               | proxy-op, proxy-step  |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--nic-metrics``             | lf, hf, hf-via-dts,   | Collect metrics from NIC/HCA devices. The 'hf' option collects high frequency metrics but lacks RoCE,   |
   |                               | **none**              | IPoIB, and 'Send Waits' metrics. The 'hf' option requires elevated user privileges. The 'hf-via-dts'    |
   |                               |                       | option collects high frequency metrics using the DOCA Telemetry Service (DTS) API and does not require  |
   |                               |                       | elevated privileges. The 'lf' option collects all available metrics but at a lower sampling frequency.  |
   |                               |                       | The deprecated 'true' option is accepted for backwards compatibility and corresponds to 'lf'. The       |
   |                               |                       | 'true' option will be removed in a future release. System scope. Not available on Nsight Systems Embedded Platforms Edition.         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--nvtx-capture``            | range\@domain, range, | Specify NVTX range and domain to trigger the profiling session. This option is applicable only when     |
   | or ``-p``                     | range\@\*, **none**   | used along with ``--capture-range=nvtx``.                                                               |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--nvtx-domain-exclude``     | default,              | Choose to exclude NVTX events from a comma separated list of domains. ``default`` excludes NVTX events  |
   |                               | <domain_names>        | without a domain. A domain with this name or commas in a domain name must be escaped with ``\\``.       |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |    Only one of ``--nvtx-domain-include`` and ``--nvtx-domain-exclude`` can be used. This option         |
   |                               |                       |    is only applicable when ``--trace=nvtx`` is specified.                                               |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--nvtx-domain-include``     | default,              | Choose to only include NVTX events from a comma separated list of domains. ``default`` filters the      |
   |                               | <domain_names>        | NVTX default domain. A domain with this name or commas in a domain name must be escaped with ``\\``.    |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |   Only one of ``--nvtx-domain-include`` and ``--nvtx-domain-exclude`` can be used. This option          |
   |                               |                       |   is only applicable when ``--trace=nvtx`` is specified.                                                |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--opengl-gpu-workload``     | **true**, false       | If true, trace the OpenGL workloads' GPU activity. Note that this switch is applicable only when        |
   |                               |                       | ``--trace=opengl`` is specified.                                                                        |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--os-events``               | 'help' or the end     | Select the OS events to sample. Use the ``--os-events=help`` switch to see the full list of events.     |
   |                               | users selected events | Multiple values can be selected, separated by commas only (no spaces). Use the ``--event-sample``       |
   |                               | in the format 'x,y'   | switch to enable. Not available on Nsight Systems Embedded Platforms Edition.                                                        |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--osrt-backtrace-depth``    | integer, **24**       | Set the depth for the backtraces collected for OS runtime libraries calls.                              |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--osrt-backtrace``          | integer, **6144**     | The ``--osrt-backtrace-stack-size`` option sets the stack dump size, in bytes, to generate backtraces   |
   | ``-stack-size``               |                       | for OS runtime libraries calls.                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--osrt-backtrace``          | nanoseconds,          | The ``--osrt-backtrace-threshold`` option set the duration, in nanoseconds, that all OS runtime         |
   | ``-threshold``                | **80000**             | libraries calls must execute before backtraces are collected.                                           |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--osrt-threshold``          | < nanoseconds >,      | Set the duration, in nanoseconds, that Operating System Runtime (osrt) APIs must execute before         |
   |                               | **1000 ns**           | they are traced. Values significantly less than 1000 may cause significant overhead and result in       |
   |                               |                       | extremely large result files.                                                                           |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |   This setting is ignored for APIs that interact with files when ``--osrt-file-access`` is set to true. |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--osrt-file-access``        | true, **false**       | Collect file access data when tracing Operating System Runtime (osrt) APIs that interact with files.    |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |   When this setting is set to true the ``--osrt-threshold`` setting is ignored for APIs that interact   |
   |                               |                       |   with files.                                                                                           |
   |                               |                       |                                                                                                         |
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
   | ``--python-backtrace``        | cuda, **none**        | Collect Python backtrace event when tracing the selected API's trigger. This option is supported        |
   |                               |                       | on Arm server (SBSA) platforms and x86 Linux targets. Note: tracing and backtraces of the selected API  |
   |                               |                       | and CPU sampling must be enabled. For example, ``--cudabacktrace`` must be set when using               |
   |                               |                       | ``--python-backtrace=cuda``.                                                                            |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--python-functions-trace``  | <json_file>           | Specify the path to the JSON file containing the requested NVTX annotations.                            |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--python-sampling``         | true, **false**       | Collect Python backtrace sampling events. This option is supported on Arm server (SBSA) platforms,      |
   |                               |                       | x86 Linux and Windows targets. Note: When profiling Python-only workflows, consider disabling the       |
   |                               |                       | CPU sampling option to reduce overhead.                                                                 |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--python-sampling``         | 1 < integers < 2000,  | The ``--python-sampling-frequency`` option specifies the Python sampling frequency. The minimum         |
   | ``-frequency``                | **1000**              | supported frequency is 1Hz. The maximum supported frequency is 2KHz. This option is ignored if the      |
   |                               |                       | ``--python-sampling`` option is set to false.                                                           |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--pytorch``                 | autograd-nvtx,        | Enable automatic annotations of PyTorch functions.                                                      |
   |                               | autograd-shapes-nvtx, |                                                                                                         |
   |                               | functions-trace,      |                                                                                                         |
   |                               | functions-trace,      |                                                                                                         |
   |                               | functions-trace-      |                                                                                                         |
   |                               | shapes, **none**      |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--dask``                    | functions-trace,      | Enable automatic annotations of Dask functions                                                          |
   |                               | **none**              |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--qnx-kernel-events``       | class/event,event,    | Multiple values can be selected, separated by commas only (no spaces). See the                          |
   |                               | class/event:mode,     | ``--qnx-kernel-events-mode`` switch description for ``:mode`` format. Use the                           |
   |                               | class:mode,help,      | ``--qnx-kernel-events=help`` switch to see the full list of values. Example:                            |
   |                               | **none**              | ``--qnx-kernel-events=8/1:system:wide,_NTO_TRACE_THREAD:process:fast,                                   |
   |                               |                       | \_NTO_TRACE_KERCALLENTER/\__KER_BAD,_NTO_TRACE_COMM,13``.                                               |
   |                               |                       | Collect QNX kernel events.                                                                              |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--qnx-kernel``              | system,process,fast,  | The ``--qnx-kernel-events-mode`` option specifies the mode for QNX kernel events collection.            |
   | ``-events-mode``              | wide,                 | Default is system:fast. Values are separated by a colon (``:``) only (no spaces). ``system`` and        |
   |                               | **system:fast**       | ``process`` cannot be specified at the same time. ``fast`` and ``wide`` cannot be specified at          |
   |                               |                       | the same time. Check the QNX documentation to determine when to select ``fast`` or ``wide`` mode.       |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--reflex-events``           | true, **false**       | Collect Reflex SDK ETW events. Available only on Windows.                                               |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--resolve-symbols``         | **true**, false       | Resolve symbols of captured samples and backtraces.                                                     |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--retain-etw-files``        | true, **false**       | Retain ETW files generated by the trace, merge and move the files to the output directory.              |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--run-as``                  | < username >,         | Run the target application as the specified username. If not specified, the target application will     |
   |                               | **none**              | be run by the same user as Nsight Systems. Requires root privileges. Available for Linux targets only.  |
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
   | ``--session-new``             | [a-Z][0-9,a-Z,spaces] | Default is profile-<id>-<application>. Name the session created by the command. Name must start with an |
   |                               |                       | alphabetical character followed by printable or space characters. Any ``%q{ENV_VAR}`` pattern will be   |
   |                               |                       | substituted with the value of the environment variable. Any ``%h`` pattern will be substituted with the |
   |                               |                       | hostname of the system. Any ``%%`` pattern will be substituted with ``%``.                              |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--show-source-info``        | **true**, false       | Show source file and line information, when available, for CPU sampling, CUDA API, OS runtime, and      |
   |                               |                       | Python backtraces. This option is supported on Linux targets and can increase report generation time.   |
   |                               |                       | Set to ``false`` to reduce report generation time.                                                      |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--show-output``             | **true**, false       | If true, send the target process's stdout and stderr streams to both the console and stdout/stderr      |
   | or ``-w``                     |                       | files which are added to the report file. If false, only send the target process stdout and stderr      |
   |                               |                       | streams to the stdout/stderr files which are added to the report file.                                  |
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
   | ``--start-frame-index``       | 1 <= integer          | Start the recording session when the frame index reaches the frame number preceding the start frame     |
   |                               |                       | index. Note when it is selected cannot include any other start options. If not specified, the default   |
   |                               |                       | is disabled.                                                                                            |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--start-later`` or ``-Y``   | true, **false**       | Delays collection indefinitely until the nsys start command is executed for this session.               |
   |                               |                       | Enabling this option overrides the ``--delay`` option.                                                  |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--stats``                   | true, **false**       | Generate summary statistics after the collection.                                                       |
   |                               |                       |                                                                                                         |
   |                               |                       | .. warning::                                                                                            |
   |                               |                       |    When set to true, an SQLite database will be created after the collection. If the collection         |
   |                               |                       |    captures a large amount of data, creating the  database file may take several minutes to complete.   |
   |                               |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--storage-metrics``         |                       | Collect throughput and operations metrics from storage devices. See:                                    |
   |                               |                       | Network Storage Profiling<network-storage-profiling>                                             |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--stop-on-exit`` or ``-x``  | **true**, false       | If true, stop collecting automatically when the launched process has exited or when the duration        |
   |                               |                       | expires - whichever occurs first. If false, duration must be set and the collection stops only when     |
   |                               |                       | the duration expires. Nsight Systems does not officially support runs longer than 5 minutes.            |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--syscall`` (beta)          | process-tree,         | Collect system calls. The value defines the collection scope: ``process-tree`` makes it tracing the     |
   |                               | pid-namespace,        | application processes only, ``pid-namespace`` - all processes in the current PID namespace and its      |
   |                               | **none**              | child namespaces (similar to the ``system-wide`` mode of other features).                               |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--system-wide``             | true, **false**       | Perform system-wide injection using Windows hooks. Equivalent to setting the                            |
   |                               |                       | ``--injection-use-detours`` option to the inverse value. Available only on Windows targets.             |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--trace``                   | **cuda**, **opengl**, | Select the API(s) to be traced. The osrt switch controls the OS runtime libraries tracing. Multiple     |
   | or ``-t``                     | **nvtx**, **osrt**,   | APIs can be selected, separated by commas only (no spaces). Since OpenACC and cuXXX APIs                |
   |                               | cuda-sw, cudnn,       | are tightly linked with CUDA, selecting one of those APIs will automatically enable CUDA tracing.       |
   |                               | cublas, cusolver,     | cublas, cudla, cusparse and cusolver all have XXX-verbose options available.                            |
   |                               | cublas-verbose,       | Reflex SDK latency markers will be automatically collected when DX or vulkan API trace is enabled.      |
   |                               | cusparse-verbose,     | See information on ``--mpi-impl`` option below if mpi is selected. If ``<api>-annotations`` is          |
   |                               | cudla, cudla-verbose, | selected, the corresponding API will also be traced. If the none option is selected, no APIs are        |
   |                               | cusolver-verbose,     | traced and no other API can be selected.                                                                |
   |                               | dx11, dx12, openacc,  |                                                                                                         |
   |                               | dx11-annotations,     | .. note::                                                                                               |
   |                               | dx12-annotations,     |    cuDNN is not available on Windows target.                                                            |
   |                               | opengl-annotations,   |                                                                                                         |
   |                               | openmp, mpi, nccl,    |                                                                                                         |
   |                               | tegra-accelerators,   | .. note::                                                                                               |
   |                               | ucx, openxr, oshmem,  |    The ``cuda`` option uses CUDA hardware trace, also called HES trace, by default on supported GPUs,   |
   |                               | openxr-annotations,   |    beginning with Blackwell.                                                                            |
   |                               | python-gil, gds,      |    Hardware trace is usually faster than the legacy software-instrumented trace, especially for         |
   |                               | s3, s3-verbose, wddm, |    workloads that launch many short kernels.                                                            |
   |                               | vulkan-annotations,   |    Use ``cuda-sw`` to force the legacy software trace for MPS workloads, MIG partitions, vGPU or VM     |
   |                               | vulkan, nvvideo, none |    environments, Confidential Compute systems, unsupported GPUs or drivers, or when you need to compare |
   |                               |                       |    against the previous CUDA trace method.                                                              |
   |                               |                       |    If hardware trace cannot be collected, Nsight Systems may fall back to software trace automatically  |
   |                               |                       |    and will report the trace method in the Diagnostics Summary page.                                    |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--trace-fork-before-exec``  | true, **false**       | If true, trace any child process after fork and before they call one of the exec functions. Beware,     |
   |                               |                       | tracing in this interval relies on undefined behavior and might cause your application to crash or      |
   |                               |                       | deadlock. This option is only available on Linux target platforms.                                      |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--vsync``                   | true, **false**       | Collect vsync events. If collection of vsync events is enabled, display/display_scanline ftrace         |
   |                               |                       | events will also be captured. Available in Nsight Systems Embedded Platforms Edition only.                                           |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--vulkan-gpu-workload``     | true, false,          | Default is individual. If individual or true, trace each Vulkan workload's GPU activity individually.   |
   |                               | batch, ,none          | If batch, trace Vulkan workloads' GPU activity in ``vkQueueSubmit`` call batches. If none or false, do  |
   |                               | **individual**        | not trace Vulkan workloads' GPU activity. Note that this switch is applicable only when                 |
   |                               |                       | ``--trace=vulkan`` is specified. This option is not supported on QNX.                                   |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--vulkan-sc-gpu-workload``  | true, false, batch,   | Default is individual. If individual or true, trace each Vulkan SC workload's GPU activity              |
   |                               | none, **individual**  | individually. If batch, trace Vulkan SC workloads' GPU activity in ``vkQueueSubmit`` call batches. If   |
   |                               |                       | none or false, do not trace Vulkan SC workloads' GPU activity. Note that this switch is applicable      |
   |                               |                       | only when ``--trace=vulkan-sc`` is specified.                                                           |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--wait``                    | primary, **all**      | If ``primary``, the CLI will wait on the application process termination. If ``all``, the CLI will      |
   |                               |                       | additionally wait on re-parented processes created by the application.                                  |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--wddm-memory-trace``       | **true**, false       | If ``true``, collect WDDM memory events: DeviceAllocation, AdapterAllocation, MemoryTransfer,           |
   |                               |                       | VidMmProcessBudgetChange, VidMmProcessUsageChange, VidMmProcessCommitmentChange,                        |
   |                               |                       | VidMmProcessDemotedCommitmentChange. Note that this switch is applicable only when ``--trace=wddm`` is  |
   |                               |                       | specified. This option is only supported on Windows targets.                                            |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--wddm-additional-events``  | true, **false**       | If ``true``, extensive trace including Hardware Scheduling queues, context status, allocations, sync    |
   |                               |                       | wait and signal events, etc. Note that this switch is applicable only when ``--trace=wddm`` is          |
   |                               |                       | specified. This option is only supported on Windows targets.                                            |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--wddm-backtraces``         | true, **false**       | If ``true``, collect backtraces of WDDM events. Enabling this collection option may increase profiling  |
   |                               |                       | overhead for target applications that generate many DxgKrnl WDDM Events. Note that this switch is       |
   |                               |                       | applicable only when ``--trace=wddm`` is specified. This option is only supported on Windows targets.   |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--xhv-trace``               | < filepath pct.json > | Collect hypervisor trace. Available in Nsight Systems Embedded Platforms Edition only.                                               |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--xhv-trace-events``        | **all**, none, core,  | Available in Nsight Systems Embedded Platforms Edition only.                                                                         |
   |                               | sched, irq, trap      |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
