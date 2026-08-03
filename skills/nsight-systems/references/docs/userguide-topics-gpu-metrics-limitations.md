---
source_path: UserGuide/topics/gpu-metrics-limitations.rst
title: #### Limitations
---
#### Limitations

-  If metric sets with NVLink are used but the links are not active, they may
   appear as fully utilized.

-  Only one tool that subscribes to these counters can be used at a time,
   therefore, Nsight Systems GPU Metrics feature cannot be used at the same time
   as the following tools:

   -  Nsight Graphics

   -  Nsight Compute

   -  DCGM (Data Center GPU Manager)

      Use the following command:

      -  ``dcgmi profile --pause``
      -  ``dcgmi profile --resume``

      Or API:

      -  ``dcgmProfPause``
      -  ``dcgmProfResume``

   -  Non-NVIDIA products which use:

      -  CUPTI sampling used directly in the application. CUPTI trace is okay
         (although it will block Nsight Systems CUDA trace)
      -  DCGM library

-  Nsight Systems limits the amount of memory that can be used to store GPU
   Metrics samples. Analysis with higher sampling rates or on GPUs with more
   SMs has a risk of exceeding this limit. This will lead to gaps on timeline
   filled with ``Missing Data`` ranges. Future releases will reduce the
   frequency of this happening.
