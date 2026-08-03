---
source_path: UserGuide/topics/cli-import-command-switch-options.rst
title: #### CLI Import Command Switch Options
---
#### CLI Import Command Switch Options

The ``nsys import`` command converts a ``.qdstrm`` intermediate result file into
a ``.nsys-rep`` report file. A ``.qdstrm`` file can be produced by the CLI before
report generation completes. Usually, Nsight Systems converts it automatically at
the end of a collection. Use ``nsys import`` when automatic conversion did not
run or did not complete.

Use the same ``nsys`` version that generated the ``.qdstrm`` file to convert it.
The resulting ``.nsys-rep`` file can be opened in the same version or a more
recent version of the GUI.

After choosing the ``import`` command switch, the following options are
available. Usage:

::

   nsys [global-options] import [options] <input-file>

For example:

::

   nsys import report.qdstrm
   nsys import --input-file report.qdstrm
   nsys import --input-file report.qdstrm --output-file report.nsys-rep
   nsys import --input-file report.qdstrm --output-file report.nsys-rep --force-overwrite=true

If ``--output-file`` is not specified, the report is saved in the same directory
as the input file, using the input file name with the ``.nsys-rep`` extension.
If the output file already exists, ``nsys import`` fails unless
``--force-overwrite=true`` is used.

   :name: table_import_table
   :class: table-compact table-expandable


   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | Option                        | Available Parameters  | Switch Description                                                                                      |
   |                               | (default in bold)     |                                                                                                         |
   +===============================+=======================+=========================================================================================================+
   | ``--help``                    | <tag>                 | Print the help message. The option can take one optional argument that will be used as a tag. If a tag  |
   | or ``-h``                     |                       | is provided, only options relevant to the tag will be printed.                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--input-file``              | <filename>            | Path to the ``.qdstrm`` file to be imported. The input file can also be supplied as the positional      |
   | or ``-i``                     |                       | ``<input-file>`` argument.                                                                              |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--output-file``             | <filename>            | Use this option to provide a different file name or path for the resulting report file. If this option  |
   | or ``-o``                     |                       | is not specified, the default output file is the input file path with the ``.nsys-rep`` extension.      |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--force-overwrite``         | true, **false**       | If true, overwrite the output file if it already exists.                                                |
   | or ``-f``                     |                       |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
