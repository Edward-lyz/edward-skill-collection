---
source_path: UserGuide/topics/example-single-command-lines.rst
title: ## Example Single Command Lines
---
## Example Single Command Lines

**Version Information**


   nsys -v

Effect: Prints tool version information to the screen.

**Run with elevated privilege**


   sudo nsys profile <app>

Effect: Nsight Systems CLI (and target application) will run with elevated
privilege. This is necessary for some features, such as FTrace or system-wide
CPU sampling. If you don't want the target application to be elevated, use
``--run-as`` option.

**Default analysis run**


   nsys profile <application>
       [application-arguments]

Effect: Launch the application using the given arguments. Start collecting
immediately and end collection when the application stops. Trace CUDA, OpenGL,
NVTX, and OS runtime libraries APIs. Collect CPU Instruction Pointer (IP)
sampling information and thread scheduling information. With Nsight Systems Embedded Platforms Edition this
will only analysis the single process. With Nsight Systems Workstation Edition this will trace
the process tree. Generate the report#.nsys-rep file in the default location,
incrementing the report number if needed to avoid overwriting any existing
output files.

**Limited trace only run**


   nsys profile --trace=cuda,nvtx -d 20
       --sample=none --cpuctxsw=none -o my_test <application>
       [application-arguments]

Effect: Launch the application using the given arguments. Start collecting
immediately and end collection after 20 seconds or when the application ends.
Trace CUDA and NVTX APIs. Do not collect CPU sampling information or thread
scheduling information. Profile any child processes. Generate the output file as
``my_test.nsys-rep`` in the current working directory.

**Force software CUDA trace run**


   nsys profile --trace=cuda-sw,nvtx
       --sample=none --cpuctxsw=none <application>
       [application-arguments]

Effect: Launch the application using the legacy software-instrumented CUDA trace
method instead of the default CUDA hardware trace method. Use this when CUDA
hardware trace is unsupported for the workload or environment, or when comparing
results against the previous CUDA trace method.

**Delayed start run**


   nsys profile -e TEST_ONLY=0 -y 20
       <application> [application-arguments]

Effect: Set environment variable TEST_ONLY=0. Launch the application using the
given arguments. Start collecting after 20 seconds and end collection at
application exit. Trace CUDA, OpenGL, NVTX, and OS runtime libraries APIs.
Collect CPU sampling and thread schedule information. Profile any child
processes. Generate the report#.nsys-rep file in the default location,
incrementing if needed to avoid overwriting any existing output files.

**Run application, start/stop collection using NVTX**


   nsys profile -c nvtx -w true -p MESSAGE@DOMAIN <application> [application-arguments]

Effect: Create interactive CLI process and set it up to begin collecting as soon
as an NVTX range with a given message in a given domain (capture range) is opened.
Launch application for default analysis, sending application output to the
terminal. Stop collection when all capture ranges are closed, when the user
calls ``nsys stop``, or when the root process terminates. Generate the
``report#.nsys-rep`` in the default location.

Note:

   The Nsight Systems CLI only triggers the profiling session for the first
   capture range.

NVTX capture range can be specified:

-  Message\@Domain: All ranges with given message in given domain are capture
   ranges. For example:


      nsys profile -c nvtx -w true -p profiler@service ./app

   This would make the profiling start when the first range with message
   "profiler" is opened in domain "service."

-  Message\@\*: All ranges with given message in all domains are capture ranges.
   For example:


      nsys profile -c nvtx -w true -p 'profiler@*' ./app

   This would make the profiling start when the first range with message
   "profiler" is opened in any domain.

-  Message: All ranges with given message in default domain are capture ranges.
   For example:


      nsys profile -c nvtx -w true -p profiler ./app

   This would make the profiling start when the first range with message
   "profiler" is opened in the default domain.

