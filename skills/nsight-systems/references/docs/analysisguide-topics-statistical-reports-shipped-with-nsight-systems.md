---
source_path: AnalysisGuide/topics/statistical-reports-shipped-with-nsight-systems.rst
title: ## Statistical Reports Shipped With |product-name|
---
## Statistical Reports Shipped With |product-name|

The Nsight Systems development team created and maintains a set of report
scripts for some of the commonly requested statistical reports. These scripts
will be updated to adapt to any changes in SQLite schema or internal data structures.

These scripts are located in the Nsight Systems package in the
Target-<architecture>/reports directory. The following standard reports are
available:

Note:
   The ability to display mangled names is a recent addition to the report file format, and requires that the profile data be captured with a recent version of Nsight Systems. Re-exporting an existing report file is not sufficient. If the raw, mangled kernel name data is not available, the default demangled names will be used.

Note:
   All time values given in nanoseconds by default. If you wish to output the results using a different time unit, use the ``--timeunit`` option when  running the recipe.


### cuda_api_gpu_sum[:nvtx-name][:base|:mangled] -- CUDA Summary (API/Kernels/MemOps)
Arguments

-  nvtx-name : Optional argument, if given, will prefix the kernel name with
   the name of the innermost enclosing NVTX range.
-  base - Optional argument, if given, will cause summary to be over the
   base name of the kernel, rather than the templated name.
-  mangled - Optional argument, if given, will cause summary to be over the
   raw mangled name of the kernel, rather than the templated name.

Note:
   The ability to display mangled names is a recent addition to the report file format, and requires that the profile data be captured with a recent version of Nsight Systems. Re-exporting an existing report file is not sufficient. If the raw, mangled kernel name data is not available, the default demangled names will be used.

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all executions of this kernel
-  Instances : Number of executions of this kernel
-  Avg : Average execution time of this kernel
-  Med : Median execution time of this kernel
-  Min : Smallest execution time of this kernel
-  Max : Largest execution time of this kernel
-  StdDev : Standard deviation of execution time of this kernel
-  Category : Category of the operation
-  Operation : Name of the kernel

This report provides a summary of CUDA API calls, kernels and memory
operations, and their execution times. Note that the "Time"
column is calculated using a summation of the "Total Time" column,
and represents that API call's, kernel's, or memory operation's
percent of the execution time of the APIs, kernels and memory
operations listed, and not a percentage of the application wall or
CPU execution time.

This report combines data from the ``cuda_api_sum``, ``cuda_gpu_kern_sum``, and
``cuda_gpu_mem_size_sum`` reports. It is very similar to profile section of
``nvprof --dependency-analysis``.

### cuda_api_sum -- CUDA API Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all executions of this function
-  Num Calls : Number of calls to this function
-  Avg : Average execution time of this function
-  Med : Median execution time of this function
-  Min : Smallest execution time of this function
-  Max : Largest execution time of this function
-  StdDev : Standard deviation of the time of this function
-  Name : Name of the function

This report provides a summary of CUDA API functions and their
execution times. Note that the "Time" column is calculated
using a summation of the "Total Time" column, and represents that
function's percent of the execution time of the functions listed,
and not a percentage of the application wall or CPU execution time.

### cuda_api_trace -- CUDA API Trace
Arguments - None

Output: All time values default to nanoseconds

-  Start : Timestamp when API call was made
-  Duration : Length of API calls
-  Name : API function name
-  Result : Return value of API call
-  CorrID : Correlation used to map to other CUDA calls
-  Pid : Process ID that made the call
-  Tid : Thread ID that made the call
-  T-Pri : Run priority of call thread
-  Thread Name : Name of thread that called API function

This report provides a trace record of CUDA API function calls and
their execution times.

### cuda_gpu_kern_gb_sum[:nvtx-name][:base|:mangled] -- CUDA GPU Kernel/Grid/Block Summary
Arguments

-  nvtx-name - Optional argument, if given, will prefix the kernel name with
   the name of the innermost enclosing NVTX range.

-  base - Optional argument, if given, will cause summary to be over the
   base name of the kernel, rather than the templated name.

-  mangled - Optional argument, if given, will cause summary to be over the
   raw mangled name of the kernel, rather than the templated name.

Note:
   The ability to display mangled names is a recent addition to the report file format, and requires that the profile data be captured with a recent version of Nsight Systems. Re-exporting an existing report file is not sufficient. If the raw, mangled kernel name data is not available, the default demangled names will be used.

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all executions of this kernel
-  Instances : Number of calls to this kernel
-  Avg : Average execution time of this kernel
-  Med : Median execution time of this kernel
-  Min : Smallest execution time of this kernel
-  Max : Largest execution time of this kernel
-  StdDev : Standard deviation of the time of this kernel
-  GridXYZ : Grid dimensions for kernel launch call
-  BlockXYZ : Block dimensions for kernel launch call
-  Name : Name of the kernel

