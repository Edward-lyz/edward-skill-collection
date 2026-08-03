---
source_path: AnalysisGuide/topics/gpu_vram_usage_trace-recipe.rst
title: ## gpu_vram_usage_trace Recipe - Preview Feature
---
## gpu_vram_usage_trace Recipe - Preview Feature

This recipe analyzes VRAM usage patterns and statistics from Nsight Systems reports,
helping identify and troubleshoot potential issues in GPU memory management.

**Overview**

The gpu_vram_usage_trace recipe generates an interactive Jupyter notebook that analyzes VRAM usage patterns, such as resource migrations between VRAM and system memory,
and resource allocation and deallocation timing.
This analysis helps identify memory management issues, optimization opportunities, and potential causes of performance degradation related to GPU memory usage.

**Key Capabilities**

The recipe provides insights into:

- **VRAM Usage Tracking**: Per-frame monitoring of VRAM's and SYSMEM's usage, commitment, and budget across all GPU resources.
- **Memory Resource Details**: Comprehensive information for all allocated GPU memory resources.
- **Resource Migrations**: Analysis of resource migration patterns between VRAM and system memory.
- **Frame-by-Frame Analysis & Comparison**: Detailed view of available resources at a specific point in time and comparison to another.
- **Debugging Context Integration**: Correlation of memory resource usage with user-provided performance markers, resource debug names, and callstack information.

**Use Cases**

The recipe is particularly valuable for identifying and addressing the following scenarios (but not limited to these):

1. **VRAM Exhaustion**: Detecting when applications approach or exceed available VRAM limits, and identifying which resources are consuming the available VRAM.
2. **Memory Thrashing**: Identifying excessive resource migrations between VRAM and system memory.
3. **Frame Spikes**: Analyzing frames with abnormal performance due to VRAM usage and/or resource transitions.

**Important Notes**

- **Preview Feature**: This recipe is a preview feature and may be subject to change in the near future.
- **Single Report Only**: This recipe is intended for use with a single report. Using it with multiple reports may cause unexpected behavior.

**Prerequisites**

* **Windows (DirectX 12 and Vulkan)**: This recipe currently supports reports recorded on Windows, using either DirectX 12 or Vulkan.

**Usage**

This recipe requires that Nsight Systems reports be collected with WDDM tracing enabled.

Steps:

1. **Collect an nsys-rep report with WDDM tracing enabled**

   - **With `nsys.exe` (CLI)**: Use the parameters
     `--trace=wddm` together with either `--wddm-memory-trace=true` or `--wddm-additional-events=true`.

   - **With `nsys-ui.exe` (GUI)**:
     Enable the **WDDM Trace** collector, using either the "Collect WDDM memory trace" or
     "Extensive trace including Hardware Scheduling queues..." option.

Note:
      *Optional: To collect additional debug name information on resources (affects the Resident Resources Details section), enable tracing of debug markers as follows:*

      - **For DirectX 12:**

        - With **`nsys-ui.exe` (GUI)**: Enable the **DX12 Trace** collector and the **Trace Debug Markers** option.
        - With **`nsys.exe` (CLI)**: Adjust the trace argument: ``--trace=wddm,dx12-annotations``.

      - **For Vulkan:**

        - With **`nsys-ui.exe` (GUI)**: Enable the **Vulkan Trace** collector and the **Trace Debug Markers** option.
        - With **`nsys.exe` (CLI)**: Adjust the trace argument: ``--trace=wddm,vulkan-annotations``.


2. **Run the recipe**
   ``nsys recipe gpu_vram_usage_trace --input [report file path]``

3. **Open the generated notebook**
   Open the produced `stats.ipynb` Jupyter notebook to view the interactive analysis.


**Output**

As the main output, the recipe generates an interactive Jupyter notebook
``stats.ipynb`` with the following sections:


-   Global Process and GPU Selectors:
           :alt: Dropdown controls to filter analysis by a specific process and GPU device.
                 The table beneath the selectors displays memory usage statistics for the selection.
           :class: image

-   Interactive Timeline Charts:
           :alt: A 2x2 grid of synchronized interactive charts showing frame duration, VRAM usage, SYSMEM usage, and memory transitions.
                 The charts support dual frame selection (left/right) for investigation and comparison in later sections.
           :class: image

-   Resident Resources Diff Tables:
           :alt: Two side-by-side tables showing resources in VRAM and SYSMEM during the selected frames.
                 A chart above each table allows selection of a specific timestamp within the selected frames.
           :class: image

-   Resident Resources Details Section:
           :alt: Resources within the Resident Resources tables can be selected for additional details.
           :class: image

-   All Allocations Table:
           :alt: Comprehensive table of all GPU resource allocations during the entire duration of the report.
           :class: image

**Recommended Workflow**

- Start by selecting the process and GPU of interest using the global selectors at the top.
- Identify and select suspicious frames, such as frames with unusual memory usage or with a high volume of memory transition events.
- Use the Resident Resources table to learn more about allocated resources during the selected frames:
   - Identify resources with significant memory usage.
   - Identify resources that have changed between the two points in time (transitioned between VRAM and SYSMEM, or were allocated/deallocated).
   - View resources' allocation details, performance markers, and callstacks to help recognize the specific resources and possible problematic settings.
- Use the "All Allocations" table to find suspicious resources, such as resources with excessive residency changes or other unusual characteristics.
