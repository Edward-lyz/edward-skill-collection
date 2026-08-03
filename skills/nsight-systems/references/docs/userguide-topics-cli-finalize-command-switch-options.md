---
source_path: UserGuide/topics/cli-finalize-command-switch-options.rst
title: #### CLI Finalize Command Switch Options
---
#### CLI Finalize Command Switch Options

After choosing the ``finalize`` command switch, the following options are available. Usage:

::

   nsys [global-options] finalize [options] [subcommand]

   :name: table_finalize_table
   :class: table-compact table-expandable


   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | Option                        | Available Parameters  | Switch Description                                                                                      |
   |                               | (default in bold)     |                                                                                                         |
   +===============================+=======================+=========================================================================================================+
   | ``--discard``                 | all, <uuid>           | Discard deferred collections without generating reports. Use ``all`` to discard all deferred            |
   |                               |                       | collections, or specify a UUID to discard a specific one. Use ``nsys finalize list`` to see             |
   |                               |                       | available UUIDs.                                                                                        |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--force-overwrite``         | true, **false**       | If true, overwrite existing report files when finalizing. Default is false.                             |
   | or ``-f``                     |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--help``                    | <tag>                 | Print the help message. The option can take one optional argument that will be used as a tag. If a tag  |
   |                               |                       | is provided, only options relevant to the tag will be printed.                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--id``                      | <uuid>                | Finalize a specific deferred collection identified by its UUID. Use ``nsys finalize list`` to see       |
   |                               |                       | available UUIDs.                                                                                        |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--output``                  | directory path        | Output directory for finalized report files. The original filename is retained. By default, reports     |
   | or ``-o``                     |                       | are placed in the directory specified during collection.                                                |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--session``                 | session name          | Filter deferred collections by session name.                                                            |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+

### CLI Finalize List Subcommand

The ``finalize list`` subcommand displays pending deferred collections. Usage:

::

   nsys [global-options] finalize list [options]

   :name: table_finalize_list_table
   :class: table-compact table-expandable


   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | Option                        | Available Parameters  | Switch Description                                                                                      |
   |                               | (default in bold)     |                                                                                                         |
   +===============================+=======================+=========================================================================================================+
   | ``--output-format``           | **plain**, json       | Controls the output format.                                                                             |
   | or ``-f``                     |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--session``                 | session name          | Filter deferred collections by session name.                                                            |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--show-header``             | **true**, false       | Controls whether a header should appear in the output.                                                  |
   | or ``-p``                     |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
