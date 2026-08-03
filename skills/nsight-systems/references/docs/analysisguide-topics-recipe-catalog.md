---
source_path: AnalysisGuide/topics/recipe-catalog.rst
title: ## Recipe Catalog and Sample Results
---
## Recipe Catalog and Sample Results

Post-Collection Analysis enables deep insights into GPU application performance
through a curated set of analysis recipes. Each recipe generates specialized
visualizations and data summaries from profiling data collected during
application execution.

This catalog documents all available recipes, their output formats, and sample
results from profiling Llama-70B inference on 8 NVIDIA H100 GPUs using the
NVIDIA Dynamo framework.

The recipes are organized by functionality:

- CUDA API Recipes: Analyze CUDA kernel launches, memory operations, and
  synchronization.
- GPU Kernel Recipes: Examine kernel execution times, duration distribution, and
  pacing.
- NVTX Recipes: Analyze application-level instrumentation ranges.
- Communication Recipes: Study multi-GPU communication patterns, including NCCL
  and NVLink.
- System Recipes: Review OS runtime and I/O operations.
- Comparison Recipes: Compare results between different profiling runs.

Each recipe includes sample data tables and visualization mockups representative
of real profiling results. 


### CUDA API Recipes


**CUDA API Summary**

Summarizes CUDA API calls by frequency and execution time. Identifies the most
time-consuming CUDA operations.

**Output Format:** Summary table, top items bar chart, and duration distribution
box plot.

   :header-rows: 1

   * - API Function
     - Call Count
     - Total Time (us)
     - Avg Time (us)
     - Max Time (us)
   * - cudaMemcpy
     - 2850
     - 125400.5
     - 43.98
     - 650.2
   * - cudaLaunchKernel
     - 5600
     - 85300.2
     - 15.23
     - 420.5
   * - cudaDeviceSynchronize
     - 280
     - 34520.0
     - 123.29
     - 850.3
   * - cudaMemset
     - 450
     - 12350.8
     - 27.45
     - 180.1
   * - cudaMalloc
     - 125
     - 8900.3
     - 71.20
     - 340.2

   :alt: CUDA API Summary chart
   :width: 100%


**CUDA Synchronization APIs**

Advisory analysis identifying synchronization bottlenecks and suggesting
optimization strategies.

**Output Format:** Advisory table with severity levels and recommendations.

   :header-rows: 1

   * - Issue
     - Severity
     - Count
     - Total Impact (us)
     - Recommendation
   * - Implicit Synchronization
     - HIGH
     - 45
     - 28500
     - Use async transfers with events
   * - Unnecessary cudaDeviceSynchronize
     - MEDIUM
     - 28
     - 12300
     - Replace with stream events
   * - Blocking Memory Transfers
     - MEDIUM
     - 156
     - 45200
     - Use pinned memory for H2D

#### CUDA GPU Kernel Recipes


**CUDA GPU Kernel Summary**

Comprehensive summary of GPU kernels executed. Shows kernel names, execution
counts, and timing statistics.

**Output Format:** Summary table, top kernels bar chart, and duration
distribution box plot.

   :header-rows: 1

   * - Kernel Name
     - Launch Count
     - Total Time (us)
     - Avg Time (us)
     - Max Time (us)
   * - volta_sgemm_128x64_nn
     - 8400
     - 2845320.0
     - 338.73
     - 4250.2
   * - attention_forward_kernel
     - 2800
     - 1950200.5
     - 696.50
     - 2850.3
   * - layernorm_forward_kernel
     - 2800
     - 892340.2
     - 318.69
     - 1620.5
   * - fused_mlp_kernel
     - 2800
     - 756200.1
     - 270.07
     - 1450.2
   * - nccl_AllReduce_Ring_LL_Sum_f16
     - 560
     - 680450.3
     - 1214.20
     - 3200.1

   :alt: CUDA GPU Kernel Summary chart
   :width: 100%


**CUDA GPU Kernel Duration Histogram**

Distribution of kernel execution durations. Shows frequency of kernels across
different execution time ranges.

