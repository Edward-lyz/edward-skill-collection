---
source_path: UserGuide/topics/cuda-event-trace.rst
title: ## CUDA Event Trace
---
## CUDA Event Trace

Nsight Systems is capable of capturing information about CUDA Events
(the synchronization mechanism, e.g. cudaEventRecord(), cudaStreamWaitEvent()
etc.) in your application. This can be set in the CLI using the
``--cuda-event-trace`` option, or in the GUI by setting the appropriate drop
down.

      :alt: Configure CUDA event trace
      :class: image

When CUDA event trace is set to ``true``, users can see device-side CUDA event
completion markers in CUDA HW timelines:

      :alt: CUDA event trace screenshot
      :class: image

Additionally, there will be better correlation support among CUDA Event APIs,
for example when clicking a cudaEventRecord(), the related calls such
cudaEventSynchronize(), cudaStreamWaitEvent() that operate on the same CUDA
event object will be highlighted:

      :alt: CUDA event trace correlation
      :class: image

However, there are also some limitations with this feature:

*  Currently, CUDA Event object created with cudaEventInterprocess flag and/or
   used in CUDA Graphs are not supported. The support only works under non-IPC
   and non-CUDA-Graph scenarios.
*  Currently, the underlying mechanism for tracing device-side CUDA Event
   completion is same as CUDA Event's own timing functionality (i.e. with a
   CUDA Event object is created without cudaEventDisableTiming flag). The
   mechanism is known to increase the possibility of false dependencies among
   seemingly unrelated CUDA Streams. Therefore, if the app's behavior changes
   with this feature, consider disabling it.
*  This option is only available with CUDA user-mode driver 12.8 or higher.
