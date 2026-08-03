---
source_path: AnalysisGuide/topics/common-sqlite-examples.rst
title: ## Common SQLite Examples
---
## Common SQLite Examples

**Common Helper Commands**

When utilizing the sqlite3 command line tool, it’s helpful to have data printed
as named columns, this can be done with:


   .mode column
   .headers on
       

The default column width is determined by the data in the first row of results.
If this doesn’t work out well, you can specify widths manually.


   .width 10 20 50

**Obtaining Sample Report**

The CLI interface of Nsight Systems was used to profile the radixSortThrust
CUDA sample, then the resulting .nsys-rep file was exported using the nsys
export.


   nsys profile --trace=cuda,osrt radixSortThrust
   nsys export --type sqlite report1.nsys-rep
       

**Serialized Process and Thread Identifiers**

Note:

   The globalTid field is a 64-bit identifier that encodes multiple components
   into a single value:
   <Hardware ID:8><VM ID:8><Process ID:24><Thread ID:24>
   It follows the structure:
   
   *  Thread ID: bits 0–23
   *  Process ID: bits 24–47
   *  VM ID: bits 48–55
   *  Hardware ID: bits 56–63
   

**Goal:** Extract readable process ID (PID) and thread ID (TID) values from
Nsight Systems's serialized identifier format.

Nsight Systems stores identifiers where events originated in serialized form to
efficiently pack multiple values into a single field. This example shows how to
decode them back to standard PID/TID format.

**What the code does:** Uses bit shifting and modulo operations to extract the
embedded PID and TID values from the globalTid field.