**Output Format:** Histogram with distribution statistics and percentile markers.

   :header-rows: 1

   * - Duration Range (us)
     - Frequency
     - Percentage
     - Cumulative %
   * - 100-500
     - 1240
     - 8.2%
     - 8.2%
   * - 500-1000
     - 2850
     - 18.7%
     - 26.9%
   * - 1000-2000
     - 4200
     - 27.5%
     - 54.4%
   * - 2000-4000
     - 3950
     - 25.9%
     - 80.3%
   * - 4000+
     - 2860
     - 18.7%
     - 99.0%

   :alt: CUDA GPU Kernel Duration Histogram chart
   :width: 100%


**CUDA GPU Kernel Pacing**

Consistency analysis of kernel execution times across iterations and GPU ranks.
Identifies pacing irregularities.

**Output Format:** Multi-line chart showing kernel timing per iteration across
all GPU ranks.

   :header-rows: 1

   * - Iteration
     - Rank 0 (us)
     - Rank 1 (us)
     - Rank 2 (us)
     - Rank 3 (us)
     - Avg Variance
   * - 0
     - 1025.3
     - 1048.2
     - 1032.5
     - 1041.8
     - 8.6
   * - 1
     - 1032.8
     - 1055.3
     - 1038.2
     - 1049.5
     - 8.9
   * - 2
     - 1038.5
     - 1062.1
     - 1044.8
     - 1055.2
     - 9.2
   * - 3
     - 1035.2
     - 1058.9
     - 1040.5
     - 1051.8
     - 8.7

   :alt: CUDA GPU Kernel Pacing chart
   :width: 100%


#### CUDA Memory Operations Recipes


**CUDA GPU MemOps Summary (by Size)**

Memory transfer operations grouped by transfer size. Analyzes efficiency of
data movement.

**Output Format:** Summary table, size distribution bar chart, and timing box
plot.

   :header-rows: 1

   * - Size Range (MB)
     - Transfer Count
     - Total Data (GB)
     - Avg Time (us)
     - Bandwidth (GB/s)
   * - <1
     - 8450
     - 5.2
     - 125.3
     - 41.5
   * - 1-10
     - 3200
     - 18.5
     - 450.2
     - 41.0
   * - 10-100
     - 850
     - 42.3
     - 1850.5
     - 22.8
   * - 100-1000
     - 280
     - 156.8
     - 8520.3
     - 18.4
   * - 1000+
     - 45
     - 234.5
     - 25300.2
     - 9.3

   :alt: CUDA GPU MemOps Summary by Size chart
   :width: 100%


**CUDA GPU MemOps Summary (by Time)**

Memory operations sorted by execution time. Identifies most time-consuming
memory transfers.

**Output Format:** Summary table, top operations bar chart, and duration
distribution box plot.

   :header-rows: 1

   * - Operation Type
     - Count
     - Total Time (us)
     - Avg Time (us)
     - Max Time (us)
   * - H2D Copy
     - 4200
     - 285400.2
     - 67.95
     - 850.3
   * - D2H Copy
     - 3850
     - 256300.5
     - 66.57
     - 720.2
   * - D2D Copy
     - 2950
     - 156800.3
     - 53.15
     - 580.1
   * - Memset
     - 450
     - 12350.8
     - 27.45
     - 180.5

   :alt: CUDA GPU MemOps Summary by Time chart
   :width: 100%


**CUDA Synchronous Memcpy**

Advisory for synchronous memory copies that may impact performance.

**Output Format:** Advisory table with impact analysis and optimization
suggestions.

   :header-rows: 1

   * - Transfer Pattern
     - Count
     - Total Time (us)
     - Severity
     - Suggestion
   * - Pageable H2D
     - 1250
     - 145200
     - HIGH
     - Use cuda-pinned memory
   * - Pageable D2H
     - 1100
     - 128500
     - HIGH
     - Implement async with streams
   * - Device Sync
     - 280
     - 34500
     - MEDIUM
     - Use cudaEventSynchronize


#### GPU Utilization Recipes


**GPU Metrics Utilization Summary**

