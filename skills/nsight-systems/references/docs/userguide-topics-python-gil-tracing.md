---
source_path: UserGuide/topics/python-gil-tracing.rst
title: ## Python GIL Tracing
---
## Python GIL Tracing

Nsight Systems for Arm server (SBSA) platforms, x86 Linux and Windows targets, is capable of tracing when Python threads are waiting to hold and holding the GIL (Global Interpreter Lock).

The Python source code does not require any changes. This feature requires CPython interpreter, release 3.9 or later.

This feature is not supported on Python that was compiled with ``Py_GIL_DISABLED=1`` (See Python documentation  for details).

**CLI** — Set ``--trace=python-gil``.

**GUI** — Select the **Trace GIL** checkbox under **Python profiling options**.

      :alt: Configure Python GIL Tracing
      :class: image

Example screenshot:

   :alt: Python GIL Tracing
   :class: image
