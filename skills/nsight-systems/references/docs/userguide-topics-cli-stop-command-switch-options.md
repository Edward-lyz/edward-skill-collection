---
source_path: UserGuide/topics/cli-stop-command-switch-options.rst
title: #### CLI Stop Command Switch Options
---
#### CLI Stop Command Switch Options

After choosing the ``stop`` command switch, the following options are available. Usage:

::

   nsys [global-options] stop [options]

   :name: table_stop_table
   :class: table-compact table-expandable


   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | Option                        | Available Parameters  | Switch Description                                                                                      |
   |                               | (default in bold)     |                                                                                                         |
   +===============================+=======================+=========================================================================================================+
   | ``--defer-report``            |                       | Defer the generation of the report file so that the stop command returns quickly. The raw data will     |
   |                               |                       | be retained in a temporary location. Use ``nsys finalize`` to generate the report file later. This      |
   |                               |                       | is useful when performing multiple start/stop cycles on a long-running application.                     |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--help``                    | <tag>                 | Print the help message. The option can take one optional argument that will be used as a tag. If a tag  |
   |                               |                       | is provided, only options relevant to the tag will be printed.                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--keep``                    | time in seconds       | Indicate how many seconds of collected data previous to the stop command should be retained in the      |
   |                               |                       | result file. Zero is treated as a special setting that retains all of the data.                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--session``                 | session identifier    | Stop the indicated session. The option argument must represent a valid session name or ID as reported   |
   |                               |                       | by ``nsys sessions list``. Any ``%q{ENV_VAR}`` pattern will be substituted with the value of the        |
   |                               |                       | environment variable. Any ``%h`` pattern will be substituted with the hostname of the system.  Any      |
   |                               |                       | ``%%`` pattern will be substituted with ``%``.                                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