This report provides a summary of CUDA kernels and their execution times.
Kernels are sorted by grid dimensions, block dimensions, and kernel name.
Note that the "Time" column is calculated using a summation of the "Total
Time" column, and represents that kernel's percent of the execution time
of the kernels listed, and not a percentage of the application wall or
CPU execution time.

### cuda_gpu_kern_sum[:nvtx-name][:base|:mangled] -- CUDA GPU Kernel Summary

Note:
   In recent versions of Nsight Systems, this report was expanded to include and sort by CUDA grid and block dimensions. This change was made to accommodate developers doing a certain type of optimization work. Unfortunately, this change caused an unexpected burden for developers doing a different type of optimization work. In order to service both use-cases, this report has been returned to the original form, without grid or block information. A new report, called ``cuda_gpu_kern_gb_sum``, has been created that retains the grid and block information.

Arguments

-  nvtx-name - Optional argument, if given, will prefix the kernel name with
   the name of the innermost enclosing NVTX range.

-  base - Optional argument, if given, will cause summary to be over the
   base name of the kernel, rather than the templated name.

-  mangled - Optional argument, if given, will cause summary to be over the
   raw mangled name of the kernel, rather than the templated name.

Note:
   The ability to display mangled names is a recent addition to the report file format, and requires that the profile data be captured with a recent version of Nsight Systems. Re-exporting an existing report file is not sufficient. If the raw, mangled kernel name data is not available, the default demangled names will be used.

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all executions of this kernel
-  Instances : Number of calls to this kernel
-  Avg : Average execution time of this kernel
-  Med : Median execution time of this kernel
-  Min : Smallest execution time of this kernel
-  Max : Largest execution time of this kernel
-  StdDev : Standard deviation of the time of this kernel
-  Name : Name of the kernel

This report provides a summary of CUDA kernels and their execution times.
Note that the "Time" column is calculated using a summation of the "Total
Time" column, and represents that kernel's percent of the execution time
of the kernels listed, and not a percentage of the application wall or
CPU execution time.

### cuda_gpu_mem_size_sum -- CUDA GPU MemOps Summary (by Size)
Arguments - None

Output:

-  Total : Total memory utilized by this operation
-  Count : Number of executions of this operation
-  Avg : Average memory size of this operation
-  Med : Median memory size of this operation
-  Min : Smallest memory size of this operation
-  Max : Largest memory size of this operation
-  StdDev : Standard deviation of the memory size of this operation
-  Operation : Name of the operation

This report provides a summary of GPU memory operations and
the amount of memory they utilize.

### cuda_gpu_mem_time_sum -- CUDA GPU MemOps Summary (by Time)
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all executions of this operation
-  Count : Number of operations to this type
-  Avg : Average execution time of this operation
-  Med : Median execution time of this operation
-  Min : Smallest execution time of this operation
-  Max : Largest execution time of this operation
-  StdDev : Standard deviation of execution time of this operation
-  Operation : Name of the memory operation

This report provides a summary of GPU memory operations and
their execution times. Note that the "Time" column is calculated
using a summation of the "Total Time" column, and represents that
operation's percent of the execution time of the operations listed,
and not a percentage of the application wall or CPU execution time.

### cuda_gpu_sum[:nvtx-name][:base|:mangled] -- CUDA GPU Summary (Kernels/MemOps)
Arguments

-  nvtx-name - Optional argument, if given, will prefix the kernel name with
   the name of the innermost enclosing NVTX range.

-  base - Optional argument, if given, will cause summary to be over the
   base name of the kernel, rather than the templated name.

-  mangled - Optional argument, if given, will cause summary to be over the
   raw mangled name of the kernel, rather than the templated name.

Note:
   The ability to display mangled names is a recent addition to the report file format, and requires that the profile data be captured with a recent version of Nsight Systems. Re-exporting an existing report file is not sufficient. If the raw, mangled kernel name data is not available, the default demangled names will be used.

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all executions of this kernel
-  Instances : Number of executions of this kernel
-  Avg : Average execution time of this kernel
-  Med : Median execution time of this kernel
-  Min : Smallest execution time of this kernel
-  Max : Largest execution time of this kernel
-  StdDev : Standard deviation of execution time of this kernel
-  Category : Category of the operation
-  Operation : Name of the kernel

This report provides a summary of CUDA kernels and memory operations,
and their execution times. Note that the "Time" column is calculated
using a summation of the "Total Time" column, and represents that
kernel's or memory operation's percent of the execution time of the
kernels and memory operations listed, and not a percentage of the
application wall or CPU execution time.

This report combines data from the ``cuda_gpu_kern_sum`` and
``cuda_gpu_mem_time_sum`` reports. This report is very similar to output of
the command ``nvprof --print-gpu-summary``.

### cuda_gpu_trace[:nvtx-name][:base|:mangled] -- CUDA GPU Trace
Arguments

