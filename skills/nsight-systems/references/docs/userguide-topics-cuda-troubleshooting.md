---
source_path: UserGuide/topics/cuda-troubleshooting.rst
title: #### CUDA Troubleshooting
---
#### CUDA Troubleshooting

**Flush CUDA Profile Data**

To reduce profiling overhead, the profiling tools collect and record profile
information into internal buffers. These buffers are then flushed asynchronously
to disk with low priority to avoid perturbing application behavior. To avoid
losing profile information that has not yet been flushed, the application being
profiled should make sure, before exiting, that all GPU work is done (using
CUDA synchronization calls), and then call cudaProfilerStop() or
cuProfilerStop(). Doing so forces buffered profile information in corresponding
context(s) to be flushed.

If your CUDA application includes graphics that operate using a display or main
loop, care must be taken to call cudaProfilerStop() or cuProfilerStop() before
the thread executing that loop calls exit(). Failure to call one of these APIs
may result in the loss of some or all of the collected profile data.

For some graphics applications like the ones use OpenGL, the application exits
when the escape key is pressed. In those cases where calling the above functions
before exit is not feasible, explicitly end analysis using ``duration`` or
``nsys stop``. The profiler will force a data flush just before the timeout.
