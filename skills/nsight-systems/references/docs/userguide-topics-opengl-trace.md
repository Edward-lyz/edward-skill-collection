---
source_path: UserGuide/topics/opengl-trace.rst
title: OpenGL Trace
---
# OpenGL Trace

OpenGL and OpenGL ES APIs can be traced to assist in the analysis of CPU and GPU interactions.

A few usage examples are:

#. Visualize how long ``eglSwapBuffers`` (or similar) is taking.

#. API trace can easily show correlations between thread state and graphics driver's behavior, uncovering where the CPU may be waiting on the GPU.

#. Spot bubbles of opportunity on the GPU, where more GPU workload could be created.

#. Use ``KHR_debug`` extension to trace GL events on both the CPU and GPU.

OpenGL trace feature in Nsight Systems consists of two different activities which will be shown in the CPU rows for those threads

-  **CPU trace**: interception of API calls that an application does to APIs (such as OpenGL, OpenGL ES, EGL, GLX, WGL, etc.).

-  **GPU trace** (or **workload trace**): trace of GPU workload (activity) triggered by use of OpenGL or OpenGL ES. Since draw calls are executed back-to-back, the GPU workload trace ranges include many OpenGL draw calls and operations in order to optimize performance overhead, rather than tracing each individual operation.

To collect GPU trace, the ``glQueryCounter()`` function is used to measure how much time batches of GPU workload take to complete.

      :alt: Configure OpenGL trace
      :class: image

..

      :alt: Configure OpenGL functions
      :class: image

Ranges defined by the ``KHR_debug`` calls are represented similarly to OpenGL API and OpenGL GPU workload trace. GPU ranges in this case represent *incremental draw cost*. They cannot fully account for GPUs that can execute multiple draw calls in parallel. In this case, Nsight Systems will not show overlapping GPU ranges.
