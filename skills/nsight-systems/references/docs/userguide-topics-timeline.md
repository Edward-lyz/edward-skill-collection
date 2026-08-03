---
source_path: UserGuide/topics/timeline.rst
title: #### Timeline
---
#### Timeline

Timeline is a versatile control that contains a tree-like **hierarchy** on the
left, a *line labels* column in the center, and the corresponding *charts* on
the right. The line labels column can be hidden by using the timeline options.

   :alt: Timeline Options button
   :class: image

Contents of the hierarchy depend on the project settings used to collect the
report. For example, if a certain feature has not been enabled, corresponding
rows will not be shown on the timeline.


**Process Coloring**

The CPU utilization timelines are colored based on the CPU operating mode:

*  User mode - Green
*  Kernel mode - Red
*  Other (for example system-wide processes) - Black

**CPU Activity Computation Notes**

CPU usage and thread-state ranges in Timeline are computed from the best available source:

*  If CPU scheduling events are available, they are used as the primary source.
*  If scheduling events are not available (for example, ``--cpuctxsw=none``), and OS Runtime
   trace data is present, thread states are estimated from OSRT events.

**Exporting from Timeline**

To generate a timeline screenshot without opening the full GUI, use the command:
::

   nsys-ui.exe --screenshot filename.nsys-rep

Hovering over elements in the GUI will cause a tooltip to pop open as appropriate
to give additional information, such as the parameters of that function call or
or the call stack. Tooltips can be copied by hovering and right clicking to bring
up the ``Copy Tooltip`` option in the context menu:

   :alt: context menu to copy the tool tip
   :class: image
