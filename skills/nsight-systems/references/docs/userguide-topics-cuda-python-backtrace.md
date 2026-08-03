---
source_path: UserGuide/topics/cuda-python-backtrace.rst
title: ## CUDA Python Backtrace
---
## CUDA Python Backtrace

Nsight Systems for Arm server (SBSA) platforms and x86 Linux targets, is capable of capturing Python backtrace information when CUDA backtrace is being captured.

To enable CUDA Python backtrace from Nsight Systems:

**CLI** — Set ``--python-backtrace=cuda``.

**GUI** — Select the **Collect Python backtrace for selected API calls** checkbox.

      :alt: Configure CUDA Python Backtrace
      :class: image

Example screenshot:

   :alt: CUDA Python Backtrace
   :class: image
