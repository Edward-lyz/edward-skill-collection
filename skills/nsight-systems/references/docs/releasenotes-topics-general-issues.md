---
source_path: ReleaseNotes/topics/general-issues.rst
title: ## General Issues
---
## General Issues

-  If you see high branch mis-predicts and instruction TLB refills, we suggest
   you try `<https://github.com/NVIDIA/cpu-code-locality-tool>`__ to further
   optimize your code for NVIDIA Grace's code caches.

-  RoCE counters for ConnectX NICs are not available with version 2025.6.

-  Nsight Systems trace features that require process injection (e.g. OSRT, NVTX,
   CUDA trace) may fail to collect data and cause unstable behavior when
   profiling applications that use seccomp to restrict system calls, such as
   Linux's `file` utility. The injection library may violate the process's
   seccomp policy, causing thread/process termination and/or other unstable
   behaviors like leaving the application hanging in a zombie process state.
   Disable seccomp in the target application if possible or use only
   non-injection-based profiling features (e.g. CPU sampling, GPU metrics
   sampling) for those applications. 

-  The current release of Nsight Systems CLI doesn't support naming a session
   with a name longer than 127 characters. Profiling an executable with a name
   exceeding 111 characters is also unsupported by the ``nsys profile`` command.
   Those limitations will be removed in a future version of the CLI.

-  Nsight Systems 2020.4 introduces collection of thread scheduling information
   without full sampling. While this allows system information at a lower cost,
   it does add overhead. To turn off thread schedule information collection, add
   ``--cpuctxsw=none`` to your command line or turn off in the GUI.

-  Profiling greater than 5 minutes is not officially supported at this time.
   Profiling high activity applications, on high performance machines, over a
   long analysis time can create large result files that may take a very long
   time to load, run out of memory, or lock up the system. If you have a complex
   application, we recommend starting with a short profiling session duration of
   no more than 5 minutes for your initial profile. If your application has a
   natural repeating pattern, often referred to as a frame or an iteration, you
   will typically only need a few of these. This suggested limit will increase
   in future releases.

-  Attaching or re-attaching to a process from the GUI is not supported with the
   x86_64 Linux target. Equivalent results can be obtained by using
   the interactive CLI to launch the process and then starting and stopping
   analysis at multiple points.

-  To reduce overhead, Nsight Systems traces a subset of API calls likely to
   impact performance when tracing APIs rather than all possible calls. There
   is currently no way to change the subset being traced when using the CLI.
   See respective library portion of this documentation for a list of calls
   traced by default. The CLI limitation will be removed in a future version of
   the product.

-  There is an upper bound on the default size used by the tool to record trace
   events during the collection. If you see the following diagnostic error, then
   Nsight Systems hit the upper limit.

   ::

      Reached the size limit on recording trace events for this process.
             Try reducing the profiling duration or reduce the number of features
             traced.

-  When profiling a framework or application that uses CUPTI, like some versions
   of TensorFlow(tm), Nsight Systems will not be able to trace CUDA usage due to
   limitations in CUPTI. These limitations will be corrected in a future version
   of CUPTI. Consider turning off the application's use of CUPTI if CUDA tracing
   is required.

-  Tracing an application that uses a memory allocator that is not thread-safe
   is not supported.

-  Tracing OS Runtime libraries in an application that preloads glibc symbols is
   unsupported and can lead to undefined behavior.

-  Nsight Systems cannot profile applications launched through a virtual window
   manager like GNU Screen.

-  Using Nsight Systems MPI trace functionality with the Darshan runtime module
   can lead to segfaults. To resolve the issue, unload the module.
   
::

   module unload darshan-runtime

-  Profiling MPI Fortran APIs with MPI_Status as an argument, e.g. MPI_Recv,
   MPI_Test[all], MPI_Wait[all], can potentially cause memory corruption for
   MPICH versions 3.0.x. The reason is that the MPI_Status structure in MPICH
   3.0.x has a different memory layout than in other MPICH versions
   (2.1.x and >=3.1.x have been tested) and the version (3.3.2) we used to
   compile the Nsight Systems MPI interception library.

-  Using ``nsys export`` to export to an SQLite database will fail if the
   destination filesystem doesn't support file locking. The error message will
   mention:
   
::

   std::exception::what: database is locked

-  On some Linux systems when VNC is used, some widgets can be rendered
   incorrectly, or Nsight Systems can crash when opening Analysis Summary or
   Diagnostics Summary pages. In this case, try forcing a specific software
   renderer: ``GALLIUM_DRIVER=llvmpipe nsys-ui``

-  Due to `a known bug in Open MPI 4.0.1
   <https://github.com/open-mpi/ompi/issues/6648>`__, target application may
   crash at the end of execution when being profiled by Nsight Systems. To avoid
   the issue, use a different Open MPI version, or add ``--mca btl ^vader``
   option to ``mpirun`` command line.

-  The multiprocessing module in Python is commonly used by customers to create
   new processes. On Linux, the module defaults to using the "fork" mode where
   it forks new processes, but does not call exec. According to the POSIX
   standard, fork without exec leads to undefined behavior and tools like
   Nsight Systems that rely on injection are only allowed to make
   async-signal-safe calls in such a process. This makes it very hard for tools
   like Nsight Systems to collect profiling information. See
   https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods

   Use the set_start_method in the multiprocessing module to change the start
   method to "spawn" which is much safer and allows tools like Nsight Systems to
   collect data. See the code example given in the link above.

   The user needs to ensure that processes exit gracefully (by using close and
   join methods, for example, in the multiprocessing module's objects).
   Otherwise, Nsight Systems cannot flush buffers properly and you might end up
   with missing traces.
   
-  When the CLI sequence launch, start, stop is used to profile a process-tree,
   LinuxPerf does a depth first search (DFS) to find all of the threads launched
   by the process-tree before programming the OS to collect the data. If, during
   the DFS, one or more threads are created by the process tree, it is possible
   those threads won't be found and LinuxPerf would not collect data for them.

   Note that once a thread is programmed via perf_event_open, any subsequent
   children processes or threads generated by that thread will be tracked since
   the perf_event_open inherit bit is set.

   No other CLI command sequence suffers from this possible issue. Also, if a
   systemwide mode is used, the issue does not exist.