-  nvtx-name - Optional argument, if given, will prefix the kernel name with
   the name of the innermost enclosing NVTX range.

-  base - Optional argument, if given, will display the base name of the
   kernel, rather than the templated name.

-  mangled - Optional argument, if given, will display the raw mangled name
   of the kernel, rather than the templated name.

Note:
   The ability to display mangled names is a recent addition to the report file format, and requires that the profile data be captured with a recent version of Nsight Systems. Re-exporting an existing report file is not sufficient. If the raw, mangled kernel name data is not available, the default demangled names will be used.

Output: All time values default to nanoseconds

-  Start : Timestamp of start time
-  Duration : Length of event
-  CorrId : Correlation ID
-  GrdX, GrdY, GrdZ : Grid values
-  BlkX, BlkY, BlkZ : Block values
-  Reg/Trd : Registers per thread
-  StcSMem : Size of Static Shared Memory
-  DymSMem : Size of Dynamic Shared Memory
-  Bytes : Size of memory operation
-  Throughput : Memory throughput
-  SrcMemKd : Memcpy source memory kind or memset memory kind
-  DstMemKd : Memcpy destination memory kind
-  Device : GPU device name and ID
-  Ctx : Context ID
-  GreenCtx: Green context ID
-  Strm : Stream ID
-  Name : Trace event name

This report displays a trace of CUDA kernels and memory operations.
Items are sorted by start time.

### cuda_kern_exec_sum[:nvtx-name][:base|:mangled] -- CUDA Kernel Launch & Exec Time Summary
Arguments

-  nvtx-name - Optional argument, if given, will prefix the kernel name with
   the name of the innermost enclosing NVTX range.

-  base - Optional argument, if given, will cause summary to be over the
   base name of the kernel, rather than the templated name.

-  mangled - Optional argument, if given, will cause summary to be over the
   raw mangled name of the kernel, rather than the templated name.

Note:
   The ability to display mangled names is a recent addition to the report file format, and requires that the profile data be captured with a recent version of Nsight Systems. Re-exporting an existing report file is not sufficient. If the raw, mangled kernel name data is not available, the default demangled names will be used.

Output: All time values default to nanoseconds

-  PID : Process ID that made kernel launch call
-  TID : Thread ID that made kernel launch call
-  DevId : CUDA Device ID that executed kernel (which GPU)
-  Count : Number of kernel records
-  QCount : Number of kernel records with positive queue time

Average, Median, Minimum, Maximum, and Standard Deviation for:

-  TAvg, TMed, TMin, TMax, TStdDev : Total time
-  AAvg, AMed, AMin, AMax, AStdDev : API time
-  QAvg, QMed, QMin, QMax, QStdDev : Queue time
-  KAvg, KMed, KMin, KMax, KStdDev : Kernel time
-  API Name : Name of CUDA API call used to launch kernel
-  Kernel Name : Name of CUDA Kernel

This report provides a summary of the launch and execution times of CUDA
kernels. The launch and execution is broken down into three phases: "API
time," the execution time of the CUDA API call on the CPU used to launch the
kernel; "Queue time," the time between the launch call and the kernel
execution; and "Kernel time," the kernel execution time on the GPU. The
"total time" is not a just sum of the other times, as the phases sometimes
overlap. Rather, the total time runs from the start of the API call to end
of the API call or the end of the kernel execution, whichever is later.

The reported queue time is measured from the end of the API call to the
start of the kernel execution. The actual queue time is slightly longer, as
the kernel is enqueue somewhere in the middle of the API call, and not in
the final nanosecond of function execution. Due to this delay, it is
possible for kernel execution to start before the CUDA launch call returns.
In these cases, no queue time will be reported. Only kernel launches with
positive queue times are included in the queue average, minimum, maximum,
and standard deviation calculations. The "QCount" column indicates how many
launches had positive queue times (and how many launches were involved in
calculating the queue time statistics). Subtracting "QCount" from "Count"
will indicate how many kernels had no queue time.

Be aware that having a queue time is not inherently bad. Queue times
indicate that the GPU was busy running other tasks when the new kernel was
scheduled for launch. If every kernel launch is immediate, without any queue
time, that _may_ indicate an idle GPU with poor utilization. In terms of
performance optimization, it should not necessarily be a goal to eliminate
queue time.

### cuda_kern_exec_trace[:nvtx-name][:base|:mangled] -- CUDA Kernel Launch & Exec Time Trace
Arguments

-  nvtx-name - Optional argument, if given, will prefix the kernel name with
   the name of the innermost enclosing NVTX range.

-  base - Optional argument, if given, will cause summary to be over the
   base name of the kernel, rather than the templated name.

-  mangled - Optional argument, if given, will cause summary to be over the
   raw mangled name of the kernel, rather than the templated name.