High-level metrics showing GPU resource utilization, including SM, Memory,
Tensor Cores, and related metrics.

**Output Format:** Summary table, metric utilization bar chart, and distribution
box plot.

   :header-rows: 1

   * - Metric
     - Avg Util (%)
     - Max Util (%)
     - Peak Time (ms)
     - Stalls
   * - SM Utilization
     - 78.5
     - 95.2
     - 245.3
     - 12
   * - Memory Utilization
     - 65.3
     - 88.1
     - 238.5
     - 28
   * - L1 Cache Hit Rate
     - 82.4
     - 96.1
     - 250.2
     - 5
   * - L2 Cache Hit Rate
     - 74.2
     - 91.3
     - 242.8
     - 18
   * - Tensor Utilization
     - 81.5
     - 94.7
     - 246.1
     - 8

   :alt: GPU Metrics Utilization Summary chart
   :width: 100%


**GPU Metric Utilization Heatmap**

Time-series heatmap showing metric utilization across GPU ranks over profiling
duration.

**Output Format:** 2D heatmap with GPU ranks on the y-axis, time bins on the
x-axis, and utilization percentage color-coded.

   :header-rows: 1

   * - GPU Rank
     - T0-T100 (%)
     - T100-T200 (%)
     - T200-T300 (%)
     - T300-T400 (%)
     - Avg (%)
   * - Rank 0
     - 82
     - 85
     - 79
     - 84
     - 82.5
   * - Rank 1
     - 80
     - 83
     - 78
     - 82
     - 80.8
   * - Rank 2
     - 81
     - 84
     - 80
     - 85
     - 82.5
   * - Rank 3
     - 79
     - 82
     - 77
     - 81
     - 79.8

   :alt: GPU Metric Utilization Heatmap chart
   :width: 100%


**Graphics VRAM Usage**

Memory allocation and deallocation trace showing VRAM consumption over time.

**Output Format:** Time-series line chart with peak VRAM markers and allocation
events.

   :header-rows: 1

   * - Time (ms)
     - Allocated (MB)
     - Free (MB)
     - Total GPU Mem (MB)
     - Peak Usage (%)
   * - 0
     - 2048
     - 77952
     - 80000
     - 2.6%
   * - 100
     - 8192
     - 71808
     - 80000
     - 10.2%
   * - 200
     - 24576
     - 55424
     - 80000
     - 30.7%
   * - 300
     - 38912
     - 41088
     - 80000
     - 48.6%
   * - 400
     - 42048
     - 37952
     - 80000
     - 52.6%

   :alt: Graphics VRAM Usage chart
   :width: 100%


**GPU Time Utilization**

Advisory on GPU idle time, gaps, and utilization efficiency.

**Output Format:** Advisory table with gap analysis and improvement suggestions.

   :header-rows: 1

   * - GPU
     - Active Time (ms)
     - Idle Time (ms)
     - Util (%)
     - Largest Gap (us)
     - Recommendation
   * - GPU 0
     - 485.2
     - 14.8
     - 96.8%
     - 2850
     - Excellent utilization
   * - GPU 1
     - 478.5
     - 21.5
     - 95.7%
     - 3200
     - Minor gaps detected
   * - GPU 2
     - 475.3
     - 24.7
     - 95.1%
     - 3850
     - Check kernel dependencies
   * - GPU 3
     - 472.8
     - 27.2
     - 94.6%
     - 4100
     - Optimize host-device sync


**GPU Gaps**

Identifies periods of GPU inactivity and analyzes root causes.

**Output Format:** Gap summary table with timeline and impact analysis.

   :header-rows: 1

   * - Gap ID
     - Start (us)
     - Duration (us)
     - GPU
     - Probable Cause
     - Impact
   * - Gap_001
     - 125340
     - 2850
     - GPU 0
     - Host-Device Sync
     - Kernel stall
   * - Gap_002
     - 245820
     - 3200
     - GPU 1
     - Memory Transfer
     - Pipeline flush
   * - Gap_003
     - 385500
     - 1950
     - GPU 2
     - Context Switch
     - Minor impact
   * - Gap_004
     - 458200
     - 4100
     - GPU 3
     - Host Queue Latency
     - Kernel delay


