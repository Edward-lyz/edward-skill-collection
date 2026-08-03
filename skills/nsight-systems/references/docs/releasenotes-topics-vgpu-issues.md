---
source_path: ReleaseNotes/topics/vgpu-issues.rst
title: ## vGPU Issues
---
## vGPU Issues

-  When running Nsight Systems on vGPU you should always use the profiler grant. See Virtual GPU Software Documentation  for details on enabling NVIDIA CUDA Toolkit profilers for NVIDIA vGPUs. Without the grant, unexpected migrations may crash a running session, report an error and abort. It may also silently produce a corrupted report which may be unloadable or show inaccurate data with no warning.

-  Starting with vGPU 13.0, device level metrics collection is exposed to end users even on vGPU. Device level metrics will give info about all the work being executed on the GPU. The work might be in the same VM or some other VM running on the same physical GPU.

-  As of CUDA 11.4 and R470 TRD1 driver release, Nsight Systems is supported in a vGPU environment which requires a vGPU license. If the license is not obtained after 20 minutes, the tool will still work but the reported GPU performance metrics data will be inaccurate. This is because of a feature in vGPU environment which reduces performance but retains functionality as specified in Grid Licensing User Guide .
