---
source_path: UserGuide/topics/gpu-direct-storage-trace.rst
title: ## GDS (GPUDirect Storage) Trace
---
## GDS (GPUDirect Storage) Trace

NVIDIA GPUDirect Storage (GDS) enables direct memory access (DMA) between
storage and GPU memory. This avoids a bounce buffer through the CPU, increasing
storage access bandwidth and decreasing latency and utilization load on the CPU.
Information about GDS can be found at `NVIDIA Magnum IO GPUDirect Storage
<https://docs.nvidia.com/gpudirect-storage/>`__.

Nsight Systems can capture information about GDS, specifically the various
cuFile API calls made by the profiled process.
GDS profiling is supported on Linux x64 and SBSA operating systems.

   :alt: GDS NVTX trace example
   :class: image


Note:
   Before collecting GDS metrics, ensure that **NVIDIA GPUDirect Storage** is
   installed correctly on your system. For installation instructions, refer to the
   `NVIDIA GPUDirect Storage Installation and Troubleshooting Guide
   <https://docs.nvidia.com/gpudirect-storage/troubleshooting-guide/index.html#nvidia-gpudirect-storage-installation-and-troubleshooting-guide/>`__.

   You can validate that GDS is installed correctly by running the gdscheck.py tool:


      /usr/local/cuda/gds/tools/gdscheck.py -p

   The tool should confirm that the intended filesystem type is supported, and that platform verification has passed successfully.
