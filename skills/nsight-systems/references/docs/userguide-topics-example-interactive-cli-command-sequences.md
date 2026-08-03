---
source_path: UserGuide/topics/example-interactive-cli-command-sequences.rst
title: ## Example Interactive CLI Command Sequences
---
## Example Interactive CLI Command Sequences

**Collect from beginning of application, end manually**


   nsys start --stop-on-exit=false
   nsys launch --trace=cuda,nvtx --sample=none <application> [application-arguments]
   nsys stop

Effect: Create interactive CLI process and set it up to begin collecting as soon
as an application is launched. Launch the application, set up to allow tracing
of CUDA and NVTX as well as collection of thread schedule information. Stop only
when explicitly requested. Generate the report#.nsys-rep in the default location.

Note:

   If you start a collection and fail to stop the collection (or if you are
   allowing it to stop on exit, and the application runs for too long), your
   system’s storage space may be filled with collected data causing significant
   issues for the system. Nsight Systems will collect a different amount of
   data/sec depending on options, but in general Nsight Systems does not support
   runs of more than 5 minutes duration.

**Run application, begin collection manually, run until process ends**


   nsys launch -w true <application> [application-arguments]
   nsys start

Effect: Create interactive CLI and launch an application set up for default
analysis. Send application output to the terminal. No data is collected until
you manually start collection at area of interest. Profile until the application
ends. Generate the report#.nsys-rep in the default location.

Note:

   If you launch an application and that application and any descendants exit
   before start is called, Nsight Systems will create a fully formed .nsys-rep
   file containing no data.
   
   
**Run application, name the session, keep only the last seconds**


   nsys start --session-new=mysession
   nsys launch --session=mysession myapp [application-arguments]
   nsys stop --session=mysession --keep=3
   
Effect: Create named interactive CLI process and launch your app with
default collection options. Manually stop that session and keep only the last
three seconds of data.

Note:

   Currently Nsight Systems will collect all the data and then trim the data at
   stop time. In the future we will add an option that does the collection in a
   ring buffer, so that if the user knows ahead of time how many seconds of data
   they wish to save we can avoid using unneeded memory.


**Run application, start/stop collection using cudaProfilerStart/Stop**


   nsys start -c cudaProfilerApi
   nsys launch -w true <application> [application-arguments]

Effect: Create interactive CLI process and set it up to begin collecting as soon
as a ``cudaProfileStart()`` is detected. Launch application for default analysis,
sending application output to the terminal. Stop collection at next call to
``cudaProfilerStop``, when the user calls ``nsys stop``, or when the root process
terminates. Generate the ``report#.nsys-rep`` in the default location.

Note:

   If you call ``nsys launch`` before ``nsys start -c cudaProfilerApi`` and the
   code contains a large number of short duration cudaProfilerStart/Stop pairs,
   Nsight Systems may be unable to process them correctly, causing a fault. This
   will be corrected in a future version.

Note:

   Use the Nsight Systems CLI option ``--capture-range-end-repeat`` to capture
   a separate report file for each capture range defined by calls to
   cudaProfilerStart/Stop. To avoid overwriting report files unexpectedly,
   Nsight Systems will ignore the ``--force-overwrite`` option in this case.

**Run application, start/stop collection using NVTX**


   nsys start -c nvtx
   nsys launch -w true -p MESSAGE@DOMAIN <application> [application-arguments]

Effect: Create interactive CLI process and set it up to begin collecting as soon
as an NVTX range with a given message in a given domain (capture range) is opened.
Launch application for default analysis, sending application output to the
terminal. Stop collection when all capture ranges are closed, when the user
calls ``nsys stop``, or when the root process terminates. Generate the
``report#.nsys-rep`` in the default location.
   
Note:

   The Nsight Systems CLI only triggers the profiling session for the first
   capture range.

NVTX capture range can be specified:

-  Message\@Domain: All ranges with given message in given domain are capture
   ranges. For example:


      nsys launch -w true -p profiler@service ./app

   This would make the profiling start when the first range with message
   "profiler" is opened in domain "service."

-  Message\@\*: All ranges with given message in all domains are capture ranges.
   For example:


      nsys launch -w true -p 'profiler@*' ./app

   This would make the profiling start when the first range with message
   "profiler" is opened in any domain.

-  Message: All ranges with given message in default domain are capture ranges.
   For example:


      nsys launch -w true -p profiler ./app

   This would make the profiling start when the first range with message
   "profiler" is opened in the default domain.

-  By default, only messages provided by NVTX registered strings are considered.
   This avoids the need to perform a string match on every NVTX string encountered
   in the application, which creates significant additional overhead. It is
   strongly recommended to always use NVTX registered strings. If you do not use
   registered strings you will have to enable the full match by launching
   your application with ``NSYS_NVTX_PROFILER_REGISTER_ONLY=0`` environment:


      nsys launch -w true -p profiler@service -e NSYS_NVTX_PROFILER_REGISTER_ONLY=0 ./app


Note:

   The separator '@' can be escaped with backslash '\\'. If multiple separators
   without escape character are specified, only the last one is applied, all others are discarded.

**Run application, start/stop collection multiple times**

The interactive CLI supports multiple sequential collections per launch.


   nsys launch <application> [application-arguments]
   nsys start
   nsys stop
   nsys start
   nsys stop
   nsys shutdown --kill sigkill

Effect: Create interactive CLI and launch an application set up for default
analysis. Send application output to the terminal. No data is collected until
the start command is executed. Collect data from start until stop requested,
generate ``report#.qstrm`` in the current working directory. Collect data from
second start until the second stop request, generate ``report#.nsys-rep``
(incremented by one) in the current working directory. Shutdown the interactive
CLI and send sigkill to the target application's process group.

**Collect multiple regions of interest, defer report generation**


   nsys launch --trace=cuda,nvtx <application> [application-arguments]
   nsys start -o region_1
   nsys stop --defer-report
   nsys start -o region_2
   nsys stop --defer-report
   nsys start -o region_3
   nsys stop --defer-report
   nsys shutdown
   nsys finalize list
   nsys finalize

Effect: Launch a long-running application and collect multiple regions of
interest. Each ``stop --defer-report`` returns quickly because report
generation is deferred, allowing the next ``start`` to begin without delay.
After all collections are complete, use ``nsys finalize list`` to see the
pending deferred collections and ``nsys finalize`` to generate the
``.nsys-rep`` report files. Output name substitution patterns (``%h``,
``%q{}``, ``%p``, ``%n``, ``%%``) are supported.

To finalize a specific collection, pass its UUID from the list output:


   nsys finalize --id <uuid-from-list>

To discard deferred collections without generating reports:


   nsys finalize --discard=all
   nsys finalize --discard=<uuid>
