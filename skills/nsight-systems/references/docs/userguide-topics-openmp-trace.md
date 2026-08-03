---
source_path: UserGuide/topics/openmp-trace.rst
title: OpenMP Trace
---
# OpenMP Trace

Nsight Systems for Linux is capable of capturing information about OpenMP events. This functionality is built on the OpenMP Tools Interface (OMPT), full support is available only for runtime libraries supporting tools interface defined in OpenMP 5.0 or greater.

As an example, LLVM OpenMP runtime library partially implements tools interface. If you use PGI compiler <= 20.4 to build your OpenMP applications, add the ``-mp=libomp`` switch to use LLVM OpenMP runtime and enable OMPT based tracing. If you use Clang, make sure the LLVM OpenMP runtime library you link to was compiled with tools interface enabled.

   :alt: OpenMP trace selection
   :class: image

Only a subset of the OMPT callbacks are processed:

::

   ompt_callback_parallel_begin
   ompt_callback_parallel_end
   ompt_callback_sync_region
   ompt_callback_task_create
   ompt_callback_task_schedule
   ompt_callback_implicit_task
   ompt_callback_master
   ompt_callback_reduction
   ompt_callback_task_create
   ompt_callback_cancel
   ompt_callback_mutex_acquire, ompt_callback_mutex_acquired
   ompt_callback_mutex_acquired, ompt_callback_mutex_released
   ompt_callback_mutex_released
   ompt_callback_work
   ompt_callback_dispatch
   ompt_callback_flush

Note:

   The raw OMPT events are used to generate ranges indicating the runtime of OpenMP operations and constructs.

Example screenshot:

   :alt: OpenMP API trace
   :class: image
