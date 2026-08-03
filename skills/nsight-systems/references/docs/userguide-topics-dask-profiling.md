---
source_path: UserGuide/topics/dask-profiling.rst
title: ## Dask Profiling
---
## Dask Profiling

Nsight Systems for Arm server (SBSA) platforms, x86 Linux and Windows targets, is capable of automatically annotating common Dask functions with execution time ranges.

The Python source code does not require any changes. This feature requires CPython interpreter, release 3.8 or later.

Set ``--dask=functions-trace`` for enabling Dask functions trace. This option sets ``--python-functions-trace=<nsys_install_dir>/<target-arch>/PythonFunctionsTrace/dask.json`` and will rename relevant threads to 'Dask Worker' and 'Dask Scheduler'.

``dask.json`` can be modified to include additional functions to be traced from any Python module.

Example screenshot:

   :alt: Dask Profiling
   :class: image
