---
source_path: UserGuide/topics/cli-status-command-switch-options.rst
title: #### CLI Status Command Switch Options
---
#### CLI Status Command Switch Options

The ``nsys status`` command returns the current state of the CLI. After choosing the ``status`` command switch, the following options are available. Usage:

::

   nsys [global-options] status [options]

   :name: table_status_table
   :class: table-compact table-expandable


   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | Option                        | Available Parameters  | Switch Description                                                                                      |
   |                               | (default in bold)     |                                                                                                         |
   +===============================+=======================+=========================================================================================================+
   | ``--all``                     |                       | Prints information for all the available profiling environments.                                        |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--environment`` or ``-e``   |                       | Returns information about the system regarding suitability of the profiling environment.                |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--help``                    | <tag>                 | Print the help message. The option can take one optional argument that will be used as a tag. If a tag  |
   |                               |                       | is provided, only options relevant to the tag will be printed.                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--network`` or ``-n``       |                       | Returns information about the system regarding suitability of the network profiling environment.        |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--session``                 | session identifier    | Print the status of the indicated session. The option argument must represent a valid session name or   |
   |                               |                       | ID as reported by ``nsys sessions list``. Any ``%q{ENV_VAR}`` pattern will be substituted with the      |
   |                               |                       | value of the environment variable. Any ``%h`` pattern will be substituted with the hostname of the      |
   |                               |                       | system. Any ``%%`` pattern will be substituted with ``%``.                                              |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
