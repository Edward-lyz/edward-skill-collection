---
source_path: AnalysisGuide/topics/file_access_sum-recipe.rst
title: ## file_access_sum Recipe
---
## file_access_sum Recipe

This recipe analyzes file access patterns and I/O performance statistics from one or more Nsight Systems reports,
aggregating data across processes and machines.

**Overview**

The file_access_sum recipe generates an interactive Jupyter notebook that analyzes POSIX VFS (Virtual File System) function calls
captured during profiling sessions. This analysis helps identify I/O bottlenecks, optimization opportunities, and file access patterns
that could impact application performance.

**Key Capabilities**

The recipe provides insights into:

- **File Access Patterns**: Breakdown of read-only, write-only, and read-write file access patterns.
- **Performance Metrics**: Total bytes transferred, operation counts, and average I/O sizes per operation.
- **Cross-Process Analysis**: File access patterns across multiple hosts, processes, and threads.
- **Temporal Analysis**: Distribution of CPU time by operation type.
- **Hotspot Identification**: Top files by read/write volume and operation frequency.
- **Performance Recommendations**: Automated detection of potentially inefficient I/O patterns with actionable suggestions.

**Use Cases**

The recipe is particularly valuable for identifying and addressing the following scenarios (but not limited to these):

1. **I/O Patterns**: Understanding application I/O behavior to uncover usage trends and inefficiencies.
2. **Small I/O Operations**: Detection of frequent small read/write operations that could benefit from batching.
3. **Caching Opportunities**: Identification of frequently accessed read-only files that are candidates for local caching.
4. **Metadata Contention**: Identifying cases where frequent metadata operations by one process may cause contention, impacting storage access for other processes.
5. **System File Noise**: Filtering out system files (/dev/, /sys/, etc.) to focus on application-relevant I/O.

**Prerequisites**

This recipe requires that Nsight Systems reports be collected with specific tracing parameters:

- ``--trace=osrt`` - Enables OS Runtime API tracing
- ``--osrt-file-access=true`` - Enables file access tracking
- **Optional:** To enable tracing of MPI rank information, use ``--trace=mpi`` along with either ``--mpi-impl=openmpi`` or ``--mpi-impl=mpich``.
- **Optional:** To enable the NVTX range correlation table, instrument your application code with NVTX ranges. See Marking and Labeling Regions  in the User Guide.

**Usage**


   [1] Create a reports folder.
   [2] Collect nsys-rep reports, using '--trace=osrt' and '--osrt-file-access=true' parameters, and save them to the reports folder.
   [3] Run the recipe, using 'nsys recipe file_access_sum --input [reports folder path]'.

**Output**

As the main output, the recipe generates an interactive Jupyter notebook
``file_access_stats.ipynb`` with the following sections:

-   File Access Summary Table:
           :alt: File Access Recipe: Summary Table. Provides high level overview of file access patterns.
           :class: image

-   Hottest Read/Write Files Tables:
           :alt: File Access Recipe: Hottest Read/Write Files Tables. Provides top 10 files with the highest read/write activity in the system.
           :class: image

-   All Files Table:
           :alt: File Access Recipe: All Files Table. provides a detailed breakdown of file access patterns for each individual file in the system
           :class: image

-   Read/Write Access Histogram:
           :alt: File Access Recipe: Read/Write Access Histogram. Provides a histogram of read/write operation sizes.
           :class: image

-   CPU Time Graph:
           :alt: File Access Recipe: CPU Time Graph. Provides a graph of CPU time distribution.
           :class: image

-   Operations Count Chart:
           :alt: File Access Recipe: Operations Count Chart. Charts the number of operations for each operation type.
           :class: image

-   Performance Analysis:
           :alt: File Access Recipe: Performance Analysis. Provides a performance analysis of the application.
           :class: image
-   NVTX Ranges Analysis:
           :alt: File Access Recipe: NVTX Ranges Analysis. Provides aggregate statistics for each NVTX range across all its instances.
           :class: image

**Recommended Workflow**
  - Start by setting file path ignore patterns to exclude system files from analysis.
  - Focus on application-specific files during the analysis by using regex filtering.
  - View the Nsight Systems report file alongside this analysis to gain a deeper understanding of the application's behavior.
