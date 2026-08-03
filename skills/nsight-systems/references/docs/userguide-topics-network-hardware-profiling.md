---
source_path: UserGuide/topics/network-hardware-profiling.rst
title: Network Hardware Profiling
---
# Network Hardware Profiling

Nsight Systems can be used to profile several popular network communication
protocols and many network hardware components. 

Note:
   Network hardware profiling uses statistical sampling of counters on the
   various appliances. Network communication API profiling uses direct trace
   of relevant function calls. Nsight Systems correlates the data as well as
   we can, however the inherent profiling differences make correlation somewhat
   inexact.
