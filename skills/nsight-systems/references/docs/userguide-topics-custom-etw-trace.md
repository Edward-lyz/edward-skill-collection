---
source_path: UserGuide/topics/custom-etw-trace.rst
title: Custom ETW Trace
---
# Custom ETW Trace

Use the custom ETW trace feature to enable and collect any manifest-based ETW log. The collected events are displayed on the timeline on dedicated rows for each event type.

Custom ETW is available on Windows target machines.

      :alt: Adding details of an ETW provider
      :class: image

..

      :alt: Adding an ETW provider to the trace settings
      :class: image

   :alt: Display of custom ETW trace events on the timeline
   :class: image

To retain the .etl trace files captured, so that they can be viewed in other tools (e.g., GPUView), change the **Save ETW log files in project folder** option under **Profile Behavior** in Nsight Systems's global Options dialog. The .etl files will appear in the same folder as the .nsys-rep file, accessible by right-clicking the report in the Project Explorer and choosing **Show in Folder...**. Data collected from each ETW provider will appear in its own .etl file, and an additional .etl file named ``Report XX-Merged-\*.etl``, containing the events from all captured sources, will be created as well.