#### NVTX Range Recipes


**NVTX Range Summary**

Summary of NVIDIA Tools eXtension (NVTX) instrumentation ranges in application code.

**Output Format:** Summary table, top ranges bar chart, and duration distribution box plot.

   :header-rows: 1

   * - Range Name
     - Count
     - Total Time (us)
     - Avg Time (us)
     - Max Time (us)
   * - forward_pass
     - 280
     - 1850320.5
     - 6608.29
     - 8520.3
   * - attention_compute
     - 2800
     - 950200.2
     - 339.36
     - 2850.1
   * - mlp_compute
     - 2800
     - 756300.8
     - 270.11
     - 1520.2
   * - backward_pass
     - 280
     - 1420500.3
     - 5073.21
     - 7250.3
   * - parameter_update
     - 280
     - 385200.1
     - 1375.71
     - 2100.5

   :alt: NVTX Range Summary chart
   :width: 100%


**NVTX Pacing**

Pacing consistency analysis of NVTX ranges across iterations.

**Output Format:** Multi-line chart showing range timing per iteration across
GPU ranks.

   :header-rows: 1

   * - Iteration
     - Rank 0 (us)
     - Rank 1 (us)
     - Rank 2 (us)
     - Rank 3 (us)
     - Std Dev
   * - 0
     - 6580.2
     - 6625.8
     - 6590.5
     - 6612.3
     - 15.8
   * - 1
     - 6598.5
     - 6642.1
     - 6608.2
     - 6630.5
     - 16.2
   * - 2
     - 6612.3
     - 6658.9
     - 6622.8
     - 6645.2
     - 16.8
   * - 3
     - 6625.8
     - 6672.5
     - 6638.5
     - 6660.1
     - 17.3

   :alt: NVTX Pacing chart
   :width: 100%


**NVTX GPU Projection Summary**

GPU utilization projection for NVTX ranges. Shows estimated GPU time within each
range.

**Output Format:** Summary table with GPU projection metrics, bar chart, and box
plot.

   :header-rows: 1

   * - Range Name
     - GPU Time (us)
     - Total Time (us)
     - GPU %
     - Kernel Calls
   * - forward_pass
     - 1750280.3
     - 1850320.5
     - 94.6%
     - 2850
   * - attention_compute
     - 905200.5
     - 950200.2
     - 95.3%
     - 2800
   * - mlp_compute
     - 725300.2
     - 756300.8
     - 95.9%
     - 2800
   * - backward_pass
     - 1385400.1
     - 1420500.3
     - 97.5%
     - 2800
   * - parameter_update
     - 370200.8
     - 385200.1
     - 96.1%
     - 280

   :alt: NVTX GPU Projection Summary chart
   :width: 100%


**NVTX GPU Projection Pacing**

Consistency of GPU utilization for NVTX ranges across iterations and ranks.

**Output Format:** Multi-line pacing chart with GPU projection metrics.

   :alt: NVTX GPU Projection Pacing chart
   :width: 100%


**NVTX GPU Projection Trace**

Detailed trace showing compute versus communication overlap within NVTX ranges.

**Output Format:** Overlap matrix and timeline visualization.

   :header-rows: 1

   * - Range
     - Compute (us)
     - Comm (us)
     - Overlap (us)
     - Overlap %
   * - forward_pass
     - 1650280
     - 185320
     - 152850
     - 82.5%
   * - attention_compute
     - 850200
     - 120200
     - 98560
     - 82.0%
   * - mlp_compute
     - 725300
     - 95300
     - 78520
     - 82.5%
   * - backward_pass
     - 1285400
     - 210500
     - 172450
     - 81.9%
   * - parameter_update
     - 285200
     - 65200
     - 52850
     - 81.0%

   :alt: NVTX GPU Projection Trace chart
   :width: 100%


#### Communication & NCCL Recipes


**NCCL Summary**

Full-run summary of NVIDIA Collective Communications Library (NCCL)
communication. The report shows communicators, ranks, operations, message-size
buckets, datatypes, and rank-local operation counts and costs. With advanced
NCCL tracing, collective and P2P GPU operations are summarized directly.

