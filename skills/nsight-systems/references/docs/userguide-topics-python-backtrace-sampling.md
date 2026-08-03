---
source_path: UserGuide/topics/python-backtrace-sampling.rst
title: ## Python Backtrace Sampling
---
## Python Backtrace Sampling

Nsight Systems for Arm server (SBSA) platforms, x86 Linux and Windows targets,
is capable of periodically capturing Python backtrace information.
This functionality is available when tracing Python interpreters of version 3.9 or later.
Capturing Python backtrace is done in periodic samples,
in a selected frequency ranging from 1Hz - 2KHz with a default value of 1KHz.
Note that this feature provides meaningful backtraces for Python processes,
when profiling Python-only workflows, consider disabling the CPU sampling option to reduce overhead.

In Nsight Systems GUI, Python backtrace sampling is visualized similar to CPU backtrace sampling.
See also Visualizing CPU Profiling Results .

To enable Python backtrace sampling from Nsight Systems:

**CLI** — Set ``--python-sampling=true`` and use the ``--python-sampling-frequency`` option to set the sampling rate.

**GUI** — Select the **Collect Python backtrace samples** checkbox.

      :alt: Configure Python Backtrace
      :class: image

Example screenshot:

   :alt: Python Backtrace sampling
   :class: image
