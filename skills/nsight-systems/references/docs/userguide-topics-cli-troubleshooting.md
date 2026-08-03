---
source_path: UserGuide/topics/cli-troubleshooting.rst
title: ## CLI Troubleshooting
---
## CLI Troubleshooting

**.nsys-rep file will not load**

If you have collected a report file using the CLI and the report will not open
in the GUI, check to see that your GUI version is the same or greater than the
CLI version you used. If it is not, download a new version of the Nsight Systems
GUI and you will be able to load and visualize your report.

This situation occurs most frequently when you update Nsight Systems using a CLI
only package, such as the package available from the NVIDIA HPC SDK.

**.nsys-rep file not generated**

The CLI initially generates a .qdstrm file. The .qdstrm file is an intermediate
result file, not intended for multiple imports. It needs to be processed. Usually
this happens automatically. If it does not, use ``nsys import`` to generate an
optimized .nsys-rep file. You can then use this file to visualize locally, to
open the result on a different machine, or for sharing results with teammates.

Use the same ``nsys`` version that generated the .qdstrm file to convert it into
a .nsys-rep file. This .nsys-rep file can then be opened in the same version or
more recent versions of the GUI.

Run ``nsys import`` on a system where the Nsight Systems CLI is installed. For
example::

   nsys import --input-file report.qdstrm
   nsys import --input-file report.qdstrm --output-file report.nsys-rep
   nsys import --input-file report.qdstrm --output-file report.nsys-rep --force-overwrite

For the complete command reference, see cli-import-command-switch-options.

**CLI command fails before profiling starts**

Your command shell may interpret special characters before Nsight Systems receives
the command line. If an ``nsys`` argument contains shell metacharacters such as
``*``, ``?``, ``[]``, ``~``, ``$``, ``;``, ``|``, ``&``, ``<``, ``>``, or
parentheses, quote the argument or escape the character. This is especially
important in shells such as zsh and fish, which can fail on unmatched wildcards
before the ``nsys`` command starts.

For example, an NVTX capture range for any domain can be written as either of
the following on Linux or macOS:


   nsys profile -c nvtx -w true -p 'profiler@*' ./app
   nsys profile -c nvtx -w true -p profiler@\* ./app