**Output Format:** Communicator/rank table, operation/datatype/message-size
summary table, operation count and timing box plots, and rank-local count and
timing box plots.

   :header-rows: 1

   * - Operation
     - Count
     - Total Time (us)
     - Avg Time (us)
     - Max Time (us)
   * - AllReduce
     - 560
     - 680450.3
     - 1214.20
     - 3200.1
   * - ReduceScatter
     - 560
     - 520300.5
     - 928.75
     - 2850.2
   * - AllGather
     - 560
     - 485200.2
     - 866.07
     - 2520.3
   * - Broadcast
     - 280
     - 185300.8
     - 661.79
     - 1850.2
   * - Barrier
     - 560
     - 125400.1
     - 223.93
     - 620.5

   :alt: NCCL Summary chart
   :width: 100%


**NCCL GPU Projection Summary**

GPU utilization during NCCL operations. Breaks down compute versus
communication time. For advanced NCCL tracing, use NCCL Summary instead
because GPU projection is unnecessary.

**Output Format:** Summary table with GPU projection, bar chart, and box plot.

   :header-rows: 1

   * - NCCL Op
     - GPU Time (us)
     - Total Time (us)
     - GPU Util %
     - Rank Participation
   * - AllReduce
     - 645200.2
     - 680450.3
     - 94.8%
     - 8
   * - ReduceScatter
     - 485300.1
     - 520300.5
     - 93.3%
     - 8
   * - AllGather
     - 450200.3
     - 485200.2
     - 92.8%
     - 8
   * - Broadcast
     - 175300.5
     - 185300.8
     - 94.6%
     - 8
   * - Barrier
     - 118200.2
     - 125400.1
     - 94.3%
     - 8

   :alt: NCCL GPU Projection Summary chart
   :width: 100%


**NCCL GPU Time Utilization Heatmap**

Time-series heatmap of GPU utilization during NCCL operations across all ranks.

**Output Format:** 2D heatmap with GPU ranks on the y-axis and time bins on the
x-axis.

   :header-rows: 1

   * - GPU Rank
     - T0 (%)
     - T1 (%)
     - T2 (%)
     - T3 (%)
     - Avg (%)
   * - Rank 0
     - 92
     - 94
     - 93
     - 95
     - 93.5
   * - Rank 1
     - 90
     - 92
     - 91
     - 93
     - 91.5
   * - Rank 2
     - 91
     - 93
     - 92
     - 94
     - 92.5
   * - Rank 3
     - 89
     - 91
     - 90
     - 92
     - 90.5

   :alt: NCCL GPU Time Utilization Heatmap chart
   :width: 100%


**NCCL GPU Overlap Trace**

Overlap analysis between communication and compute during NCCL operations.

**Output Format:** Overlap matrix showing communication overlap percentages
between ranks.

   :header-rows: 1

   * - Op
     - Overlap %
     - Compute Time (us)
     - Comm Time (us)
     - Concurrent Time (us)
   * - AllReduce
     - 78.5
     - 620300
     - 145200
     - 113850
   * - ReduceScatter
     - 76.2
     - 450200
     - 98500
     - 75000
   * - AllGather
     - 74.8
     - 425300
     - 85200
     - 63800
   * - Broadcast
     - 72.5
     - 160300
     - 32500
     - 23600
   * - Barrier
     - 65.3
     - 108200
     - 18500
     - 12100

   :alt: NCCL GPU Overlap Trace chart
   :width: 100%


#### Network & Storage Recipes


**Network Traffic Summary**

Summary of network I/O operations and traffic patterns.

**Output Format:** Summary table, traffic distribution bar chart, and timing box
plot.

   :header-rows: 1

   * - Interface
     - Packets
     - Bytes (MB)
     - Avg Latency (us)
     - Max Latency (us)
   * - eth0
     - 85230
     - 2048.5
     - 125.3
     - 850.2
   * - eth1
     - 75600
     - 1820.3
     - 130.5
     - 920.3
   * - InfiniBand
     - 125400
     - 3200.8
     - 85.2
     - 520.1

   :alt: Network Traffic Summary chart
   :width: 100%


