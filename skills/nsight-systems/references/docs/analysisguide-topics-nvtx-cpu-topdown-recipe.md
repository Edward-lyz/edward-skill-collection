---
source_path: AnalysisGuide/topics/nvtx_cpu_topdown-recipe.rst
title: ## nvtx_cpu_topdown Recipe
---
## nvtx_cpu_topdown Recipe

This recipe calculates CPU Topdown methodology metrics for NVTX push/pop ranges
based on collected PMU core events for NVIDIA CPUs featuring Arm cores. It can
process multiple Nsight Systems reports.

Currently, the recipe supports NVIDIA Grace (TM) CPUs and NVIDIA DGX Spark
(TM) CPUs.

We recommend using this recipe after running the ``collect_cpu_topdown.sh``
script, which simplifies collecting all PMU core event and metric data needed to
perform a CPU Topdown analysis of the workload's CPU performance. For more
details on this script, refer to the Arm Topdown Analysis section.

If PMU core events other than those required by Topdown are collected, the
recipe will calculate available CPU metrics based on them and display those
metrics in the output.

**Use Case**

The recipe is most useful when the following conditions are met:

1. The application runs on CPU cores supported by the recipe.

2. The application is instrumented with NVTX push/pop ranges.

3. NVTX range spans a specific CPU algorithm / code section that does not make
   syscalls or calls to other libraries whose functions take significant time
   to execute.

4. NVTX ranges with the same name are used to represent the same workload across
   all threads and all repetitions.

5. The duration of the NVTX range is 5 ms or longer to obtain more accurate
   results.

6. In systems with heterogeneous CPU cores, the NVTX range executed on a given
   core type remains consistent across runs, ensuring a reliable view of CPU
   metrics for that range on that core type. For example, to achieve stable
   runs, you can pin the process to specific CPU cores using ``taskset``.

Note:
   For the case of NVTX ranges from multiple threads, only the NVTX ranges from
   either the main thread (default) or the thread specified via ``--thread-name``
   will be processed.

**Usage**


   [1] mkdir reports && cd reports
   [2] <path to target-linux-sbsa-armv8>/CpuProfiling/collect_cpu_topdown.sh ./myApp
   [3] nsys recipe nvtx_cpu_topdown --input .

1. This step creates a new directory to store the reports.
   We recommend using an empty new directory, because the
   ``collect_cpu_topdown.sh`` script overwrites the output files and does
   not currently allow customization of file names.

2. This step creates several report files: cpu-td1.nsys-rep,
   cpu-branch-ipc.nsys-rep, etc.

Note:
      Note that since multiple reports are created, this step can
      take significant time to complete.

3. This step runs the recipe, uses all reports in the current directory as the
   input, and produces a ``.ipynb`` Jupyter notebook, ``.parquet`` and ``.csv``
   (if ``--csv`` is specified) files as the output.

**Output**

As the main output, the recipe generates the Jupyter notebook
``nvtx_cpu_topdown.ipynb`` with the following sections:

-   NVTX Summary for Heterogeneous CPU Cores:
        Displays a summary of NVTX ranges compiled from Nsight Systems
        reports provided to the recipe.

        For a report selected from the drop-down menu, the section shows each
        NVTX range (in call stack order) with its instance count, median*
        instance duration, and CPU time aggregated across heterogeneous cores,
        as well as CPU time per core type - both related to the NVTX instance
        with the median* duration.

        Note: median* is defined as the middle value in the sorted list. For an
        even number of elements, it is the second of the two middle values.

Note:
           This section is available only for data collected from heterogeneous
           CPU cores. For these cores, the remaining sections apply to each CPU
           core type individually and can be toggled using the ``Select CPU Core``
           drop-down menu.

           :alt: NVTX CPU Topdown Recipe: NVTX Summary for Heterogeneous CPU Cores
           :class: image

-   Warnings:
        Displays warnings generated during recipe execution and related to the
        entire recipe output (or to the portion of it specific to a given CPU
        core type). If there are no warnings, this section is not displayed.

-   NVTX Summary:
        Displays a summary of NVTX ranges compiled from Nsight Systems reports
        provided to the recipe.

        For a report selected from the drop-down menu, the section shows each
        NVTX range (in call stack order) with its instance count, median
        duration with median absolute deviation, median CPU time with median
        absolute deviation, and relevant notes.

        If NVTX ranges are filtered out, they are grayed out in the table, and a
        note is displayed in the `Notes` column for the corresponding range.
        The following ranges are candidates to be filtered out:

        -   Ranges that contain fewer than 3 PMU samples in at least one Nsight
            Systems report provided to the recipe.
        -   Ranges that are not present in at least one Nsight Systems report
            provided to the recipe.

        If NVTX ranges are not stable across some of the reports, the section
        will display a warning next to the unstable data and a note in the
        `Notes` column for the corresponding range.

           :alt: NVTX CPU Topdown Recipe: NVTX Summary
           :class: image

-   CPU Topdown Methodology Metrics:
        Presents the metric results of the CPU Topdown methodology
        for the selected NVTX range.

        For the range name selected from the drop-down menu, the most appropriate
        NVTX range instance is identified from the Nsight Systems reports
        as follows:

           **For data collected from heterogeneous CPU cores:** The NVTX range
           instance with the median* CPU time is selected from each report.

           **Otherwise:** The NVTX range instance with the median* duration is
           selected from the first report (displayed by default in the
           `NVTX Summary` section). The corresponding instance index is then used
           to extract data from subsequent reports.

           Note: median* is defined as the middle value in a sorted list. For an
           even number of elements, it is the second of the two middle values.

        The section shows the following tables:

        1. Topdown Level 1 metrics

        2. Frontend Bound metrics

        3. Backend Bound metrics

        4. Bad Speculation metrics

        5. Retiring metrics

        6. Miscellaneous metrics

        Each table is displayed only when the required data is available.

           :alt: NVTX CPU Topdown Recipe: CPU Topdown Methodology Metrics
           :class: image

-   Report Summary:
        Displays information about the Nsight Systems report files
        given to the recipe for input, as well as: the PMU core events collected
        in each specific report, and the CPU core metrics computed for each
        specific report.

           :alt: NVTX CPU Topdown Recipe: Report Summary
           :class: image
