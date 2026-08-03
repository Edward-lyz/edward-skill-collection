---
source_path: UserGuide/topics/unified-memory-gpu-page-faults.rst
title: #### Unified Memory GPU Page Faults
---
#### Unified Memory GPU Page Faults

The Unified Memory GPU page faults feature in Nsight Systems tracks the page
faults that occur when GPU code tries to access a memory page that resides on
the host.

Note:
   
   Collecting Unified Memory GPU page faults can cause overhead of up to 70% in
   testing. Use this functionality only when needed.

   :alt: Unified Memory GPU Page Faults on timeline
   :class: image