**Network Devices Traffic Heatmap**

Time-series heatmap showing network device utilization over profiling duration.

**Output Format:** 2D heatmap with network devices on the y-axis and time bins
on the x-axis.

   :header-rows: 1

   * - Device
     - T0 (Mb/s)
     - T1 (Mb/s)
     - T2 (Mb/s)
     - T3 (Mb/s)
     - Avg (Mb/s)
   * - eth0
     - 2500
     - 2350
     - 2400
     - 2450
     - 2425
   * - eth1
     - 2200
     - 2100
     - 2150
     - 2200
     - 2162
   * - InfiniBand
     - 3500
     - 3400
     - 3450
     - 3550
     - 3475

   :alt: Network Devices Traffic Heatmap chart
   :width: 100%


**AWS Metrics Heatmap**

CloudWatch metrics heatmap for AWS-deployed systems.

**Output Format:** Heatmap of AWS metrics, including CPU, Memory, and Network,
over time.

   :header-rows: 1

   * - Metric
     - T0 (%)
     - T1 (%)
     - T2 (%)
     - T3 (%)
     - Avg (%)
   * - CPU Util
     - 75
     - 78
     - 76
     - 79
     - 77.0
   * - Memory Util
     - 62
     - 64
     - 63
     - 65
     - 63.5
   * - Network Util
     - 58
     - 60
     - 59
     - 62
     - 59.8

   :alt: AWS Metrics Heatmap chart
   :width: 100%


**Storage Metrics Heatmap**

Storage I/O and utilization metrics over profiling duration.

**Output Format:** Heatmap showing storage device utilization percentages.

   :header-rows: 1

   * - Storage Device
     - T0 (%)
     - T1 (%)
     - T2 (%)
     - T3 (%)
     - Avg (%)
   * - NVMe-0
     - 45
     - 48
     - 46
     - 50
     - 47.25
   * - NVMe-1
     - 42
     - 44
     - 43
     - 46
     - 43.75
   * - HDD-0
     - 28
     - 30
     - 29
     - 32
     - 29.75

   :alt: Storage Metrics Heatmap chart
   :width: 100%


#### System & OS Runtime Recipes


**OS Runtime Summary**

Summary of OS runtime operations including system calls and I/O operations.

**Output Format:** Summary table, operation distribution bar chart, and timing box plot.

   :header-rows: 1

   * - OS Operation
     - Call Count
     - Total Time (us)
     - Avg Time (us)
     - Max Time (us)
   * - read()
     - 1850
     - 28500.3
     - 15.41
     - 250.2
   * - write()
     - 1620
     - 24300.5
     - 15.01
     - 220.3
   * - open()
     - 450
     - 8500.2
     - 18.89
     - 120.5
   * - close()
     - 425
     - 7200.1
     - 16.94
     - 95.2
   * - mmap()
     - 120
     - 4200.8
     - 35.01
     - 180.3

   :alt: OS Runtime Summary chart
   :width: 100%


**Linux File Access Summary**

Specialized analysis of file system access patterns during profiling.

**Output Format:** File access statistics table with I/O patterns.

   :header-rows: 1

   * - File/Path
     - Access Count
     - Bytes Read
     - Bytes Written
     - Total Time (us)
   * - /data/model.bin
     - 250
     - 2048000
     - 0
     - 18500.2
   * - /tmp/cache
     - 1850
     - 512000
     - 256000
     - 12300.5
   * - /proc/stat
     - 450
     - 0
     - 0
     - 2800.3
   * - /dev/null
     - 600
     - 0
     - 1024000
     - 8200.1

   :alt: Linux File Access Summary chart
   :width: 100%


#### NVLink & MPI Recipes


**NVLink Network Throughput Summary**

Summary of NVLink GPU-to-GPU communication throughput and efficiency.

