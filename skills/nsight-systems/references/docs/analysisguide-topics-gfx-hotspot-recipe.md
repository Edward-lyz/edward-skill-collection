---
source_path: AnalysisGuide/topics/gfx_hotspot-recipe.rst
title: ## gfx_hotspot Recipe
---
## gfx_hotspot Recipe

This recipe's output is different from other recipes and is presented as a web
application.

The output can be viewed by passing the ``--run-viewer`` argument to the recipe -
along with the further ``--show-viewer`` which will automatically open a web
browser to the report view.

Alternatively, a previously-executed ``gfx_hotspot`` recipe's output can be
viewed by executing the ``run_viewer.py`` script from the recipe output folder.

For the best results, run the recipe on a report with resolved symbols.

**Threading Analysis**

In this tab, an overview of the multi-threading behavior of the target (most active)
process is presented.

-   Application Statistics:
        This table shows the CPU and thread statistics for the target process.

-   CPU Info:
        This table shows information about the CPU hardware.

-   Top 5 Processes CPU Utilisation:
        This table shows the most active processes during the sample, to help detect
        situations where another process is interfering with the target process's
        execution.

-   Threading Health Check:
        This table contains a list of very common CPU-bound application performance
        indicators. If the target application is GPU bound, the entire table will
        be shown in green. If it is CPU bound, then each row will be highlighted in
        green if the value is healthy, in yellow if it requires attention, and in
        red if it potentially indicates of a threading issue. For unhealthy metrics,
        the "warning" column will also show steps or investigation angles that may
        be considered in order to improve the result.

-   Thread Utilisation:
        This graph shows the process threads, ordered from most busy to least.

-   Thread Concurrency:
        This graph shows the percentage and amount of time an average graphic frame
        is running each number of threads concurrently. High percentage of low thread
        counts could indicate excessive serialization in the algorithm, where CPU
        work could be better parallelized by improving the use of multi-threading.

**Hotspot Analysis**

In this tab, frames are selected in one of four methods:
 * Longest Frame time (Slow Frames)
 * Periodic time-based selection (Periodic Frames)
 * Frames with highest transfer activity (Bar1 Reads)
 * Frames with least GPU activity (GR Idle)

The report view then allows comparing the selected frames to each other and to
the median frame in the same metric, helping identify the main differences and
possible problem areas in each one.

-   Overview:
        These tables show the report overview as well as the frame selection method
        and other capture-wide statistics and general information. A shorthand list
        of the "Performance Issues" table for each frame is also shown.

-   Frame Times:
        This graph shows a sequence of the graphical frames (CPU time and GPU time
        derived from GPU Utilisation percentage per CPU frame time) ordered by
        their index. The selected frames are indicated and labelled. Clicking any
        of the indicated frames will set it as the left frame for comparison.

-   Region / Compare to:
        These controls allow selecting the two frames to be shown for comparison.
        "Periodic Frames" shows 10 sampled frames (with equally distributed indices),
        while the other three modes show the 5 frames with the highest value in
        the chosen metric and the median frame in the same metric. All information
        from this point onwards is shown per selected frame in each of the two columns,
        allowing for 1-to-1 comparison. Selecting the same frame for both controls
        will show just the single frame as the entire width of the view.

-   Frame Info:
        This table shows the frame duration and start time, the number of threads
        that were active during the frame, and the thread IDs of key threads in
        the frame processing operation which are important for determining likely
        performance issues.

-   Performance Issues:
        This table shows the key performance limiters and hotspots for the selected
        frame. Each indicator will have a breakdown of what indicators were present
        to call out the performance issue during this frame. These indicators are
        not necessarily the root cause of the problems in the region, but have been
        flagged for consideration.

-   GPU Metrics:
        This table shows the average or total (respectively) values of the GPU
        metrics collected during the frame time. If GPU Metrics were not collected,
        this table will not appear.

-   System ETW Events (Windows only):
        This chart shows a breakdown of the system process-reported ETW events during
        the frame. If WDDM trace and Custom ETW trace were not collected, this chart
        will not appear.

-   DxgKrnl Events (Windows only):
        This chart shows a breakdown of the DxgKrnl ETW provider events during the
        frame. If WDDM trace was not collected, this chart will not appear.

-   CPU Thread Utilisation Time:
        This graph shows the time spent inside each thread during the frame. The
        bars match the two selected frames, and the matching-colored line shows
        the total frame time. Clicking any of the columns in the graph will select
        that thread for the following elements in the report.

-   Thread:
        This control allows selecting the thread to be shown in the following views.

-   Call stacks:
        This control shows the sampled call stacks during the frame. Clicking a
        call stack frame will filter the view to only show call stacks containing
        this call stack frame, allowing to drill down into potential problem areas.
        The title of the control indicates the two modes selected for display,
        which can be switched with the two toggles in the top right of the control:

-   Call stacks - Merged:
        Merges all similar call stacks logically, regardless of when in the frame
        time the functions appeared. This is useful to see where the cumulative time is spent.

-   Call stacks - Over Time:
        Keeps call stacks ordered chronologically, so that repeated calls to the
        same function appear separately.

-   Periodic Sampled Call stacks:
        Only shows call stacks acquired by periodic sampling (matching the orange
        marks in Nsight Systems's timeline view). This view provides a better
        statistical overview of where the frame time was spent.

-   All Call stacks:
        Shows periodic sampled call stacks as well as call stacks acquired from
        other sources such as call stacks from ETW events (Windows) and
        event-based sampling (Linux) (matching both the orange AND the grey marks
        in Nsight Systems's timeline view).

-   Modules in Sampled Call Stacks:
        This graph shows the number of call stacks in the frame that include at
        least one call stack frame in a function belonging to each module. This
        helps identify which modules were the most active during the frame.

-   ETW Events (Windows only):
        This chart shows a breakdown of the thread-reported ETW events during the
        frame. If WDDM trace and Custom ETW trace were not collected, this chart
        will not appear.

-   Context Switch Call Stacks:
        This table shows a breakdown of the call stacks that led to context switches
        for the thread during the frame, indicating where the thread may have stalled.
        Hovering the mouse cursor over the "Name" column will show the full call
        stack for each entry.

-   DX12 API / Vulkan API:
        These tables show a breakdown of the graphical API functions that appeared
        in sampled call stacks. If DX12 / Vulkan trace were not collected, these
        tables will not appear.

-   Known Symbols From Sampled Call Stacks:
        This table shows a breakdown of known symbols that often cause performance
        issues, such as DX12's CreateCommittedResource.  If symbols were not resolved
        for the nsys-rep file, this table will not appear.

-   PIX Markers (Windows only):
        This table shows a breakdown of PIX marker ranges that contained sampled
        call stacks. If WDDM trace and DX11 / DX12 trace were not collected or the
        target application does not use PIX markers, this table will not appear.
