---
source_path: UserGuide/topics/command-line-options.rst
title: ## Command Line Options
---
## Command Line Options

The Nsight Systems command lines can have one of two forms:

::

   nsys [global_option]

or

::

   nsys [command_switch][optional command_switch_options][application] [optional application_options]

All command line options are case-sensitive. For command switch options, when short options are used, the parameters should follow the switch after a space; e.g., ``-s process-tree``. When long options are used, the switch should be followed by an equal sign and then the parameter(s); e.g., ``--sample=process-tree``.

For this version of Nsight Systems, if you launch a process from the command line to begin analysis, the launched process will be terminated when collection is complete, including runs with ``--duration`` set, unless the user specifies the ``--kill none`` option (details below). The exception is that if the user uses NVTX, cudaProfilerStart/Stop, or hotkeys to control the duration, the application will continue unless ``--kill`` is set.

The Nsight Systems CLI supports concurrent analysis by using sessions. Each Nsight Systems session is defined by a sequence of CLI commands that define one or more collections (e.g., when and what data is collected). A session begins with either a start, launch, or profile command. A session ends with a shutdown command, when a profile command terminates, or, if requested, when all the process tree(s) launched in the session exit. Multiple sessions can run concurrently on the same system.