-  By default, only messages provided by NVTX registered strings are considered.
   This avoids the need to perform a string match on every NVTX string encountered
   in the application, which creates significant additional overhead. It is
   strongly recommended to always use NVTX registered strings. If you do not use
   registered strings you will have to enable the full match by launching
   your application with ``NSYS_NVTX_PROFILER_REGISTER_ONLY=0`` environment:


      nsys profile -c nvtx -w true -p profiler@service -e NSYS_NVTX_PROFILER_REGISTER_ONLY=0 ./app


Note:

   The separator '@' can be escaped with backslash '\\'. If multiple separators
   without escape character are specified, only the last one is applied, all others are discarded.
   
   
**Collect ftrace events**


   nsys profile --ftrace=drm/drm_vblank_event
       -d 20

Effect: Collect ftrace ``drm_vblank_event`` events for 20 seconds. Generate the
report#.nsys-rep file in the current working directory. Note that ftrace event
collection requires running as root. To get a list of ftrace events available
from the kernel, run the following:


   sudo cat /sys/kernel/debug/tracing/available_events

**Run GPU metric sampling on one TU10x**


   nsys profile --gpu-metrics-devices=0
       --gpu-metrics-set=tu10x-gfxt <application>

Effect: Launch application. Collect default options and GPU metrics for the
first GPU (a TU10x), using the tu10x-gfxt metric set at the default frequency
(10 kHz). Profile any child processes. Generate the ``report#.nsys-rep`` file
in the default location, incrementing if needed to avoid overwriting any
existing output files.

**Run GPU metric sampling on all GPUs at a set frequency**


   nsys profile --gpu-metrics-devices=all
       --gpu-metrics-frequency=20000 <application>

Effect: Launch application. Collect default options and GPU metrics for all
available GPUs using the first suitable metric set for each and sampling at 20
kHz. Profile any child processes. Generate the report#.nsys-rep file in the
default location, incrementing if needed to avoid overwriting any existing
output files.

**Collect CPU IP/backtrace and CPU context switch**


   nsys profile --sample=system-wide --duration=5

Effect: Collects both CPU IP/backtrace samples using the default backtrace
mechanism and traces CPU context switch activity for the whole system for 5
seconds. Note that it requires root permission or a Linux paranoid level of 0
or less to run. No hardware or OS events are sampled. Post processing of this
collection will take longer due to the large number of symbols to be resolved
caused by system-wide sampling.

**Get list of available CPU core/uncore events and metrics**


   nsys profile --cpu-metrics=help

Effect: Prints grammar describing how to list supported core and uncore PMUs,
their events and derived metrics, and supported uncore PMU event filters.


   nsys profile --cpu-metrics=help:all

Effect: Lists the CPU core/uncore events and derived metrics available for
sampling, the maximum number of events that can be sampled concurrently per
core/uncore PMU, and a summary of supported PMUs and their filters (if
applicable).

**Collect system-wide CPU events and metrics, and trace application**


   nsys profile --event-sample=system-wide
       --cpu-metrics=ITLB_WALK,DTLB_WALK,ipc,PCIe/RD_BYTES_LOC
       --event-sampling-interval=5 <app> [app args]

Effect: Collects CPU IP/backtrace samples using the default backtrace mechanism,
traces CPU context switch activity, collects CPU core events: ITLB_WALK, DTLB_WALK,
CPU core metrics: ipc, and CPU uncore events: PCIe/RD_BYTES_LOC every 5 ms for
the whole system. Note that it requires root permission or a Linux paranoid level
of 0 or less to run. Note that CUDA, NVTX, OpenGL, and OSRT within the app launched
by Nsight Systems are traced by default while using this command. Post processing
of this collection will take longer due to the large number of symbols to be
resolved caused by system-wide sampling.

**Collect custom ETW trace using configuration file**


   nsys profile --etw-provider=file.JSON

Effect: Configure custom ETW collectors using the contents of file.JSON. Collect
data for 20 seconds. Generate the ``report#.nsys-rep`` file in the current
working directory.