**Output Format:** Summary table, throughput distribution bar chart, and timing box plot.

   :header-rows: 1

   * - Link Pair
     - Transfers
     - Total Data (MB)
     - Total Time (us)
     - Throughput (GB/s)
   * - GPU0-GPU1
     - 450
     - 2048.5
     - 2350.3
     - 871.0
   * - GPU1-GPU2
     - 450
     - 2048.3
     - 2340.2
     - 875.1
   * - GPU2-GPU3
     - 450
     - 2048.1
     - 2360.5
     - 868.2
   * - GPU4-GPU5
     - 450
     - 2048.2
     - 2345.8
     - 873.1
   * - GPU6-GPU7
     - 450
     - 2048.0
     - 2355.2
     - 869.8

   :alt: NVLink Network Throughput Summary chart
   :width: 100%


**MPI Summary**

Summary of Message Passing Interface (MPI) operations and communication patterns.

**Output Format:** Summary table, operation distribution bar chart, and timing
box plot.

   :header-rows: 1

   * - MPI Operation
     - Call Count
     - Total Data (MB)
     - Total Time (us)
     - Avg Time (us)
   * - MPI_Allreduce
     - 560
     - 520.0
     - 680450.3
     - 1214.20
   * - MPI_Reduce
     - 280
     - 280.5
     - 350200.2
     - 1250.71
   * - MPI_Bcast
     - 280
     - 256.2
     - 185300.5
     - 661.79
   * - MPI_Send
     - 1850
     - 850.3
     - 125400.2
     - 67.81
   * - MPI_Recv
     - 1850
     - 850.3
     - 128200.1
     - 69.30

   :alt: MPI Summary chart
   :width: 100%


**MPI and GPU Time Utilization Heatmap**

Correlation heatmap showing GPU utilization during MPI operations across ranks.

**Output Format:** 2D heatmap with MPI ranks on the y-axis and time bins on the
x-axis.

   :header-rows: 1

   * - MPI Rank
     - T0 (%)
     - T1 (%)
     - T2 (%)
     - T3 (%)
     - Avg (%)
   * - Rank 0
     - 88
     - 90
     - 89
     - 92
     - 89.75
   * - Rank 1
     - 86
     - 88
     - 87
     - 90
     - 87.75
   * - Rank 2
     - 87
     - 89
     - 88
     - 91
     - 88.75
   * - Rank 3
     - 85
     - 87
     - 86
     - 89
     - 86.75

   :alt: MPI and GPU Time Utilization Heatmap chart
   :width: 100%


**UCX and GPU Time Utilization Heatmap**

Heatmap showing GPU utilization during UCX (Unified Communication X) operations.

**Output Format:** 2D heatmap with UCX operation types on the y-axis and time
bins on the x-axis.

   :header-rows: 1

   * - UCX Op Type
     - T0 (%)
     - T1 (%)
     - T2 (%)
     - T3 (%)
     - Avg (%)
   * - UCX_Put
     - 82
     - 84
     - 83
     - 86
     - 83.75
   * - UCX_Get
     - 79
     - 81
     - 80
     - 83
     - 80.75
   * - UCX_Atomic
     - 75
     - 77
     - 76
     - 79
     - 76.75

   :alt: UCX and GPU Time Utilization Heatmap chart
   :width: 100%


#### Comparison & Diff Recipes


**Statistics Diff**

Side-by-side comparison of profiling statistics from two different runs.

**Output Format:** Comparison table with Run A versus Run B metrics and
percentage differences.

   :header-rows: 1

   * - Metric
     - Run A
     - Run B
     - Difference
     - Change %
   * - Total GPU Time (s)
     - 485.2
     - 492.5
     - +7.3
     - +1.5%
   * - Avg Kernel Time (us)
     - 338.73
     - 341.25
     - +2.52
     - +0.7%
   * - Memory Bandwidth (GB/s)
     - 750.2
     - 745.8
     - -4.4
     - -0.6%
   * - NCCL Overhead (ms)
     - 125.3
     - 128.5
     - +3.2
     - +2.6%
   * - Peak VRAM (MB)
     - 42048
     - 42512
     - +464
     - +1.1%

   :alt: Statistics Diff chart
   :width: 100%