Note: the ability to display mangled names is a recent addition to the
report file format, and requires that the profile data be captured with
a recent version of Nsight Systems. Re-exporting an existing report file is not
sufficient. If the raw, mangled kernel name data is not available, the
default demangled names will be used.

Output: All time values default to nanoseconds

-  API Start : Start timestamp of CUDA API launch call
-  API Dur : Duration of CUDA API launch call
-  Queue Start : Start timestamp of queue wait time, if it exists
-  Queue Dur : Duration of queue wait time, if it exists
-  Kernel Start : Start timestamp of CUDA kernel
-  Kernel Dur : Duration of CUDA kernel
-  Total Dur : Duration from API start to kernel end
-  PID : Process ID that made kernel launch call
-  TID : Thread ID that made kernel launch call
-  DevId : CUDA Device ID that executed kernel (which GPU)
-  API Function : Name of CUDA API call used to launch kernel
-  GridXYZ : Grid dimensions for kernel launch call
-  BlockXYZ : Block dimensions for kernel launch call
-  Kernel Name : Name of CUDA Kernel

This report provides a trace of the launch and execution time of each CUDA
kernel. The launch and execution is broken down into three phases: "API
time," the execution time of the CUDA API call on the CPU used to launch the
kernel; "Queue time," the time between the launch call and the kernel
execution; and "Kernel time," the kernel execution time on the GPU. The
"total time" is not a just sum of the other times, as the phases sometimes
overlap. Rather, the total time runs from the start of the API call to end
of the API call or the end of the kernel execution, whichever is later.

The reported queue time is measured from the end of the API call to the
start of the kernel execution. The actual queue time is slightly longer, as
the kernel is enqueue somewhere in the middle of the API call, and not in
the final nanosecond of function execution. Due to this delay, it is
possible for kernel execution to start before the CUDA launch call returns.
In these cases, no queue times will be reported.

Be aware that having a queue time is not inherently bad. Queue times
indicate that the GPU was busy running other tasks when the new kernel was
scheduled for launch. If every kernel launch is immediate, without any queue
time, that _may_ indicate an idle GPU with poor utilization. In terms of
performance optimization, it should not necessarily be a goal to eliminate
queue time.

### dx11_pix_sum -- DX11 PIX Range Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all instances of this range
-  Instances : Number of instances of this range
-  Avg : Average execution time of this range
-  Med : Median execution time of this rage
-  Min : Smallest execution time of this range
-  Max : Largest execution time of this range
-  StdDev : Standard deviation of execution time of this range
-  Range : Name of the range

This report provides a summary of D3D11 PIX CPU debug markers,
and their execution times. Note that the "Time" column
is calculated using a summation of the "Total Time" column, and represents
that range's percent of the execution time of the ranges listed, and not a
percentage of the application wall or CPU execution time.

### dx12_gpu_marker_sum -- DX12 GPU Command List PIX Ranges Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all instances of this range
-  Instances : Number of instances of this range
-  Avg : Average execution time of this range
-  Med : Median execution time of this range
-  Min : Smallest execution time of this range
-  Max : Largest execution time of this range
-  StdDev : Standard deviation of execution time of this range
-  Range : Name of the range

This report provides a summary of DX12 PIX GPU command list debug markers,
and their execution times. Note that the "Time" column
is calculated using a summation of the "Total Time" column, and represents
that range's percent of the execution time of the ranges listed, and not a
percentage of the application wall or CPU execution time.

### dx12_pix_sum -- DX12 PIX Range Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all instances of this range
-  Instances : Number of instances of this range
-  Avg : Average execution time of this range
-  Med : Median execution time of this range
-  Min : Smallest execution time of this range
-  Max : Largest execution time of this range
-  StdDev : Standard deviation of execution time of this range
-  Range : Name of the range

This report provides a summary of D3D12 PIX CPU debug markers,
and their execution times. Note that the "Time" column
is calculated using a summation of the "Total Time" column, and represents
that range's percent of the execution time of the ranges listed, and not a
percentage of the application wall or CPU execution time.

### mpi_event_sum -- MPI Event Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all instances of this event
-  Instances : Number of instances of this event
-  Avg : Average execution time of this event
-  Med : Median execution time of this event
-  Min : Smallest execution time of this event
-  Max : Largest execution time of this event
-  StdDev : Standard deviation of execution time of this event
-  Source: Original source class of event data
-  Name : Name of MPI event

This report provides a summary of all recorded MPI events.  Note that the
"Time" column is calculated using a summation of the "Total Time" column,
and represents that event's percent of the total execution time of the
listed events, and not a percentage of the application wall or CPU
execution time.

### mpi_event_trace -- MPI Event Trace
Arguments - None

Output: All time values default to nanoseconds

