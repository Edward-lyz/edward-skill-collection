---
source_path: UserGuide/topics/symbol-resolution.rst
title: ## Symbol Resolution
---
## Symbol Resolution

If stack trace information is missing symbols and you have a symbol file, you can manually re-resolve using the ResolveSymbols utility. This can be done by right-clicking the report file in the Project Explorer window and selecting "Resolve Symbols...".

Alternatively, you can find the utility as a separate executable in the ``[installation_path]\Host`` directory. This utility works with ELF format files, with Linux Debuginfod cache directories and Linux/QNX symbol servers, with Windows PDB directories and symbol servers, or with files where each line is in the format ``<start><length><name>``.

   :name: table_symbolres_table
   :class: table-compact   

   +-------+--------------------------+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | Short | Long                     | Argument        | Description                                                                                                                                                           |
   +=======+==========================+=================+=======================================================================================================================================================================+
   | -h    | ``--help``               |                 | Help message providing information about available options.                                                                                                           |
   +-------+--------------------------+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | -l    | ``--process-list``       |                 | Print global process IDs list                                                                                                                                         |
   +-------+--------------------------+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | -s    | ``--sym-file``           | filename        | Path to symbol file                                                                                                                                                   |
   +-------+--------------------------+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | -b    | ``--base-addr``          | address         | If set then <start> in symbol file is treated as relative address starting from this base address                                                                     |
   +-------+--------------------------+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | -p    | ``--global-pid``         | pid             | Which process in the report should be resolved. May be omitted if there is only one process in the report.                                                            |
   +-------+--------------------------+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | -f    | ``--force``              |                 | This option forces use of a given symbol file.                                                                                                                        |
   +-------+--------------------------+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | -i    | ``--report``             | filename        | Path to the report with unresolved symbols.                                                                                                                           |
   +-------+--------------------------+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | -o    | ``--output``             | filename        | Path and name of the output file. If it is omitted then "resolved" suffix is added to the original filename.                                                          |
   +-------+--------------------------+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | -d    | ``--directories``        | directory paths | List of symbol folder paths, separated by semi-colon characters. Available only on Windows.                                                                           |
   +-------+--------------------------+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | -v    | ``--servers``            | server URLs     | Windows: list of symbol servers that uses the same format as ``_NT_SYMBOL_PATH`` environment variable, i.e. ``srv*<LocalStore>*<SymbolServerURL>``.                   |
   |       |                          |                 |                                                                                                                                                                       |
   |       |                          |                 | Linux: list of Linux/QNX symbol servers separated by commas, i.e. ``SymbolServerURL1,SymbolServerURL2``.                                                              |
   |       |                          |                 | Note: ``DEBUGINFOD_URLS`` environment variable can be used instead of ``--servers`` option.                                                                           |
   +-------+--------------------------+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
   | -n    | ``--ignore-nt-sym-path`` |                 | Ignore the symbol locations stored in the ``_NT_SYMBOL_PATH`` environment variable. Available only on Windows.                                                        |
   +-------+--------------------------+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
