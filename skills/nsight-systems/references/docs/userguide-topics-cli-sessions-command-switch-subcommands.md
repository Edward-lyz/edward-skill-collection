---
source_path: UserGuide/topics/cli-sessions-command-switch-subcommands.rst
title: #### CLI Sessions Command Switch Subcommands
---
#### CLI Sessions Command Switch Subcommands

After choosing the ``sessions`` command switch, the following subcommands are available. Usage:

::

   nsys [global-options] sessions [subcommand]

   :name: table_sessions_table
   :class: table-compact

   +------------+--------------------------------------------------------------------+
   | Subcommand | Description                                                        |
   +============+====================================================================+
   | list       | List all active sessions including ID, name, and state information |
   +------------+--------------------------------------------------------------------+


### CLI Sessions List Command Switch Options

After choosing the ``sessions list`` command switch, the following options are available. Usage:


   nsys [global-options] sessions list [options]

   :name: table_grid_table
   :class: table-compact table-expandable

   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | Option                        | Available Parameters  | Switch Description                                                                                      |
   |                               | (default in bold)     |                                                                                                         |
   +===============================+=======================+=========================================================================================================+
   | ``--help``                    | <tag>                 | Print the help message. The option can take one optional argument that will be used as a tag. If a tag  |
   |                               |                       | is provided, only options relevant to the tag will be printed.                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--show-header`` or ``-p``   | **true**, false       | Controls whether a header should appear in the output.                                                  |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--output-format`` or ``-f`` | **plain**, json       | Output format used for session list.                                                                    |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