-  Start : Start timestamp of event
-  End : End timestamp of event
-  Duration : Duration of event
-  Event : Name of event type
-  Pid : Process Id that generated the event
-  Tid : Thread Id that generated the event
-  Tag : MPI message tag
-  Rank : MPI Rank that generated event
-  PeerRank : Other MPI rank of send or receive type events
-  RootRank : Root MPI rank for broadcast type events
-  Size : Size of message for uni-directional operations (send & recv)
-  CollSendSize : Size of sent message for collective operations
-  CollRecvSize : Size of received message for collective operations

This report provides a trace record of all recorded MPI events.

Note that MPI_Sendrecv events with different rank, tag, or size values
are broken up into two separate report rows, one reporting the send,
and one reporting the receive.  If only one row exists, the rank,
tag, and size can assumed to be the same.

### mpi_msg_size_sum -- MPI Message Size Summary
Arguments - None

Output: Message size values are in bytes

-  Total Message Volume : Aggregated message size from all instances of this API function
-  Instances : Number of instances of this API function
-  Avg : Average message size of this API function
-  Med : Median message size of this API function
-  Min : Smallest message size of this API function
-  Max : Largest message size of this API function
-  StdDev : Standard deviation of message size for this API function
-  Source : Message source (p2p, coll_send, coll_recv)
-  Name : Name of the MPI API function

This report provides a message size summary of all collective and point-to-point
MPI calls.

Note that for MPI collectives the report presents the sent message with Source
equal to ``coll_send`` and the received message with Source equal to ``coll_recv``.

### network_congestion[:ticks_threshold=<ticks_per_ms>] -- Network Devices Congestion
Arguments

-  ticks_threshold=<ticks_per_ms> - Threshold in ticks/ms above which we report
   congestion. Default is 10000.

Output: All time values default to nanoseconds

-  Start : Start timestamp of congestion interval
-  End : End timestamp of congestion interval
-  Duration : Duration of congestion interval
-  Send wait rate: Rate of congestion during the interval
-  GUID : The device GUID
-  Name : The device name

This report displays congestion events with a high send wait rate. By
default, only events with a send wait rate above 10000 ticks/ms are shown,
but a custom threshold value can be set.

Each event defines a period of time when the device experienced some level
of congestion. The level of congestion is defined by the send wait rate,
given in time ticks per millisecond (ticks/ms). The specific duration of a
tick is device specific, but can be assumed to be nanoseconds in scale.
Congestion is measured by counting the number of ticks during which the port
had data to transmit, but no data was sent because of insufficient credits
or because of lack of arbitration. The presented value of send wait rate is
the amount of ticks counted during an event, normalized over the event's
duration. Higher send wait rate values indicate more congestion.

Because the specific duration of a tick is device dependent, analysis
should focus on the relative send wait rates of events generated by the same
device. Comparing absolute send wait rates across devices is only meaningful
if the time tick duration is known to be similar.

For IB Switch metrics, we do not present the device name, only the GUID.

### nvtx_gpu_proj_sum -- NVTX GPU Projection Summary
Arguments - None

Output: All time values default to nanoseconds

-  Range : Name of the NVTX range
-  Style : Range style; Start/End or Push/Pop
-  Total Proj Time: Total projected time used by all instances of this range name
-  Total Range Time: Total original NVTX range time used by all instances of this range name
-  Range Instances : Number of instances of this range
-  Proj Avg : Average projected time for this range
-  Proj Med : Median projected time for this range
-  Proj Min : Minimum projected time for this range
-  Proj Max : Maximum projected time for this range
-  Proj StdDev : Standard deviation of projected times for this range
-  Total GPU Ops : Total number of GPU ops
-  Avg GPU Ops : Average number of GPU ops
-  Avg Range Lvl : Average range stack depth
-  Avg Num Child : Average number of children ranges

This report provides a summary of NVTX time ranges projected from the
CPU to the GPU. Each NVTX range contains one or more GPU operations. A
GPU operation is considered to be "contained" by the NVTX range if the
CUDA API call used to launch the operation is within the NVTX range.
Only ranges that start and end on the same thread are taken into account.

The projected range will have the start timestamp of the start of the
first enclosed GPU operation and the end timestamp of the end of the
last enclosed GPU operation. This report then summarizes all the range
instances by name and style. Note that in cases when one NVTX range
might enclose another, the time of the child(ren) range(s) is not
subtracted from the parent range. This is because the projected times
may not strictly overlap like the original NVTX range times do. As such,
the total projected time of all ranges might exceed the total sampling
duration.

### nvtx_gpu_proj_trace -- NVTX GPU Projection Trace
Arguments - None

Output: All time values default to nanoseconds

-  Name : Name of the NVTX range
-  Projected Start : Projected range start timestamp
-  Projected Duration : Projected range duration
-  Orig Start : Original NVTX range start timestamp
-  Orig Duration : Original NVTX range duration
-  Style : Range style; Start/End or Push/Pop
-  PID : Process ID
-  TID : Thread ID
-  NumGPUOps : Number of enclosed GPU operations
-  Lvl : Stack level, starts at 0
-  NumChild : Number of children ranges
-  RangeId : Arbitrary ID for range
-  ParentId : Range ID of the enclosing range
-  RangeStack : Range IDs that make up the push/pop stack

