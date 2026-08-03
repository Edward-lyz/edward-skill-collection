---
source_path: UserGuide/topics/python-nvtx-annotations.rst
title: ## Python Functions Trace
---
## Python Functions Trace

Nsight Systems for Arm server (SBSA) platforms, x86 Linux and Windows targets, is capable of using NVTX to annotate Python functions.

The Python source code does not require any changes. This feature requires CPython interpreter, release 3.8 or later.

The annotations are configured in a JSON file. An example file is located in Nsight Systems installation folder in ``<target-platform-folder>/PythonFunctionsTrace/annotations.json``.

For PyTorch applications, Nsight Systems provides a predefined annotations file located in ``<target-platform-folder>/PythonFunctionsTrace/pytorch.json``.

For Dask applications, Nsight Systems provides a predefined annotations file located in ``<target-platform-folder>/PythonFunctionsTrace/dask.json``.

Note:
   Annotating a function from the module ``__main__`` is not supported.


To enable Python functions trace from Nsight Systems:

**CLI** — Set ``--python-functions-trace=<json_file>``.

**GUI** — Select the **Python Functions trace** checkbox and specify the JSON file.

      :alt: Configure Python Functions Trace
      :class: image

Example screenshot:

   :alt: Python Functions Trace
   :class: image
