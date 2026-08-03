---
source_path: InstallationGuide/topics/cuda-version.rst
title: ## CUDA Version
---
## CUDA Version

-  Nsight Systems supports CUDA 10.0+ for most platforms

-  Nsight Systems on Arm SBSA supports 10.2+

Note that CUDA version and driver version must be compatible.

   :name: table_cudaversion_table
   :class: table-compact

   ============ ======================
   CUDA Version Driver minimum version
   ============ ======================
   11.0         450
   10.2         440.30
   10.1         418.39
   10.0         410.48
   ============ ======================

From CUDA 11.X on, any driver from 450 on will be supported, although new
features introduced in more recent drivers will not be available.

For information about which drivers were specifically released with each toolkit,
see `CUDA Toolkit Release Notes - Major Component Versions
<https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html#cuda-major-component-versions>`__