This report provides a trace of NVTX time ranges projected from the CPU
onto the GPU. Each NVTX range contains one or more GPU operations. A GPU
operation is considered to be "contained" by an NVTX range if the CUDA API
call used to launch the operation is within the NVTX range. Only ranges
that start and end on the same thread are taken into account.

The projected range will have the start timestamp of the first enclosed GPU
operation and the end timestamp of the last enclosed GPU operation, as well
as the stack state and relationship to other NVTX ranges.

### nvtx_kern_sum[:base|:mangled] -- NVTX Range Kernel Summary
Arguments

-  base - Optional argument, if given, will cause summary to be over the
   base name of the CUDA kernel, rather than the templated name.

-  mangled - Optional argument, if given, will cause summary to be over the
   raw mangled name of the kernel, rather than the templated name.


Note:
   The ability to display mangled names is a recent addition to the report file format, and requires that the profile data be captured with a recent version of Nsight Systems. Re-exporting an existing report file is not sufficient. If the raw, mangled kernel name data is not available, the default demangled names will be used.

Output: All time values default to nanoseconds

-  NVTX Range : Name of the range
-  Style : Range style; Start/End or Push/Pop
-  PID : Process ID for this set of ranges and kernels
-  TID : Thread ID for this set of ranges and kernels
-  NVTX Inst : Number of NVTX range instances
-  Kern Inst : Number of CUDA kernel instances
-  Total Time : Total time used by all kernel instances of this range
-  Avg : Average execution time of the kernel
-  Med : Median execution time of the kernel
-  Min : Smallest execution time of the kernel
-  Max : Largest execution time of the kernel
-  StdDev : Standard deviation of the execution time of the kernel
-  Kernel Name : Name of the kernel

This report provides a summary of CUDA kernels, grouped by NVTX ranges. To
compute this summary, each kernel is matched to one or more containing NVTX
range in the same process and thread ID. A kernel is considered to be
"contained" by an NVTX range if the CUDA API call used to launch the kernel
is within the NVTX range. The actual execution of the kernel may last
longer than the NVTX range. A specific kernel instance may be associated
with more than one NVTX range if the ranges overlap. For example, if a
kernel is launched inside a stack of push/pop ranges, the kernel is
considered to be "contained" by all of the ranges on the stack, not just
the deepest range. This becomes very confusing if NVTX ranges appear inside
other NVTX ranges of the same name.

Once each kernel is associated to one or more NVTX range(s), the list of
ranges and kernels grouped by range name, kernel name, and PID/TID. A
summary of the kernel instances and their execution times is then computed.
The "NVTX Inst" column indicates how many NVTX range instances contained
this kernel, while the "Kern Inst" column indicates the number of kernel
instances in the summary line.

### nvtx_pushpop_sum -- NVTX Push/Pop Range Summary
Arguments - None

Output: All time values given in nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all instances of this range
-  Instances : Number of instances of this range
-  Avg : Average execution time of this range
-  Med : Median execution time of this range
-  Min : Smallest execution time of this range
-  Max : Largest execution time of this range
-  StdDev : Standard deviation of execution time of this range
-  Range : Name of the range

This report provides a summary of NV Tools Extensions Push/Pop Ranges and
their execution times. Note that the "Time" column is calculated
using a summation of the "Total Time" column, and represents that
range's percent of the execution time of the ranges listed,
and not a percentage of the application wall or CPU execution time.

### nvtx_pushpop_trace -- NVTX Push/Pop Range Trace
Arguments - None

Output: All time values default to nanoseconds

-  Start : Range start timestamp
-  End : Range end timestamp
-  Duration : Range duration
-  DurChild : Duration of all child ranges
-  DurNonChild : Duration of this range minus child ranges
-  Name : Name of the NVTX range
-  PID : Process ID
-  TID : Thread ID
-  Lvl : Stack level, starts at 0
-  NumChild : Number of children ranges
-  RangeId : Arbitrary ID for range
-  ParentId : Range ID of the enclosing range
-  RangeStack : Range IDs that make up the push/pop stack
-  NameTree : Range name prefixed with level indicator

This report provides a trace of NV Tools Extensions Push/Pop Ranges,
their execution time, stack state, and relationship to other push/pop
ranges.

### nvtx_startend_sum -- NVTX Start/End Range Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all instances of this range
-  Instances : Number of instances of this range
-  Avg : Average execution time of this range
-  Med : Median execution time of this range
-  Min : Smallest execution time of this range
-  Max : Largest execution time of this range
-  StdDev : Standard deviation of execution time of this range
-  Range : Name of the range

This report provides a summary of NV Tools Extensions Start/End Ranges
and their execution times. Note that the "Time" column is calculated
using a summation of the "Total Time" column, and represents that
range's percent of the execution time of the ranges listed, and not a
percentage of the application wall or CPU execution time.

