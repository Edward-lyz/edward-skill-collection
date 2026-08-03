---
source_path: UserGuide/topics/addon-flamegraph.rst
title: ## Add-on Graphs - Flame Graph
---
## Add-on Graphs - Flame Graph

The generation of Flame Graphs from Nsight Systems reports is not a built-in
feature, but it is possible to create such graphs from Nsight Systems reports
with the script ``stackcollapse_nsys.py`` located at
``<nsys-install-dir>/<host-folder>/Scripts/Flamegraph``.
There is also a ``README.md file`` at that location with
additional usage details.


**Requirements:**

-   ``flamegraph.pl`` from `Brendan Gregg's FlameGraph
    github <https://github.com/brendangregg/FlameGraph>`__,
-   Perl


**Usage**


Generating flamegraph from Nsight Systems report file on Linux:

   
    python3 stackcollapse_nsys.py report.nsys-rep | ./flamegraph.pl > result_flamegraph.svg


Generating flamegraph from Nsight Systems report file on Windows:

   
    PowerShell -Command "python stackcollapse_nsys.py report.nsys-rep | perl flamegraph.pl > result_flamegraph.svg"

The script exports the report to SQLite, queries the CPU samples and passes them
as input to flamegraph.pl.

**Parameters**

The following parameters can be passed to the script:

   :name: table_flamegraph_table  
   :class: table-compact    


   +-------+-------------------------------+---------------------------------------------------+--------------------------------------------------------------------------------------------------------------+
   | Short | Long                          | Default                                           | Switch Description                                                                                           |
   +=======+===============================+===================================================+==============================================================================================================+
   |       | ``--nsys``                    | Current Nsight Systems CLI installation location  | Path to the Nsight Systems CLI directory (e.g., ``/opt/nvidia/nsight-systems/2022.4.1/target-linux-x64``).   |
   +-------+-------------------------------+---------------------------------------------------+--------------------------------------------------------------------------------------------------------------+
   | -o    | ``--out``                     | Output is written to stdout                       | Path to a result file containing a data suitable for ``flamegraph.pl``.                                      |
   +-------+-------------------------------+---------------------------------------------------+--------------------------------------------------------------------------------------------------------------+
   |       | ``--full_function_names``     | False                                             | Use full function names with return type, arguments and expanded templates, if available.                    |
   +-------+-------------------------------+---------------------------------------------------+--------------------------------------------------------------------------------------------------------------+


Note:

   By default, the script tries to shorten function definitions (eliminating
   return type, arguments and templates). In some complex cases
   shortening may fail and return a full function definition. To disable
   shortening defining ``--full_function_names=False`` argument can be used.


Here is an example of a Flame Graph generated from an Nsight Systems report. The
program was a debug build of GROMACS, running on two ranks, each running two
OpenMP threads.

      :alt: Flamegraph generated from Nsight Systems collection
      :class: image