For events that have globalTid or globalPid fields exported, use the following
code to extract numeric TID and PID.


   SELECT globalTid / 0x1000000 % 0x1000000 AS PID, globalTid % 0x1000000 AS TID FROM TABLE_NAME;
       


   # Python equivalent:
   def extract_pid_tid(global_tid):
       PID = (global_tid // 0x1000000) % 0x1000000
       TID = global_tid % 0x1000000
       return PID, TID

Note:
   
   globalTid field includes both TID and PID values, while globalPid only
   contains the PID value.

**Read NVTX Binary Payload Fields**

**Goal:** Read the fields of an NVTX binary payload alongside the event that
carried it.

When exported with ``nsys export --dynamic-tables=all``, each NVTX binary payload
schema becomes its own table named
``DYNAMIC_NVTXPAYLOAD_DATATYPE_<globalPid>_<domainId>_<schemaId>``, one row per
payload instance. The ``NVTX_EVENTS_PAYLOAD_SCHEMAS`` link table maps each event
to the ``globalPid``, ``domainId``, and ``payloadSchemaID`` that name its table.

**What the code does:** Lists the payload links, then joins one payload table
back to ``NVTX_EVENTS`` on ``eventId`` to read the payload fields together with
the event's timing and text.


   SELECT eventId, globalPid, domainId, payloadSchemaID FROM NVTX_EVENTS_PAYLOAD_SCHEMAS;

Substitute the ids from a row above into the table name.


   SELECT e.start, e.end, e.text, d.*
   FROM DYNAMIC_NVTXPAYLOAD_DATATYPE_<globalPid>_<domainId>_<payloadSchemaID> AS d
   JOIN NVTX_EVENTS AS e USING (eventId);

Note:

   The same tables and join are available in the Arrow, Arrow directory, and
   Parquet directory exports. SQLite has no unsigned or fixed-width integer
   types, so payload columns typed ``uint8``/``uint16``/``uint32``/``uint64`` or
   32-bit ``float`` are widened to signed 64-bit integers or ``REAL`` in a SQLite
   export, while those formats preserve the payload's native column types.

**Understanding Event Types and Tags**

Many tables in the nsys SQLite export use numeric codes for event types, tags,
and classes. These codes represent different categories of events:

- **Event Types**: Identify the kind of operation or marker (e.g., NVTX marks vs ranges)
- **Tags**: Specify event phases like BEGIN/END for state transitions  
- **Event Classes**: Categorize broad event categories (e.g., different types of GPU operations)

When you see numeric values in queries, refer to the documentation sections
above or query the relevant string tables to understand their meanings.


**Correlate CUDA Kernel Launches With CUDA API Kernel Launches**

**Goal:** Link CUDA runtime API calls to the actual GPU kernels they launch,
enabling analysis of which API calls resulted in the longest-running kernels.

**What the code does:** 
1. Adds human-readable columns to the runtime table
2. Joins runtime API calls with GPU kernel executions using correlation IDs
3. Populates kernel names and API function names from the string table
4. Finds the 10 longest API calls that resulted in kernel execution


   ALTER TABLE CUPTI_ACTIVITY_KIND_RUNTIME ADD COLUMN name TEXT;
   ALTER TABLE CUPTI_ACTIVITY_KIND_RUNTIME ADD COLUMN kernelName TEXT;

   UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET kernelName =
       (SELECT value FROM StringIds
       JOIN CUPTI_ACTIVITY_KIND_KERNEL AS cuda_gpu
           ON cuda_gpu.shortName = StringIds.id
           AND CUPTI_ACTIVITY_KIND_RUNTIME.correlationId = cuda_gpu.correlationId);

   UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET name =
       (SELECT value FROM StringIds WHERE nameId = StringIds.id);
       

Select the 10 longest CUDA API ranges that resulted in kernel execution.


       
   SELECT name, kernelName, start, end FROM CUPTI_ACTIVITY_KIND_RUNTIME
       WHERE kernelName IS NOT NULL ORDER BY end - start LIMIT 10;
       


   # Python equivalent workflow:
   # 1. Load runtime and kernel data
   # 2. Join on correlation_id to match API calls with kernels
   # 3. Add readable names from string table
   # 4. Sort by duration and get top 10
   
   runtime_with_kernels = runtime.merge(kernels, on='correlationId')
   runtime_with_kernels['duration'] = runtime_with_kernels['end'] - runtime_with_kernels['start']
   top_10_longest = runtime_with_kernels.nlargest(10, 'duration')

Results:


   name                    kernelName               start       end       
   ----------------------  -----------------------  ----------  ----------
   cudaLaunchKernel_v7000  RadixSortScanBinsKernel  658863435   658868490 
   cudaLaunchKernel_v7000  RadixSortScanBinsKernel  609755015   609760075 
   cudaLaunchKernel_v7000  RadixSortScanBinsKernel  632683286   632688349 
   cudaLaunchKernel_v7000  RadixSortScanBinsKernel  606495356   606500439 
   cudaLaunchKernel_v7000  RadixSortScanBinsKernel  603114486   603119586 
   cudaLaunchKernel_v7000  RadixSortScanBinsKernel  802729785   802734906 
   cudaLaunchKernel_v7000  RadixSortScanBinsKernel  593381170   593386294 
   cudaLaunchKernel_v7000  RadixSortScanBinsKernel  658759955   658765090 
   cudaLaunchKernel_v7000  RadixSortScanBinsKernel  681549917   681555059 
   cudaLaunchKernel_v7000  RadixSortScanBinsKernel  717812527   717817671
       

**Remove Ranges Overlapping With Overhead**

**Goal:** Identify and remove CUDA API calls that overlap with profiler overhead
to get cleaner performance measurements.

**What the code does:** Uses spatial overlap detection to find CUDA runtime
ranges that intersect with profiler overhead periods. The query checks for three
types of overlap: range starts within overhead, range ends within overhead, or
range completely encompasses overhead.

Use the this query to count CUDA API ranges overlapping with the overhead ones.

Replace "SELECT COUNT(\*)" with "DELETE" to remove such ranges.


   SELECT COUNT(*) FROM CUPTI_ACTIVITY_KIND_RUNTIME WHERE rowid IN
   (
       SELECT cuda.rowid
       FROM PROFILER_OVERHEAD as overhead
       INNER JOIN CUPTI_ACTIVITY_KIND_RUNTIME as cuda ON
       (cuda.start BETWEEN overhead.start and overhead.end)
       OR (cuda.end BETWEEN overhead.start and overhead.end)
       OR (cuda.start < overhead.start AND cuda.end > overhead.end)
   );
       


   # Python equivalent for finding overlaps:
   def ranges_overlap(range1_start, range1_end, range2_start, range2_end):
       return (range1_start <= range2_end and range1_end >= range2_start)
   
   overlapping_ranges = []
   for cuda_range in cuda_ranges:
       for overhead_range in overhead_ranges:
           if ranges_overlap(cuda_range.start, cuda_range.end, 
                           overhead_range.start, overhead_range.end):
               overlapping_ranges.append(cuda_range)

Results:


## COUNT(*)
   1095      
       

**Find CUDA API Calls that Resulted in the Original Graph Node Creation**

**Goal:** Identify which CUDA API calls were responsible for creating the
original nodes in CUDA graphs (as opposed to cloned or instantiated nodes).

**What the code does:** 
1. Filters graph nodes to find only original creations (those without originalGraphNodeId)
2. Groups by graphNodeId to get the first occurrence
3. Correlates with CUDA runtime API calls that were active when the graph node was created
4. Joins with string table to get readable API function names


   SELECT graph.graphNodeId, api.start, graph.start as graphStart, api.end,
       api.globalTid, api.correlationId, api.globalTid,
       (SELECT value FROM StringIds where api.nameId == id) as name
   FROM CUPTI_ACTIVITY_KIND_RUNTIME as api
   JOIN
       (
           SELECT start, graphNodeId, globalTid from CUDA_GRAPH_NODE_EVENTS
           GROUP BY graphNodeId
           HAVING COUNT(originalGraphNodeId) = 0
       ) as graph
   ON api.globalTid == graph.globalTid AND api.start < graph.start AND api.end > graph.start
   ORDER BY graphNodeId;
       

Results:


   graphNodeId  start       graphStart  end         globalTid        correlationId  globalTid        name                         
   -----------  ----------  ----------  ----------  ---------------  -------------  ---------------  -----------------------------
   1            584366518   584378040   584379102   281560221750233  109            281560221750233  cudaGraphAddMemcpyNode_v10000
   2            584379402   584382428   584383139   281560221750233  110            281560221750233  cudaGraphAddMemsetNode_v10000
   3            584390663   584395352   584396053   281560221750233  111            281560221750233  cudaGraphAddKernelNode_v10000
   4            584396314   584397857   584398438   281560221750233  112            281560221750233  cudaGraphAddMemsetNode_v10000
   5            584398759   584400311   584400812   281560221750233  113            281560221750233  cudaGraphAddKernelNode_v10000
   6            584401083   584403047   584403527   281560221750233  114            281560221750233  cudaGraphAddMemcpyNode_v10000
   7            584403928   584404920   584405491   281560221750233  115            281560221750233  cudaGraphAddHostNode_v10000  
   29           632107852   632117921   632121407   281560221750233  144            281560221750233  cudaMemcpyAsync_v3020        
   30           632122168   632125545   632127989   281560221750233  145            281560221750233  cudaMemsetAsync_v3020        
   31           632131546   632133339   632135584   281560221750233  147            281560221750233  cudaMemsetAsync_v3020        
   34           632162514   632167393   632169297   281560221750233  151            281560221750233  cudaMemcpyAsync_v3020        
   35           632170068   632173334   632175388   281560221750233  152            281560221750233  cudaLaunchHostFunc_v10000    
      

**Backtraces for OSRT Ranges**

**Goal:** Analyze operating system runtime (OSRT) function calls with their full
call stacks to understand performance bottlenecks and call patterns.

**What the code does:** 
1. Adds human-readable columns for function names, symbol names, and module names
2. Populates these from the string table for better readability
3. Shows how to query the longest OSRT call with its complete backtrace

Adding text columns makes results of the query below more human-readable.


   ALTER TABLE OSRT_API ADD COLUMN name TEXT;
   UPDATE OSRT_API SET name = (SELECT value FROM StringIds WHERE OSRT_API.nameId = StringIds.id);

   ALTER TABLE OSRT_CALLCHAINS ADD COLUMN symbolName TEXT;
   UPDATE OSRT_CALLCHAINS SET symbolName = (SELECT value FROM StringIds WHERE symbol = StringIds.id);

   ALTER TABLE OSRT_CALLCHAINS ADD COLUMN moduleName TEXT;
   UPDATE OSRT_CALLCHAINS SET moduleName = (SELECT value FROM StringIds WHERE module = StringIds.id);
      

Print backtrace of the longest OSRT range.


   SELECT globalTid / 0x1000000 % 0x1000000 AS PID, globalTid % 0x1000000 AS TID,
       start, end, name, callchainId, stackDepth, symbolName, moduleName
   FROM OSRT_API LEFT JOIN OSRT_CALLCHAINS ON callchainId == OSRT_CALLCHAINS.id
   WHERE OSRT_API.rowid IN (SELECT rowid FROM OSRT_API ORDER BY end - start DESC LIMIT 1)
   ORDER BY stackDepth LIMIT 10;
      


   # Python equivalent for finding longest call with backtrace:
   longest_call = osrt_api.loc[osrt_api['duration'].idxmax()]
   backtrace = osrt_callchains[osrt_callchains['id'] == longest_call['callchainId']]
   backtrace_ordered = backtrace.sort_values('stackDepth')

Results:


   PID         TID         start       end         name                    callchainId  stackDepth  symbolName                      moduleName                              
   ----------  ----------  ----------  ----------  ----------------------  -----------  ----------  ------------------------------  ----------------------------------------
   19163       19176       360897690   860966851   pthread_cond_timedwait  88           0           pthread_cond_timedwait@GLIBC_2  /lib/x86_64-linux-gnu/libpthread-2.27.so
   19163       19176       360897690   860966851   pthread_cond_timedwait  88           1           0x7fbc983b7227                  /usr/lib/x86_64-linux-gnu/libcuda.so.418
   19163       19176       360897690   860966851   pthread_cond_timedwait  88           2           0x7fbc9835d5c7                  /usr/lib/x86_64-linux-gnu/libcuda.so.418
   19163       19176       360897690   860966851   pthread_cond_timedwait  88           3           0x7fbc983b64a8                  /usr/lib/x86_64-linux-gnu/libcuda.so.418
   19163       19176       360897690   860966851   pthread_cond_timedwait  88           4           start_thread                    /lib/x86_64-linux-gnu/libpthread-2.27.so
   19163       19176       360897690   860966851   pthread_cond_timedwait  88           5           __clone                         /lib/x86_64-linux-gnu/libc-2.27.so      
      

Profiled processes output streams.

**Goal:** Access stdout and stderr output from profiled processes to correlate
application output with performance data.

**What the code does:** Resolves file paths and content from string IDs to show
the captured stdout/stderr streams from profiled applications.


   ALTER TABLE ProcessStreams ADD COLUMN filename TEXT;
   UPDATE ProcessStreams SET filename = (SELECT value FROM StringIds WHERE ProcessStreams.filenameId = StringIds.id);

   ALTER TABLE ProcessStreams ADD COLUMN content TEXT;
   UPDATE ProcessStreams SET content = (SELECT value FROM StringIds WHERE ProcessStreams.contentId = StringIds.id);
      

Select all collected stdout and stderr streams.


   select globalPid / 0x1000000 % 0x1000000 AS PID, filename, content from ProcessStreams;
      

Results:


   PID         filename                                                 content                                                                                                                                                                                                                                                                                                                    
   ----------  -------------------------------------------------------  --------------------------------------------------------------------------------------------------------------------                                                                                                                                                                                                       
   19163       /tmp/nvidia/nsight_systems/streams/pid_19163_stdout.log  /home/<user>/NVIDIA_CUDA-10.1_Samples/6_Advanced/radixSortThrust/radixSortThrust Starting...

   GPU Device 0: "Quadro P2000" with compute capability 6.1


   Sorting 1048576 32-bit unsigned int keys and values

   radixSortThrust, Throughput = 401.0872 MElements/s, Time = 0.00261 s, Size = 1048576 elements
   Test passed

   19163       /tmp/nvidia/nsight_systems/streams/pid_19163_stderr.log
      

**Thread Summary**

**Goal:** Calculate CPU utilization statistics per thread to identify which
threads are consuming the most CPU resources.

Note that Nsight Systems applies additional logic during sampling events
processing to work around lost events. This means that the results of the below
query might differ slightly from the ones shown in "Analysis Summary" tab.

**Approach 1: Using CPU Cycles (when available)**

**What this code does:** Calculates thread CPU utilization using hardware
performance counter data (CPU cycles) which provides the most accurate
measurement of actual CPU usage per thread.


   SELECT
       globalTid / 0x1000000 % 0x1000000 AS PID,
       globalTid % 0x1000000 AS TID,
       ROUND(100.0 * SUM(cpuCycles) / 
           (
               SELECT SUM(cpuCycles) FROM COMPOSITE_EVENTS 
               GROUP BY globalTid / 0x1000000000000 % 0x100
           ),
           2
       ) as CPU_utilization,
       (SELECT value FROM StringIds WHERE id = 
           (
               SELECT nameId FROM ThreadNames 
               WHERE ThreadNames.globalTid = COMPOSITE_EVENTS.globalTid
           )
       ) as thread_name
   FROM COMPOSITE_EVENTS
   GROUP BY globalTid
   ORDER BY CPU_utilization DESC
   LIMIT 10;
      

Results:


   PID         TID         CPU_utilization  thread_name    
   ----------  ----------  ---------------  ---------------
   19163       19163       98.4             radixSortThrust
   19163       19168       1.35             CUPTI worker th
   19163       19166       0.25             [NS]    
      

**Approach 2: Using Scheduling Events (when PMU data not available)**

**What this approach does:** When CPU cycle counter data is not collected, this
method calculates thread CPU time based on scheduling events (when threads are
scheduled in/out), then calculates utilization percentages. This approach is
less precise but still useful for understanding relative thread activity.


   CREATE INDEX sched_start ON SCHED_EVENTS (start);

   CREATE TABLE CPU_USAGE AS
   SELECT
       first.globalTid as globalTid,
       (SELECT nameId FROM ThreadNames WHERE ThreadNames.globalTid = first.globalTid) as nameId,
       sum(second.start - first.start) as total_duration,
       count() as ranges_count
   FROM SCHED_EVENTS as first
   LEFT JOIN SCHED_EVENTS as second
   ON second.rowid =
       (
           SELECT rowid
           FROM SCHED_EVENTS
           WHERE start > first.start AND globalTid = first.globalTid
           ORDER BY start ASC
           LIMIT 1
       )
   WHERE first.isSchedIn != 0
   GROUP BY first.globalTid
   ORDER BY total_duration DESC;

   SELECT
       globalTid / 0x1000000 % 0x1000000 AS PID,
       globalTid % 0x1000000 AS TID,
       (SELECT value FROM StringIds where nameId == id) as thread_name,
       ROUND(100.0 * total_duration / (SELECT SUM(total_duration) FROM CPU_USAGE), 2) as CPU_utilization
   FROM CPU_USAGE
   ORDER BY CPU_utilization DESC;
      


   # Python equivalent for scheduling-based calculation:
   def calculate_thread_cpu_time(sched_events):
       cpu_usage = {}
       for tid in unique_tids:
           tid_events = sched_events[sched_events['globalTid'] == tid]
           tid_events = tid_events[tid_events['isSchedIn'] == 1]  # Only sched-in events
           
           total_time = 0
           for i in range(len(tid_events) - 1):
               time_slice = tid_events.iloc[i+1]['start'] - tid_events.iloc[i]['start']
               total_time += time_slice
           
           cpu_usage[tid] = total_time
       return cpu_usage

Results:


   PID         TID         thread_name      CPU_utilization
   ----------  ----------  ---------------  ---------------
   19163       19163       radixSortThrust  93.74          
   19163       19169       radixSortThrust  3.22           
   19163       19168       CUPTI worker th  2.46           
   19163       19166       [NS]             0.44           
   19163       19172       radixSortThrust  0.07           
   19163       19167       [NS Comms]       0.05           
   19163       19176       radixSortThrust  0.02           
   19163       19170       radixSortThrust  0.0
      

**Function Table**

**Goal:** Create profiler-style function tables showing flat view (total time
in each function across all call stacks) and bottom-up view (time spent directly
in each function).

**What the code does:** Processes sampling callchain data to calculate time
spent in functions, providing two views commonly used in profilers.

These examples demonstrate how to calculate Flat and BottomUp (for top level
only) views statistics.

To set up:


   ALTER TABLE SAMPLING_CALLCHAINS ADD COLUMN symbolName TEXT;
   UPDATE SAMPLING_CALLCHAINS SET symbolName = (SELECT value FROM StringIds WHERE symbol = StringIds.id);

   ALTER TABLE SAMPLING_CALLCHAINS ADD COLUMN moduleName TEXT;
   UPDATE SAMPLING_CALLCHAINS SET moduleName = (SELECT value FROM StringIds WHERE module = StringIds.id);
      

To get flat view:

**Flat view:** Shows total time spent in each function across all call stacks (inclusive time).


   SELECT symbolName, moduleName, ROUND(100.0 * sum(cpuCycles) /
       (SELECT SUM(cpuCycles) FROM COMPOSITE_EVENTS), 2) AS flatTimePercentage
   FROM SAMPLING_CALLCHAINS
   LEFT JOIN COMPOSITE_EVENTS ON SAMPLING_CALLCHAINS.id == COMPOSITE_EVENTS.id
   GROUP BY symbol, module
   ORDER BY flatTimePercentage DESC
   LIMIT 5;
      

To get BottomUp view (top level only):

**Bottom-up view:** Shows time spent directly in each function (exclusive time, only leaf functions in call stacks).


   SELECT symbolName, moduleName, ROUND(100.0 * sum(cpuCycles) /
       (SELECT SUM(cpuCycles) FROM COMPOSITE_EVENTS), 2) AS selfTimePercentage
   FROM SAMPLING_CALLCHAINS
   LEFT JOIN COMPOSITE_EVENTS ON SAMPLING_CALLCHAINS.id == COMPOSITE_EVENTS.id
   WHERE stackDepth == 0
   GROUP BY symbol, module
   ORDER BY selfTimePercentage DESC
   LIMIT 5;
      


   # Python equivalent:
   # Flat view - aggregate all occurrences of each function
   flat_view = callchains.groupby(['symbol', 'module'])['cpuCycles'].sum()
   flat_percentages = (flat_view / total_cycles * 100).sort_values(ascending=False)
   
   # Bottom-up view - only leaf nodes (stackDepth == 0)
   leaf_functions = callchains[callchains['stackDepth'] == 0]
   bottomup_view = leaf_functions.groupby(['symbol', 'module'])['cpuCycles'].sum()

Results:


   symbolName   moduleName   flatTimePercentage
   -----------  -----------  ------------------
   [Max depth]  [Max depth]  99.92             
   thrust::zip  /home/user_  24.17             
   thrust::zip  /home/user_  24.17             
   thrust::det  /home/user_  24.17             
   thrust::det  /home/user_  24.17             
   symbolName      moduleName                                   selfTimePercentage
   --------------  -------------------------------------------  ------------------
   0x7fbc984982b6  /usr/lib/x86_64-linux-gnu/libcuda.so.418.39  5.29              
   0x7fbc982d0010  /usr/lib/x86_64-linux-gnu/libcuda.so.418.39  2.81              
   thrust::iterat  /home/<user>/NVIDIA_CUDA-10.1_Samples/6_  2.23              
   thrust::iterat  /home/<user>/NVIDIA_CUDA-10.1_Samples/6_  1.55              
   void thrust::i  /home/<user>/NVIDIA_CUDA-10.1_Samples/6_  1.55
      

**DX12 API Frame Duration Histogram**

**Goal:** Analyze DirectX 12 application frame timing by measuring the duration between consecutive Present calls and creating a timing histogram.

**What the code does:** 
1. Creates a view that pairs consecutive Present calls to calculate frame durations
2. Groups frame durations into millisecond buckets
3. Counts how many frames fall into each duration bucket

The example demonstrates how to calculate DX12 CPU frames durartion and construct a histogram out of it.


   CREATE INDEX DX12_API_ENDTS ON DX12_API (end);

   CREATE TEMP VIEW DX12_API_FPS AS SELECT end AS start,
       (SELECT end FROM DX12_API
           WHERE end > outer.end AND nameId == (SELECT id FROM StringIds
               WHERE value == "IDXGISwapChain::Present")
           ORDER BY end ASC LIMIT 1) AS end
   FROM DX12_API AS outer
       WHERE nameId == (SELECT id FROM StringIds WHERE value == "IDXGISwapChain::Present")
   ORDER BY end;
      

Number of frames with a duration of [X, X + 1] milliseconds.


   SELECT
       CAST((end - start) / 1000000.0 AS INT) AS duration_ms,
       count(*)
   FROM DX12_API_FPS
   WHERE end IS NOT NULL
   GROUP BY duration_ms
   ORDER BY duration_ms;
      


   # Python equivalent:
   present_calls = dx12_api[dx12_api['function_name'] == 'IDXGISwapChain::Present']
   present_calls = present_calls.sort_values('end')
   
   frame_durations = []
   for i in range(len(present_calls) - 1):
       duration = present_calls.iloc[i+1]['end'] - present_calls.iloc[i]['end']
       duration_ms = duration / 1000000.0  # Convert to milliseconds
       frame_durations.append(int(duration_ms))
   
   # Create histogram
   histogram = pd.Series(frame_durations).value_counts().sort_index()

Results:


   duration_ms  count(*)  
   -----------  ----------
   3            1         
   4            2         
   5            7         
   6            153       
   7            19        
   8            116       
   9            16        
   10           8         
   11           2         
   12           2         
   13           1         
   14           4         
   16           3         
   17           2         
   18           1
      

**GPU Context Switch Events Enumeration**

**Goal:** Track GPU context switches to understand GPU scheduling behavior and
identify context switch patterns.

**What the code does:** Filters GPU context switch events to show only BEGIN
(tag=8) and END (tag=7) events, which mark the boundaries of GPU context
execution periods.

**GPU Context Switch Event Tags:**
- **7**: END events (context execution ends)
- **8**: BEGIN events (context execution begins)

GPU context duration is between first BEGIN and a matching END event.


   SELECT (CASE tag WHEN 8 THEN "BEGIN" WHEN 7 THEN "END" END) AS tag,
       globalPid / 0x1000000 % 0x1000000 AS PID,
       vmId, seqNo, contextId, timestamp, gpuId FROM GPU_CONTEXT_SWITCH_EVENTS
   WHERE tag in (7, 8) ORDER BY seqNo LIMIT 10;
      

Results:


   tag         PID         vmId        seqNo       contextId   timestamp   gpuId     
   ----------  ----------  ----------  ----------  ----------  ----------  ----------
   BEGIN       23371       0           0           1048578     56759171    0         
   BEGIN       23371       0           1           1048578     56927765    0         
   BEGIN       23371       0           3           1048578     63799379    0         
   END         23371       0           4           1048578     63918806    0         
   BEGIN       19397       0           5           1048577     64014692    0         
   BEGIN       19397       0           6           1048577     64250369    0         
   BEGIN       19397       0           8           1048577     1918310004  0         
   END         19397       0           9           1048577     1918521098  0         
   BEGIN       19397       0           10          1048577     2024164744  0         
   BEGIN       19397       0           11          1048577     2024358650  0   
      

**Resolve NVTX Category Name**

**Goal:** Decode NVTX category names for NVTX markers and ranges to make the
profiling data more human-readable.

**What the code does:** Joins NVTX events with their category definitions to
resolve category IDs into meaningful category names, making it easier to
understand the purpose of different NVTX annotations.

**NVTX Event Types:**

  *  **33**: Category definition events (define new categories)
  *  **34**: Mark events (instantaneous markers) 
  *  **59**: Push/Pop range events (nested ranges)
  *  **60**: Start/End range events (paired ranges)

The example demonstrates how to resolve NVTX category name for NVTX marks and
ranges.


   WITH
     event AS (
       SELECT *
       FROM NVTX_EVENTS
       WHERE eventType IN (34, 59, 60) -- mark, push/pop, start/end
     ),
     category AS (
       SELECT
         category,
         domainId,
         text AS categoryName
       FROM NVTX_EVENTS
       WHERE eventType == 33 -- category definition events
     )
   SELECT
     start,
     end,
     globalTid,
     eventType,
     domainId,
     category,
     categoryName,
     text
   FROM event JOIN category USING (category, domainId)
   ORDER BY start;
      

Results:


   start       end         globalTid        eventType   domainId    category    categoryName               text            
   ----------  ----------  ---------------  ----------  ----------  ----------  -------------------------  ----------------
   18281150    18311960    281534938484214  59          0           1           FirstCategoryUnderDefault  Push Pop Range A
   18288187    18306674    281534938484214  59          0           2           SecondCategoryUnderDefaul  Push Pop Range B
   18294247                281534938484214  34          0           1           FirstCategoryUnderDefault  Mark A          
   18300034                281534938484214  34          0           2           SecondCategoryUnderDefaul  Mark B          
   18345546    18372595    281534938484214  60          1           1           FirstCategoryUnderMyDomai  Start End Range 
   18352924    18378342    281534938484214  60          1           2           SecondCategoryUnderMyDoma  Start End Range 
   18359634                281534938484214  34          1           1           FirstCategoryUnderMyDomai  Mark A          
   18365448                281534938484214  34          1           2           SecondCategoryUnderMyDoma  Mark B 
      

**Rename CUDA Kernels with NVTX**

**Goal:** Associate CUDA kernels with their surrounding NVTX ranges to provide
more meaningful names and context for kernel analysis.

**What the code does:** 
1. Finds the innermost NVTX push-pop range that encompasses each CUDA kernel launch
2. Maps the NVTX range text to the corresponding kernel execution
3. Enables analysis of kernels by their logical function rather than just their technical names

The example demonstrates how to map innermost NVTX push-pop range to a matching CUDA kernel run.


   ALTER TABLE CUPTI_ACTIVITY_KIND_KERNEL ADD COLUMN nvtxRange TEXT;
   CREATE INDEX nvtx_start ON NVTX_EVENTS (start);


   UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET nvtxRange = (
       SELECT NVTX_EVENTS.text
       FROM NVTX_EVENTS JOIN CUPTI_ACTIVITY_KIND_RUNTIME ON
           NVTX_EVENTS.eventType == 59 AND
           NVTX_EVENTS.globalTid == CUPTI_ACTIVITY_KIND_RUNTIME.globalTid AND
           NVTX_EVENTS.start <= CUPTI_ACTIVITY_KIND_RUNTIME.start AND
           NVTX_EVENTS.end >= CUPTI_ACTIVITY_KIND_RUNTIME.end
       WHERE
           CUPTI_ACTIVITY_KIND_KERNEL.correlationId == CUPTI_ACTIVITY_KIND_RUNTIME.correlationId
       ORDER BY NVTX_EVENTS.start DESC LIMIT 1
   );

   SELECT start, end, globalPid, StringIds.value as shortName, nvtxRange
   FROM CUPTI_ACTIVITY_KIND_KERNEL JOIN StringIds ON shortName == id
   ORDER BY start LIMIT 6;
      


   # Python equivalent:
   def find_innermost_nvtx_range(kernel_start, kernel_end, nvtx_ranges):
       # Find NVTX ranges that completely contain the kernel
       containing_ranges = []
       for nvtx in nvtx_ranges:
           if nvtx['start'] <= kernel_start and nvtx['end'] >= kernel_end:
               containing_ranges.append(nvtx)
       
       # Return the innermost (latest starting) range
       if containing_ranges:
           return max(containing_ranges, key=lambda x: x['start'])['text']
       return None

Results:


   start       end         globalPid          shortName      nvtxRange 
   ----------  ----------  -----------------  -------------  ----------
   526545376   526676256   72057700439031808  MatrixMulCUDA            
   526899648   527030368   72057700439031808  MatrixMulCUDA  Add       
   527031648   527162272   72057700439031808  MatrixMulCUDA  Add       
   527163584   527294176   72057700439031808  MatrixMulCUDA  My Kernel 
   527296160   527426592   72057700439031808  MatrixMulCUDA  My Range  
   527428096   527558656   72057700439031808  MatrixMulCUDA   
      

**Select CUDA Calls With Backtraces**

**Goal:** Analyze CUDA API calls along with their call stacks to understand the
application code paths that lead to CUDA API usage.

**What the code does:** Joins CUDA runtime API calls with their associated call
chains to show the complete stack trace for each CUDA call, helping identify
where in the application CUDA calls originate.


   ALTER TABLE CUPTI_ACTIVITY_KIND_RUNTIME ADD COLUMN name TEXT;
   UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET name = (SELECT value FROM StringIds WHERE CUPTI_ACTIVITY_KIND_RUNTIME.nameId = StringIds.id);

   ALTER TABLE CUDA_CALLCHAINS ADD COLUMN symbolName TEXT;
   UPDATE CUDA_CALLCHAINS SET symbolName = (SELECT value FROM StringIds WHERE symbol = StringIds.id);

   SELECT globalTid % 0x1000000 AS TID,
       start, end, name, callchainId, stackDepth, symbolName
   FROM CUDA_CALLCHAINS JOIN CUPTI_ACTIVITY_KIND_RUNTIME ON callchainId == CUDA_CALLCHAINS.id
   ORDER BY callchainId, stackDepth LIMIT 11;
      

Results:


   TID         start       end         name           callchainId  stackDepth  symbolName    
   ----------  ----------  ----------  -------------  -----------  ----------  --------------
   11928       168976467   169077826   cuMemAlloc_v2  1            0           0x7f13c44f02ab
   11928       168976467   169077826   cuMemAlloc_v2  1            1           0x7f13c44f0b8f
   11928       168976467   169077826   cuMemAlloc_v2  1            2           0x7f13c44f3719
   11928       168976467   169077826   cuMemAlloc_v2  1            3           cuMemAlloc_v2 
   11928       168976467   169077826   cuMemAlloc_v2  1            4           cudart::driver
   11928       168976467   169077826   cuMemAlloc_v2  1            5           cudart::cudaAp
   11928       168976467   169077826   cuMemAlloc_v2  1            6           cudaMalloc    
   11928       168976467   169077826   cuMemAlloc_v2  1            7           cudaError cuda
   11928       168976467   169077826   cuMemAlloc_v2  1            8           main          
   11928       168976467   169077826   cuMemAlloc_v2  1            9           __libc_start_m
   11928       168976467   169077826   cuMemAlloc_v2  1            10          _start  
      

**SLI Peer-to-Peer Query**

**Goal:** Filter and analyze SLI (Scalable Link Interface) peer-to-peer memory
transfers between GPUs based on size, timing, and other criteria.

**What the code does:** Demonstrates how to query SLI P2P events with filtering
conditions on resource size, time range, and sorting by transfer size to
identify significant GPU-to-GPU transfers.

**SLI P2P Event Classes:**
- **62**: Peer-to-peer transfer events between GPUs

The example demonstrates how to query SLI Peer-to-Peer events with resource size
greater than value and within a time range sorted by resource size descending.


   SELECT *
   FROM SLI_P2P
   WHERE resourceSize < 98304 AND start > 1568063100 AND end < 1579468901
   ORDER BY resourceSize DESC;
      


   # Python equivalent:
   filtered_transfers = sli_p2p[
       (sli_p2p['resourceSize'] < 98304) &
       (sli_p2p['start'] > 1568063100) &
       (sli_p2p['end'] < 1579468901)
   ].sort_values('resourceSize', ascending=False)

Results:


   start       end         eventClass  globalTid          gpu         frameId     transferSkipped  srcGpu      dstGpu      numSubResources  resourceSize  subResourceIdx  smplWidth   smplHeight  smplDepth   bytesPerElement  dxgiFormat  logSurfaceNames  transferInfo  isEarlyPushManagedByNvApi  useAsyncP2pForResolve  transferFuncName  regimeName  debugName   bindType  
   ----------  ----------  ----------  -----------------  ----------  ----------  ---------------  ----------  ----------  ---------------  ------------  --------------  ----------  ----------  ----------  ---------------  ----------  ---------------  ------------  -------------------------  ---------------------  ----------------  ----------  ----------  ----------
   1570351100  1570351101  62          72057698056667136  0           771         0                256         512         1                1048576       0               256         256         1           16               2                            3             0                          0                                                                          
   1570379300  1570379301  62          72057698056667136  0           771         0                256         512         1                1048576       0               64          64          64          4                31                           3             0                          0                                                                          
   1572316400  1572316401  62          72057698056667136  0           773         0                256         512         1                1048576       0               256         256         1           16               2                            3             0                          0                                                                          
   1572345400  1572345401  62          72057698056667136  0           773         0                256         512         1                1048576       0               64          64          64          4                31                           3             0                          0                                                                          
   1574734300  1574734301  62          72057698056667136  0           775         0                256         512         1                1048576       0               256         256         1           16               2                            3             0                          0                                                                          
   1574767200  1574767201  62          72057698056667136  0           775         0                256         512         1                1048576       0               64          64          64          4                31                           3             0                          0                                                                          
      

**Generic Events**

**Goal:** Analyze system-level events captured through generic event collection (like ftrace) to understand system behavior and syscall patterns.

**What the code does:** Demonstrates how to query generic events stored in JSON format, specifically showing how to create a histogram of syscall usage by process ID. The query uses a subquery to find the specific event type ID for "raw_syscalls:sys_enter" events, then counts occurrences by process ID.

Syscall usage histogram by PID:


   SELECT json_extract(data, '$.common_pid') AS PID, count(*) AS total
   FROM GENERIC_EVENTS WHERE PID IS NOT NULL AND typeId = (
     SELECT typeId FROM GENERIC_EVENT_TYPES
     WHERE json_extract(data, '$.Name') = "raw_syscalls:sys_enter")
   GROUP BY PID
   ORDER BY total DESC
   LIMIT 10;
      


   # Python equivalent:
   import json
   
   # Filter for syscall enter events
   syscall_events = []
   for event in generic_events:
       data = json.loads(event['data'])
       if 'common_pid' in data:
           syscall_events.append(data['common_pid'])
   
   # Count syscalls by PID
   pid_counts = pd.Series(syscall_events).value_counts().head(10)

Results:


   PID         total     
   ----------  ----------
   5551        32811     
   9680        3988      
   4328        1477      
   9564        1246      
   4376        1204      
   4377        1167      
   4357        656       
   4355        655       
   4356        640       
   4354        633
      

**Fetching Generic Events in JSON Format**

**Goal:** Export generic events, types, and sources in JSON format for external
analysis tools or custom processing pipelines.

**What the code does:** Constructs JSON objects from the database tables
containing generic event data, enabling export to JSON Lines format for further
processing with external tools.

Use the below queries (without the LIMIT clause) to extract JSON lines
representation of generic events, types, and sources.


   SELECT json_insert('{}',
       '$.sourceId', sourceId,
       '$.data', json(data)
   )
   FROM GENERIC_EVENT_SOURCES LIMIT 2;

   SELECT json_insert('{}',
       '$.typeId', typeId,
       '$.sourceId', sourceId,
       '$.data', json(data)
   )
   FROM GENERIC_EVENT_TYPES LIMIT 2;

   SELECT json_insert('{}',
       '$.rawTimestamp', rawTimestamp,
       '$.timestamp', timestamp,
       '$.typeId', typeId,
       '$.data', json(data)
   )
   FROM GENERIC_EVENTS LIMIT 2;
      

Results:


   json_insert('{}',
       '$.sourceId', sourceId,
       '$.data', json(data)
## )
   {"sourceId":72057602627862528,"data":{"Name":"FTrace","TimeSource":"ClockMonotonicRaw","SourceGroup":"FTrace"}}
   json_insert('{}',
       '$.typeId', typeId,
       '$.sourceId', sourceId,
       '$.data', json(data)
## )
   {"typeId":72057602627862547,"sourceId":72057602627862528,"data":{"Name":"raw_syscalls:sys_enter","Format":"\"NR %ld (%lx, %lx, %lx, %lx, %lx, %lx)\", REC->id, REC->args[0], REC->args[1], REC->args[2], REC->args[3], REC->args[4], REC->args[5]","Fields":[{"Name":"common_pid","Prefix":"int","Suffix":""},{"Name":"id","Prefix":"long","S
   {"typeId":72057602627862670,"sourceId":72057602627862528,"data":{"Name":"irq:irq_handler_entry","Format":"\"irq=%d name=%s\", REC->irq, __get_str(name)","Fields":[{"Name":"common_pid","Prefix":"int","Suffix":""},{"Name":"irq","Prefix":"int","Suffix":""},{"Name":"name","Prefix":"__data_loc char[]","Suffix":""},{"Name":"common_type",
   json_insert('{}',
       '$.rawTimestamp', rawTimestamp,
       '$.timestamp', timestamp,
       '$.typeId', typeId,
       '$.data', json(data)
## )
   {"rawTimestamp":1183694330725221,"timestamp":6236683,"typeId":72057602627862670,"data":{"common_pid":"0","irq":"66","name":"327696","common_type":"142","common_flags":"9","common_preempt_count":"0"}}
   {"rawTimestamp":1183694333695687,"timestamp":9207149,"typeId":72057602627862670,"data":{"common_pid":"0","irq":"66","name":"327696","common_type":"142","common_flags":"9","common_preempt_count":"0"}}
