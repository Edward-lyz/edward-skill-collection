---
source_path: UserGuide/topics/cli-command-switches.rst
title: ## CLI Command Switches
---
## CLI Command Switches

The Nsight Systems command line interface can be used in two modes. You may
launch your application and begin analysis with options specified to the
``nsys profile`` command. Alternatively, you can control the launch of an
application and data collection using interactive CLI commands.

   :name: table_command_table
   :class: table-compact table-expandable     

   +----------+---------------------------------------------------------------------------------------------------------------------------------+
   | Command  | Description                                                                                                                     |
   +==========+=================================================================================================================================+
   | analyze  | Post process existing Nsight Systems result, either in .nsys-rep or SQLite format, to generate expert systems report.           |
   +----------+---------------------------------------------------------------------------------------------------------------------------------+
   | export   | Generates an export file from an existing ``.nsys-rep`` file. For more information about the exported formats see the           |
   |          | ``/documentation/nsys-exporter`` directory in your Nsight Systems installation directory.                                       |
   +----------+---------------------------------------------------------------------------------------------------------------------------------+
   | finalize | Generate report files from deferred collections. When ``nsys stop --defer-report`` is used, the stop command returns            |
   |          | quickly and raw data is retained without generating a report. The ``finalize`` command processes these deferred                 |
   |          | collections and produces ``.nsys-rep`` files.                                                                                   |
   +----------+---------------------------------------------------------------------------------------------------------------------------------+
   | import   | Converts a ``.qdstrm`` intermediate result file into a ``.nsys-rep`` report file. Use this command when automatic report        |
   |          | generation did not run or did not complete.                                                                                     |
   +----------+---------------------------------------------------------------------------------------------------------------------------------+
   | launch   | In interactive mode, launches an application in an environment that supports the requested options. The launch command can be   |
   |          | executed before or after a start command.                                                                                       |
   +----------+---------------------------------------------------------------------------------------------------------------------------------+
   | profile  | A fully formed profiling description requiring and accepting no further input. The command switch options used (see below       |
   |          | table) determine when the collection starts, stops, what collectors are used (e.g., API trace, IP sampling, etc.), what         | 
   |          | processes are monitored, etc.                                                                                                   |
   +----------+---------------------------------------------------------------------------------------------------------------------------------+
   | recipe   | Post process one or more existing Nsight Systems results to generate statistical                                                |
   |          | information and create various plots. See the **Post-Collection Analysis Guide** for details.                                   |
   +----------+---------------------------------------------------------------------------------------------------------------------------------+
   | sessions | Gives information about all sessions running on the system.                                                                     |
   +----------+---------------------------------------------------------------------------------------------------------------------------------+
   | shutdown | Disconnects the CLI process from the launched application and forces the CLI process to exit. If a collection is pending or     |
   |          | active, it is canceled.                                                                                                         |
   +----------+---------------------------------------------------------------------------------------------------------------------------------+
   | start    | Starts a collection in interactive mode. The start command can be executed before or after a launch command.                    |
   +----------+---------------------------------------------------------------------------------------------------------------------------------+
   | stats    | Post process existing Nsight Systems result, either in ``.nsys-rep`` or SQLite format, to generate statistical information.     |
   +----------+---------------------------------------------------------------------------------------------------------------------------------+
   | status   | Reports on the status of a CLI-based collection or the suitability of the profiling environment.                                |
   +----------+---------------------------------------------------------------------------------------------------------------------------------+
   | stop     | Stops a collection that was started in interactive mode. When executed, all active collections stop, the CLI process            |
   |          | terminates but the application continues running.                                                                               |
   +----------+---------------------------------------------------------------------------------------------------------------------------------+