### nvtx_sum -- NVTX Range Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all instances of this range
-  Instances : Number of instances of this range
-  Avg : Average execution time of this range
-  Med : Median execution time of this range
-  Min : Smallest execution time of this range
-  Max : Largest execution time of this range
-  StdDev : Standard deviation of execution time of this range
-  Style : Range style; Start/End or Push/Pop
-  Range : Name of the range

This report provides a summary of NV Tools Extensions Start/End and
Push/Pop Ranges, and their execution times. Note that the "Time" column
is calculated using a summation of the "Total Time" column, and represents
that range's percent of the execution time of the ranges listed, and not a
percentage of the application wall or CPU execution time.

### nvvideo_api_sum -- NvVideo API Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all executions of this function
-  Num Calls : Number of calls to this function
-  Avg : Average execution time of this function
-  Med : Median execution time of this function
-  Min : Smallest execution time of this function
-  Max : Largest execution time of this function
-  StdDev : Standard deviation of the time of this function
-  Event Type : Which API this function belongs to
-  Name : Name of the function

This report provides a summary of NvVideo API functions and their
execution times. Note that the "Time" column is calculated
using a summation of the "Total Time" column, and represents that
function's percent of the execution time of the functions listed,
and not a percentage of the application wall or CPU execution time.

### openacc_sum -- OpenACC Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all executions of event type
-  Count : Number of event type
-  Avg : Average execution time of event type
-  Med : Median execution time of event type
-  Min : Smallest execution time of event type
-  Max : Largest execution time of event type
-  StdDev : Standard deviation of execution time of event type
-  Name : Name of the event

This report provides a summary of OpenACC events and their
execution times. Note that the "Time" column is calculated
using a summation of the "Total Time" column, and represents that
event type's percent of the execution time of the events listed,
and not a percentage of the application wall or CPU execution time.

### opengl_khr_gpu_range_sum -- OpenGL KHR_debug GPU Range Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all instances of this range
-  Instances : Number of instances of this range
-  Avg : Average execution time of this range
-  Med : Median execution time of this range
-  Min : Smallest execution time of this range
-  Max : Largest execution time of this range
-  StdDev : Standard deviation of execution time of this range
-  Range : Name of the range

This report provides a summary of OpenGL KHR_debug GPU PUSH/POP debug Ranges,
and their execution times. Note that the "Time" column
is calculated using a summation of the "Total Time" column, and represents
that range's percent of the execution time of the ranges listed, and not a
percentage of the application wall or CPU execution time.

### opengl_khr_range_sum -- OpenGL KHR_debug Range Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all instances of this range
-  Instances : Number of instances of this range
-  Avg : Average execution time of this range
-  Med : Median execution time of this range
-  Min : Smallest execution time of this range
-  Max : Largest execution time of this range
-  StdDev : Standard deviation of execution time of this range
-  Range : Name of the range

This report provides a summary of OpenGL KHR_debug CPU PUSH/POP debug Ranges,
and their execution times. Note that the "Time" column
is calculated using a summation of the "Total Time" column, and represents
that range's percent of the execution time of the ranges listed, and not a
percentage of the application wall or CPU execution time.

### openmp_sum -- OpenMP Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all executions of event type
-  Count : Number of event type
-  Avg : Average execution time of event type
-  Med : Median execution time of event type
-  Min : Smallest execution time of event type
-  Max : Largest execution time of event type
-  StdDev : Standard deviation of execution time of event type
-  Name : Name of the event

This report provides a summary of OpenMP events and their
execution times. Note that the "Time" column is calculated
using a summation of the "Total Time" column, and represents that
event type's percent of the execution time of the events listed,
and not a percentage of the application wall or CPU execution time.

### osrt_sum -- OS Runtime Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all executions of this function
-  Num Calls : Number of calls to this function
-  Avg : Average execution time of this function
-  Med : Median execution time of this function
-  Min : Smallest execution time of this function
-  Max : Largest execution time of this function
-  StdDev : Standard deviation of execution time of this function
-  Name : Name of the function

This report provides a summary of operating system functions and
their execution times. Note that the "Time" column is calculated
using a summation of the "Total Time" column, and represents that
function's percent of the execution time of the functions listed,
and not a percentage of the application wall or CPU execution time.

### syscall_sum -- Syscall Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all executions of this syscall
-  Num Calls : Number of calls to this syscall
-  Avg : Average execution time of this syscall
-  Med : Median execution time of this syscall
-  Min : Smallest execution time of this syscall
-  Max : Largest execution time of this syscall
-  StdDev : Standard deviation of execution time of this syscall
-  Name : Name of the syscall

This report provides a summary of syscalls and their execution
times. Note that the "Time" column is calculated using a summation
of the "Total Time" column, and represents that syscall's percent
of the execution time of the syscalls listed, and not a percentage
of the application wall or CPU execution time.