A template JSON configuration file is located at in the Nsight Systems
installation directory as ``\\target-windows-x64\\etw_providers_template.json``.
This path will show up automatically if you call the following:


   nsys profile --help

The **level** attribute can only be set to one of the following:

-  TRACE_LEVEL_CRITICAL
-  TRACE_LEVEL_ERROR
-  TRACE_LEVEL_WARNING
-  TRACE_LEVEL_INFORMATION
-  TRACE_LEVEL_VERBOSE

The **flags** attribute can only be set to one or more of the following:

-  EVENT_TRACE_FLAG_ALPC
-  EVENT_TRACE_FLAG_CSWITCH
-  EVENT_TRACE_FLAG_DBGPRINT
-  EVENT_TRACE_FLAG_DISK_FILE_IO
-  EVENT_TRACE_FLAG_DISK_IO
-  EVENT_TRACE_FLAG_DISK_IO_INIT
-  EVENT_TRACE_FLAG_DISPATCHER
-  EVENT_TRACE_FLAG_DPC
-  EVENT_TRACE_FLAG_DRIVER
-  EVENT_TRACE_FLAG_FILE_IO
-  EVENT_TRACE_FLAG_FILE_IO_INIT
-  EVENT_TRACE_FLAG_IMAGE_LOAD
-  EVENT_TRACE_FLAG_INTERRUPT
-  EVENT_TRACE_FLAG_JOB
-  EVENT_TRACE_FLAG_MEMORY_HARD_FAULTS
-  EVENT_TRACE_FLAG_MEMORY_PAGE_FAULTS
-  EVENT_TRACE_FLAG_NETWORK_TCPIP
-  EVENT_TRACE_FLAG_NO_SYSCONFIG
-  EVENT_TRACE_FLAG_PROCESS
-  EVENT_TRACE_FLAG_PROCESS_COUNTERS
-  EVENT_TRACE_FLAG_PROFILE
-  EVENT_TRACE_FLAG_REGISTRY
-  EVENT_TRACE_FLAG_SPLIT_IO
-  EVENT_TRACE_FLAG_SYSTEMCALL
-  EVENT_TRACE_FLAG_THREAD
-  EVENT_TRACE_FLAG_VAMAP
-  EVENT_TRACE_FLAG_VIRTUAL_ALLOC

**Typical case: profile a Python script that uses CUDA**


   nsys profile --trace=cuda,cudnn,cublas,osrt,nvtx
       --cudabacktrace=all --python-backtrace=cuda --python-sampling=true
       --delay=60 python my_dnn_script.py

Effect: Launch a Python script and start profiling it 60 seconds after the
launch, tracing CUDA, cuDNN, cuBLAS, OS runtime APIs, and NVTX as well as
collecting CPU IP and Python call stack samples and thread scheduling information.
CUDA and Python call stacks are also collected on CUDA API calls.

**Typical case: profile a Python script that uses PyTorch and CUDA**


   nsys profile --trace=cuda,cudnn,cublas,osrt,nvtx --pytorch=functions-trace-shapes,autograd-nvtx
       --cudabacktrace=all --python-backtrace=cuda --python-sampling=true
       --delay=60 python my_torch_script.py

Effect: Launch a Python script and start profiling it 60 seconds after the
launch, tracing CUDA, cuDNN, cuBLAS, OS runtime APIs, and NVTX as well as
collecting CPU IP and Python call stack samples and thread scheduling information.
PyTorch functions are traced, and tensor shapes are collected via ``--pytorch=functions-trace-shapes``
to provide detailed information about the structure and execution of the neural network model.
CUDA and Python call stacks are also collected on CUDA API calls.


**Typical case: profile an app that uses Vulkan**


   nsys profile --trace=vulkan,osrt,nvtx
       --delay=60 ./myapp

Effect: Launch an app and start profiling it 60 seconds after the launch,
tracing Vulkan, OS runtime APIs, and NVTX as well as collecting CPU sampling and
thread schedule information.
