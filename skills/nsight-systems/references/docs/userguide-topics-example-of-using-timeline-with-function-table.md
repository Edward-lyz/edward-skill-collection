---
source_path: UserGuide/topics/example-of-using-timeline-with-function-table.rst
title: #### Example of Using Timeline with Function Table
---
#### Example of Using Timeline with Function Table

Here is an example walkthrough of using the timeline and function table with Instruction Pointer (IP)/backtrace Sampling Data

**Timeline**

When a collection result is opened in the Nsight Systems GUI, there are multiple ways to view the CPU profiling data - especially the CPU IP / backtrace data.

   :alt: Timeline showing CPU IP/backtrace information
   :class: image

In the timeline, yellow-orange marks can be found under each thread's timeline that indicate the moment an IP / backtrace sample was collected on that thread (e.g., see the yellow-orange marks in the Specific Samples box above). Hovering the cursor over a mark will cause a tooltip to display the backtrace for that sample.

Below the Timeline is a drop-down list with multiple options including Events View, Top-Down View, Bottom-Up View, and Flat View. All four of these views can be used to view CPU IP / backtrace sampling data.

If the Bottom-Up View is selected, here is the sampling summary shown in the bottom half of the Timeline View screen. Notice that the summary includes the phrase “65,022 samples are used,” indicating how many samples are summarized. By default, functions that were found in less less than 0.5% of the samples are not show. Use the ``filter`` button to modify that setting.

   :alt: Timeline showing CPU IP/backtrace information
   :class: image

When sampling data is filtered, the Sampling Summary will summarize the selected samples. Samples can be filtered on an OS thread basis, on a time basis, or both. Above, deselecting a checkbox next to a thread removes its samples from the sampling summary. Dragging the cursor over the timeline and selecting “Filter and Zoom In” chooses the samples during the time selected, as seen below. The sample summary includes the phrase “0.35% (225 samples) of data is shown due to applied filters” indicating that only 225 samples are included in the summary results.

   :alt: Timeline showing CPU IP/backtrace information, filtered
   :class: image

Deselecting threads one at a time by deselecting their checkbox can be tedious. Click on the down arrow next to a thread and choose Show Only This Thread to deselect all threads except that thread.

   :alt: How to deselect all threads except one
   :class: image

If the Events View is selected in the Timeline View's drop-down list, right click on a specific thread and choose Show in Events View. The samples collected while that thread executed will be shown in the Events View. Double-clicking on a specific sample in the Events view causes the timeline to show when that sample was collected; see the green boxes below. The backtrace for that sample is also shown in the Events View.

   :alt: events view
   :class: image

**Backtraces**

To understand the code path used to get to a specific function shown in the sampling summary, right-click on a function and select Expand.

   :alt: expand backtrace
   :class: image

The above shows what happens when a function’s backtraces are expanded. In this case, the PCQueuePop function was called from the CmiGetNonLocal function which was called by the CsdNextMessage function which was called by the CsdScheduleForever function. The [Max depth] string marks the end of the collected backtrace.

   :alt: zoom in expand backtrace
   :class: image

Note that, by default, backtraces with less than 0.5% of the total backtraces are hidden. This behavior can make the percentage results hard to understand. If all backtraces are shown (i.e., the filter is disabled), the results look very different and the numbers add up as expected. To disable the filter, click on the Filter… button and uncheck the **Hide functions with CPU usage below X%** checkbox.

   :alt: no function filter backtraces
   :class: image

When the filter is disabled, the backtraces are recalculated. Note that you may need to right-click on the function and select **Expand** again to get all of the backtraces to be shown.

   :alt: reset backtraces
   :class: image

When backtraces are collected, the whole sample (IP and backtrace) is handled as a single sample. If two samples have the exact same IP and backtrace, they are summed in the final results. If two samples have the same IP but a different backtrace, they will be shown as having the same leaf (i.e., IP) but a different backtrace. As mentioned earlier, when backtraces end, they are marked with the [Max depth] string (unless the backtrace can be traced back to its origin; e.g., \__libc_start_main) or the backtrace breaks because an IP cannot be resolved.

Above, the leaf function is PCQueuePop. In this case, there are 11 different backtraces that lead to PCQueuPop — all of them end with [Max depth]. For example, the dominant path is ``PCQueuPop<-CmiGetNonLocal<-CsdNextmessage<-CsdScheduleForever<-[Max depth]``. This path accounts for 5.67% of all samples as shown in line 5 (red numbers). The second most dominant path is ``PCQueuPop<-CmiGetNonLocal<-[Max depth]`` which accounts for 0.44% of all samples as shown in line 24 (red numbers). The path ``PCQueuPop<-CmiGetNonLocal<-CsdNextmessage<-CsdScheduleForever<-Sequencer::integrate(int)<-[Max depth]`` accounts for 0.03% of the samples as shown in line 7 (red numbers). Adding up percentages shown in the [Max depth] lines (lines 5, 7, 9, 13, 15, 16, 17, 19, 21, 23, and 24) generates 7.04% which equals the percentage of samples associated with the PCQueuePop function shown in line 0 (red numbers).
