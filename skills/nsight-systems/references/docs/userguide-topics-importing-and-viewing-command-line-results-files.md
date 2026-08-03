---
source_path: UserGuide/topics/importing-and-viewing-command-line-results-files.rst
title: ## Opening Command Line Results Files for Visualization
---
## Opening Command Line Results Files for Visualization

**Open CLI results in GUI**

The CLI will generate an .nsys-rep file after analysis is complete. This file can
be opened in any GUI that is the same version or a more recent version.

The opening of really large, multi-gigabyte, .nsys-rep files may take up all of
the memory on the host computer and lock up the system. This will be fixed in a
later version.

**Importing Windows ETL files**

For Windows targets, ETL files captured with Xperf or the ``log.cmd`` command
supplied with GPUView in the Windows Performance Toolkit can be imported to
create reports as if they were captured with Nsight Systems's "WDDM trace" and
"Custom ETW trace" features. Simply choose the .etl file from the Import dialog
to convert it to a .nsys-rep file.
