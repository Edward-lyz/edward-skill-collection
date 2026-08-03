---
source_path: UserGuide/topics/function-table-modes.rst
title: #### Function Table Modes
---
#### Function Table Modes

      :alt: Function table modes
      :class: image

The function table can work in three modes:

-  **Top-Down View** — In this mode, expanding top-level functions provides information about the *callee* functions. One of the top-level functions is typically the main function of your application, or another entry point defined by the runtime libraries.

-  **Bottom-Up View** — This is a reverse of the Top-Down view. On the top level, there are functions directly hit by the sampling profiler. To explore all possible call chains leading to these functions, you need to expand the subtrees of the top-level functions.

-  **Flat View** — This view enumerates all functions ever observed by the profiler, even if they have never been directly hit, but just appeared somewhere on the call stack. This view typically provides a high-level overview of which parts of the code are CPU-intensive.

Each of the views helps understand particular performance issues of the application being profiled. For example:

-  When trying to find specific bottleneck functions that can be optimized, the Bottom-Up view should be used. Typically, the top few functions should be examined. Expand them to understand in which contexts they are being used.

-  To navigate the call tree of the application and while generally searching for algorithms and parts of the code that consume unexpectedly large amount of CPU time, the Top-Down view should be used.

-  To quickly assess which parts of the application, or high level parts of an algorithm, consume significant amount of CPU time, use the Flat view.

The Top-Down and Bottom-Up views have *Self* and *Total* columns, while the Flat view has a *Flat* column. It is important to understand the meaning of each of the columns:

-  Top-Down view

   -  **Self** column denotes the relative amount of time spent executing instructions of this particular function.

   -  **Total** column shows how much time has been spent executing this function, including all other functions called from this one. Total values of sibling rows sum up to the Total value of the parent row, or 100% for the top-level rows.

-  Bottom-Up view

   -  **Self** column for *top-level rows*, as in the Top-Down view, shows how much time has been spent directly in this function. Self times of all top-level rows add up to 100%.

   -  **Self** column for *children rows* breaks down the value of the parent row based on the various call chains leading to that function. Self times of sibling rows add up to the value of the parent row.

-  Flat view

   -  **Flat** column shows how much time this function has been anywhere on the call stack. Values in this column do not add up or have other significant relationships.

When source file and line information is enabled during report collection, the
Top-Down and Bottom-Up views also include Source File and Source Line columns.
Flat View does not show Source File or Source Line columns and does not provide
line-level Self % data, even when source file and line collection is enabled;
use Top-Down View or Bottom-Up View for line-level source information.
This is controlled by the **Collect source file and line information** GUI
option or the ``--show-source-info`` CLI option. This information can help
identify where the program spends the most time at the line level. Instead of
only seeing that a large function is slow, you can locate the loop, conditional
statement, or call site responsible for the bottleneck. If a common utility
function is called from multiple places, the line-level data can show which call
site is responsible for the most CPU usage.

In Top-Down View, source information provides line-level Self % data, allowing
more precise bottleneck identification.

   :alt: Top-Down View with source file and line information
   :class: image

In Bottom-Up View, a function can appear multiple times based on its occurrences
in the samples. To prevent the Bottom-Up table from becoming unmanageable,
Nsight Systems groups identical functions at the same level and aggregates their
Self %. This allows you to analyze the performance of individual parts of a
function while still viewing the total aggregate performance of the function as a
whole. When rows for the same function and module are aggregated from different
source lines, the aggregate row may retain source file information but does not
show a single Source Line; expand the child rows to inspect each source line.
This grouping logic scales recursively throughout the call tree.

   :alt: Bottom-Up View with source file and line information
   :class: image

Note:
   
   If low-impact functions have been filtered out, values may not add up correctly to 100%, or to the value of the parent row. This filtering can be disabled.

Contents of the symbols table is tightly related to the timeline. Users can apply and modify filters on the timeline, and they will affect which information is displayed in the symbols table:

-  **Per-thread filtering** — Each thread that has sampling information associated with it has a checkbox next to it on the timeline. Only threads with selected checkboxes are represented in the symbols table.

-  **Time filtering** — A time filter can be setup on the timeline by pressing the left mouse button, dragging over a region of interest on the timeline, and then choosing **Filter by selection** in the dropdown menu. In this case, only sampling information collected during the selected time range will be used to build the symbols table.

Note:

   If too little sampling data is being used to build the symbols table (for example, when the sampling rate is configured to be low, and a short period of time is used for time-based filtering), the numbers in the symbols table might not be representative or accurate in some cases.
