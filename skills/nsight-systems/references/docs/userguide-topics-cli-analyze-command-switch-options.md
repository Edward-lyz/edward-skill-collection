---
source_path: UserGuide/topics/cli-analyze-command-switch-options.rst
title: #### CLI Analyze Command Switch Options
---
#### CLI Analyze Command Switch Options

The ``nsys analyze`` command generates and outputs a report to the terminal
using expert system rules on existing results. Reports are generated from an
SQLite export of a .nsys-rep file. If a .nsys-rep file is specified,
Nsight Systems will look for an accompanying SQLite file and use it. If no
SQLite export file exists, one will be created.

After choosing the ``analyze`` command switch, the following options are
available. Usage:

``nsys [global-options] analyze [options] [input-file]``

   :name: table_analyze_table
   :class: table-compact table-expandable


   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | Option                        | Available Parameters  | Switch Description                                                                                      |
   |                               | (default in bold)     |                                                                                                         |
   +===============================+=======================+=========================================================================================================+
   | ``--help``                    | <tag>, ``none``       | Print the help message. The option can take one optional argument that will be used as a tag. If a tag  |
   |                               |                       | is provided, only options relevant to the tag will be printed.                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--format``                  | column, table, csv,   | Specify the output format. The special name "." indicates the default format for the given output. The  |
   | or ``-f``                     | tsv, json, hdoc,      | default format for console is column, while files and process outputs default to csv. This option may   |
   |                               | htable, .             | be used multiple times. Multiple formats may also be specified using a comma-separated list             |
   |                               |                       | (<name[:args...][,name[:args...]...]>). See options available with each format at                       |
   |                               |                       | Available Export Formats .                                                                       |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--force-export``            | true, ``false``       | Force a re-export of the SQLite file from the specified report, even if an SQLite file already exists.  |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--force-overwrite``         | true, ``false``       | Overwrite any existing output files.                                                                    |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--help-formats``            | <format_name>, ALL,   | With no argument, list a summary of the available output formats. If a format name is given, a more     |
   |                               | ``[none]``            | detailed explanation of the format is displayed. If ``ALL`` is given, a more detailed explanation of    |
   |                               |                       | all available formats is displayed.                                                                     |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--help-rules``              | <rule_name>, ALL,     | With no argument, list available rules with a short description. If a rule name is given, a more        |
   |                               | ``[none]``            | detailed explanation of the rule is displayed. If ``ALL`` is given, a more detailed explanation  of all |
   |                               |                       | available rules is displayed.                                                                           |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--output``                  | ``-``, @<command>,    | Specify the output mechanism. There are three output mechanisms: print to console, output to file, or   |
   | or ``-o``                     | <basename>, .         | output to command. This option may be used multiple times. Multiple outputs may also be specified using |
   |                               |                       | a comma-separated list. If the given output name is "-", the output will be displayed on the console.   |
   |                               |                       | If the output name starts with "@", the output designates a command to run. The nsys command will be    |
   |                               |                       | executed and the analysis output will be piped into the command. Any other output is assumed to be the  |
   |                               |                       | base path and name for a file. If a file basename is given, the filename used will be:                  |
   |                               |                       | <basename>\_<analysis&args>.<output_format>. The default base (including path) is the name of the       |
   |                               |                       | SQLite file (as derived from the input file or ``--sqlite`` option), minus the extension. The output    |
   |                               |                       | "." can be used to indicate the analysis should be output to a file, and the default basename should be |
   |                               |                       | used. To write one or more analysis outputs to files using the default basename, use ``--output``. If   |
   |                               |                       | the output starts with "@", the nsys command output is piped to the given command. The command is run,  |
   |                               |                       | and the output is piped to the command's stdin (standard-input). The command's stdout and stderr remain |
   |                               |                       | attached to the console, so any output will be displayed directly to the console. Be aware there are    |
   |                               |                       | some limitations in how the command string is parsed. No shell expansions (including \*, ?, [], and ~)  |
   |                               |                       | are supported. The command cannot be piped to another command, nor redirected to a file using shell     |
   |                               |                       | syntax. The command and command arguments are split on whitespace, and no quotes (within the command    |
   |                               |                       | syntax) are supported. For commands that require complex command line syntax, it is suggested that the  |
   |                               |                       | command be put into a shell script file, and the script designated as the output command.               |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--quiet`` or ``-q``         |                       | Do not display verbose messages, only display errors.                                                   |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--rule``  or ``-r``         | cuda_memcpy_async,    | Specify the rule(s) to execute, including any arguments. This option may be used multiple times.        |
   |                               | cuda_memcpy_sync,     | Multiple rules may also be specified using a comma-separated list. See                                  |
   |                               | cuda_memset_sync,     | Expert Systems Analysis section and ``--help-rules`` switch for details                          |
   |                               | cuda_api_sync,        | on all rules.                                                                                           |
   |                               | gpu_gaps,             |                                                                                                         |
   |                               | gpu_time_util,        |                                                                                                         |
   |                               | dx12_mem_ops, ``all`` |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--sqlite``                  | <file.sqlite>         | Specify the SQLite export filename. If this file exists, it will be used. If this file doesn't exist    |
   |                               |                       | (or if ``--force-export`` was given) this file will be created from the specified .nsys-rep file before |
   |                               |                       | processing. This option cannot be used if the specified input file is also an SQLite file.              |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--timeunit``                | nsec, usec, msec,     | Set basic unit of time. The argument of the switch is matched by using the longest prefix matching.     |
   |                               | ``nanoseconds``,      | This means that it is not necessary to write a whole word as the switch argument. It is similar to      |
   |                               | microseconds,         | passing  a ":time=<unit>" argument to every formatter, although the formatter uses more strict naming   |
   |                               | milliseconds, seconds | conventions. See ``nsys analyze --help-formats column`` for detailed information on unit conversion.    |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
