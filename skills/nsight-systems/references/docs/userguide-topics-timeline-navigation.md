---
source_path: UserGuide/topics/timeline-navigation.rst
title: #### Timeline Navigation
---
#### Timeline Navigation


#### Zoom and Scroll

At the upper right portion of your Nsight Systems GUI, you will see this section:

      :alt: scroll bar to set vertical scaling
      :class: image

The slider sets the vertical size of screen rows, and the magnifying glass
resets it to the original settings.

There are many ways to zoom and scroll horizontally through the timeline.
Clicking on the keyboard icon seen above, opens the below dialog that explains
them.

      :alt: various options for zoom and scroll 
      :class: image


#### Pinning Rows

In order to better allow users to compare rows from different sections of the
timeline, Nsight Systems gives the user the ability to select rows and "pin" 
them in the visual range. To select a row to pin, use ``Ctrl+P`` or ``Pin row``
from the right click menu.

   :alt: context menu to copy the tool tip
   :class: image   

Once a row has been pinned, it remain at the top or bottow of the window, rather
than scrolling off.

   :alt: screenshot of timeline with pinned rows
   :class: image   


#### Timeline Correlation

The Nsight Systems GUI can correlate between calls on the CPU and GPU to help
you understand the workflow.

Selecting an item will highlight that item in teal as well as:

-  Any copy of that same item in other rows. This means that if there is a
   summary row that includes this item it will also have the appropriate section
   highlighted.
-  All correlated items. For example, if a CUDA kernel was launched by a CPU
   function both are highlighted.
-  All things in that thread or stream that falls into the time range since
   they are of part of that larger range. For example, if you clicked an NVTX
   range it would select all NVTX ranges and CUDA launches inside and then
   extend to its correlations.

The highlighting also includes lines to each event to better distinguish when
highlighted events or ranges are overlapping.


In addition, Nsight Systems also provides indicators to help you find correlated
items not currently on your screen, including:

-  Highlights in the row headers when there is something highlighted in that row.
-  Diagonal arrows in row headers if something is in a child row.
-  Highlights in the timeline rule.
-  Arrows in corners when something highlighted is off-screen.  You can click
   those and the timeline will pan or zoom to get them into view.

      :alt: graphic showing correlation navigation hints
      :class: image

Correlation exists bidirectionally for:

-  CUDA kernels, CUDA graphs, GPU memcopies, and OptiX.
-  GPU memsets.
-  Vulkan QueueSubmits API and CommandBuffers on GPU.
-  D3D and GL just like Vulkan.


#### Timeline/Events Correlation

To display trace events in the Events View right-click a timeline row and select
the ``Show in Events View`` command. The events of the selected row and all of
its sub-rows will be displayed in the Events View. Note that the events
displayed will correspond to the current zoom in the timeline, zooming in or out
will reset the event pane filter.

If a timeline row has been selected for display in the Events View, then
double-clicking a timeline item on that row will automatically scroll the
content of the Events View to make the corresponding events view item visible
and select it. If that event has tool tip information, it will be displayed in
the right hand pane.

Likewise, double-clicking on a particular instance in the Events View will
highlight the corresponding event in the timeline.

      :alt: various options for zoom and scroll 
      :class: image


#### Row Height

Several of the rows in the timeline use height as a way to model the percent
utilization of resources. This gives the user insight into what is going on even
when the timeline is zoomed all the way out.

      :alt: various options for zoom and scroll 
      :class: image

In this picture, you see that for kernel occupation there is a colored bar of
variable height.

Nsight Systems calculates the average occupancy for the period of time represented
by particular pixel width of screen. It then uses that average to set the top of
the colored section. So, for instance, if 25% of that timeslice the kernel is
active, the bar goes 25% of the distance to the top of the row.

In order to make the difference clear, if the percentage of the row height is
non-zero, but would be represented by less than one vertical pixel,
Nsight Systems displays it as one pixel high. The gray height represents the
maximum usage in that time range.

This row height coding is used in the CPU utilization, thread and process
occupancy, kernel occupancy, and memory transfer activity rows.


#### Row Percentage

In the previous image, you also see that there are percentages prefixing the
stream rows in the GPU.

The percentage shown in front of the stream indicates the proportion of context
running time this particular stream takes.

   
          % stream = 100.0 X streamUsage / contextUsage
          streamUsage = total amount of time this stream is active on GPU
          contextUsage = total amount of time all streams for this context are active on GPU
          
          
So "26% Stream 1" means that Stream 1 takes 26% of its context's total running
time.

   
          Total running time = sum of durations of all kernels and memory ops that
          run in this context