### um_cpu_page_faults_sum -- Unified Memory CPU Page Faults Summary
Arguments - None

Output:

   CPU Page Faults : Number of CPU page faults that occurred
   CPU Instruction Address : Address of the CPU instruction that caused the CPU page faults

   This report provides a summary of CPU page faults for unified memory.

### um_sum[:rows=<limit>] -- Unified Memory Analysis Summary
Arguments

-  rows=<limit> - Maximum number of rows returned by the query.
   Default is 10.

Output:

-  Virtual Address : Virtual base address of the page(s) being transferred
-  HtoD Migration Size : Bytes transferred from Host to Device
-  DtoH Migration Size : Bytes transferred from Device to Host
-  CPU Page Faults : Number of CPU page faults that occurred for the virtual base address
-  GPU Page Faults : Number of GPU page faults that occurred for the virtual base address
-  Migration Throughput : Bytes transferred per second

This report provides a summary of data migrations for unified memory.

### um_total_sum -- Unified Memory Totals Summary
Arguments - None

Output:

-  Total HtoD Migration Size : Total bytes transferred from host to device
-  Total DtoH Migration Size : Total bytes transferred from device to host
-  Total CPU Page Faults : Total number of CPU page faults that occurred
-  Total GPU Page Faults : Total number of GPU page faults that occurred
-  Minimum Virtual Address : Minimum value of the virtual address range for the pages transferred
-  Maximum Virtual Address : Maximum value of the virtual address range for the pages transferred

This report provides a summary of all the page faults for unified memory.

### vulkan_api_sum -- Vulkan API Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all executions of this function
-  Num Calls: Number of calls to this function
-  Avg : Average execution time of this function
-  Med : Median execution time of this function
-  Min : Smallest execution time of this function
-  Max : Largest execution time of this function
-  StdDev : Standard deviation of the time of this function
-  Name : Name of the function

This report provides a summary of Vulkan API functions and their
execution times. Note that the "Time" column is calculated
using a summation of the "Total Time" column, and represents that
function's percent of the execution time of the functions listed,
and not a percentage of the application wall or CPU execution time.

### vulkan_api_trace -- Vulkan API Trace
Arguments - None

Output: All time values default to nanoseconds

-  Start : Timestamp when API call was made
-  Duration : Length of API calls
-  Name : API function name
-  Event Class : Vulkan trace event type
-  Context : Trace context ID
-  CorrID : Correlation used to map to other Vulkan calls
-  Pid : Process ID that made the call
-  Tid : Thread ID that made the call
-  T-Pri : Run priority of call thread
-  Thread Name : Name of thread that called API function

This report provides a trace record of Vulkan API function calls and
their execution times.

### vulkan_gpu_marker_sum -- Vulkan GPU Range Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all instances of this range
-  Instances : Number of instances of this range
-  Avg : Average execution time of this range
-  Med : Median execution time of this range
-  Min : Smallest execution time of this range
-  Max : Largest execution time of this range
-  StdDev : Standard deviation of execution time of this range
-  Range : Name of the range

This report provides a summary of Vulkan GPU debug markers,
and their execution times. Note that the "Time" column
is calculated using a summation of the "Total Time" column, and represents
that range's percent of the execution time of the ranges listed, and not a
percentage of the application wall or CPU execution time.

### vulkan_marker_sum -- Vulkan Range Summary
Arguments - None

Output: All time values default to nanoseconds

-  Time : Percentage of "Total Time"
-  Total Time : Total time used by all instances of this range
-  Instances : Number of instances of this range
-  Avg : Average execution time of this range
-  Med : Median execution time of this range
-  Min : Smallest execution time of this range
-  Max : Largest execution time of this range
-  StdDev : Standard deviation of execution time of this range
-  Range : Name of the range

This report provides a summary of Vulkan debug markers on the CPU,
and their execution times. Note that the "Time" column
is calculated using a summation of the "Total Time" column, and represents
that range's percent of the execution time of the ranges listed, and not a
percentage of the application wall or CPU execution time.

### wddm_queue_sum -- WDDM Queue Utilization Summary
Arguments - None

Output: All time values default to nanoseconds

-  Utilization : Percent of time when queue was not empty
-  Instances : Number of events
-  Avg : Average event duration
-  Med : Median event duration
-  Min : Minimum event duration
-  Max : Maximum event duration
-  StdDev : Standard deviation of event durations
-  Name : Event name
-  Q Type : Queue type ID
-  Q Name : Queue type name
-  PID : Process ID associated with event
-  GPU ID : GPU index
-  Context : WDDM context of queue
-  Engine : Engine type ID
-  Node Ord : WDDM node ordinal ID

This report provides a summary of the WDDM queue utilization. The
utilization is calculated by comparing the amount of time when the queue had
one or more active events to total duration, as defined by the minimum and
maximum event time for a given Process ID (regardless of the queue context).
