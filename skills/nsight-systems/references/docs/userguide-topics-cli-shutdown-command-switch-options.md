---
source_path: UserGuide/topics/cli-shutdown-command-switch-options.rst
title: #### CLI Shutdown Command Switch Options
---
#### CLI Shutdown Command Switch Options

After choosing the ``shutdown`` command switch, the following options are available. Usage:

::

   nsys [global-options] shutdown [options]

   :name: table_shutdown_table
   :class: table-compact table-expandable


   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | Option                        | Available Parameters  | Switch Description                                                                                      |
   |                               | (default in bold)     |                                                                                                         |
   +===============================+=======================+=========================================================================================================+
   | ``--help``                    | <tag>                 | Print the help message. The option can take one optional argument that will be used as a tag. If a tag  |
   |                               |                       | is provided, only options relevant to the tag will be printed.                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--kill``                    | On Linux: none,       | Send signal to the target application's process group when shutting down session.                       |
   |                               | sigkill, **sigterm**, |                                                                                                         |
   |                               | signal number         |                                                                                                         |
   |                               |                       |                                                                                                         |
   |                               | On Windows: **true**, |                                                                                                         |
   |                               | false                 |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--session``                 | session identifier    | Shutdown the indicated session. The option argument must represent a valid session name or ID as        |
   |                               |                       | reported by ``nsys sessions list``. Any ``%q{ENV_VAR}`` pattern will be substituted with the value of   |  
   |                               |                       | the environment variable. Any ``%h`` pattern will be substituted with the hostname of the system. Any   |
   |                               |                       | ``%%`` pattern will be substituted with ``%``.                                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
