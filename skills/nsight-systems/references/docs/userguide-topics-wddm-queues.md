---
source_path: UserGuide/topics/wddm-queues.rst
title: WDDM Queues
---
# WDDM Queues

The Windows Display Driver Model (WDDM) architecture uses queues to send work packets from the CPU to the GPU. Each D3D device in each process is associated with one or more contexts. Graphics, compute, and copy commands that the profiled application uses are associated with a context, batched in a command buffer, and pushed into the relevant queue associated with that context.

Nsight Systems can capture the state of these queues during the trace session.

Enabling the "Extensive trace" option will also capture extended DxgKrnl events from the ``Microsoft-Windows-DxgKrnl`` provider, such as Hardware Scheduling queues, context status, allocations, sync wait, signal events, etc.

      :alt: WDDM Queues
      :class: image

A command buffer in a WDDM queues may have one the following types:

-  Render

-  Deferred

-  System

-  MMIOFlip

-  Wait

-  Signal

-  Device

-  Software

It may also be marked as a Present buffer, indicating that the application has finished rendering and requests to display the source surface.

See the Microsoft documentation for the WDDM architecture and the ``DXGKETW_QUEUE_PACKET_TYPE`` enumeration.

To retain the .etl trace files captured, so that they can be viewed in other tools (e.g. GPUView), change the "Save ETW log files in project folder" option under "Profile Behavior" in Nsight Systems's global Options dialog. The .etl files will appear in the same folder as the .nsys-rep file, accessible by right-clicking the report in the Project Explorer and choosing "Show in Folder...". Data collected from each ETW provider will appear in its own .etl file, and an additional .etl file named "Report XX-Merged-\*.etl", containing the events from all captured sources, will be created as well.
