---
source_path: UserGuide/topics/nvidia-nvshmem-trace.rst
title: ## NVIDIA NVSHMEM Trace
---
## NVIDIA NVSHMEM Trace

The NVIDIA network communication library NVSHMEM has been instrumented using NVTX annotations. To enable tracing this library in Nsight Systems, turn on NVTX tracing in the GUI or CLI. To enable the NVTX instrumentation of the NVSHMEM library, make sure that the environment variable ``NVSHMEM_NVTX`` is set properly; e.g., ``NVSHMEM_NVTX=common``.
