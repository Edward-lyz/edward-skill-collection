---
source_path: UserGuide/topics/gpu-direct-storage-counters.rst
title: ## GDS (GPUDirect Storage) Counters
---
## GDS (GPUDirect Storage) Counters

Nsight Systems can collect GDS user-space metrics from profiled processes.
GDS metrics collection is supported on Linux x64 and SBSA operating systems.

Note:
   This is only supported with GPUDirect Storage v1.16.0 or newer,
   which is available from CUDA Toolkit v13.1.

**Available arguments:**

- ``--gds-metrics``: Enable GDS (GPUDirect Storage) user-space performance metrics collection.
- ``--gds-libs-path=<path>``: Specify a directory containing GPUDirect Storage
  libraries (must contain libcufile.so). Use this argument if the GDS libraries
  are located in a different path than the default. Default is
  ``/usr/local/cuda/lib64``. This argument is used together with
  ``--gds-metrics``.

**Usage Example**

To profile a process with GDS metrics:

``./nsys profile --gds-metrics <target-application>``

If your GDS libraries are installed in a custom location:

``./nsys profile --gds-metrics --gds-libs-path=/custom/path/to/gds/libs <target-application>``

   :alt: GDS user-space report example
   :class: image
