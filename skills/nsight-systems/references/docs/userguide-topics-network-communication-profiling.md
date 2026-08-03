---
source_path: UserGuide/topics/network-communication-profiling.rst
title: Network Communication Profiling
---
# Network Communication Profiling

Nsight Systems can be used to profiles several popular network communication
protocols and many network hardware components. To enable this, please select
the **Network profiling options** dropdown.

Note:
   Network hardware profiling uses statistical sampling of counters on the
   various appliances. Network communication API profiling uses direct trace
   of relevant function calls. Nsight Systems correlates the data as well as
   we can, however the inherent profiling differences make correlation somewhat
   inexact.

   :alt: Project settings screen
   :class: image

Then select the libraries you would like to trace:

   :alt: Communication library selection screen
   :class: image

The corresponding Nsight Systems CLI ``--trace|-t`` options are ``mpi``,
``oshmem``, ``ucx``, and ``nccl``. For multi-node runs, please refer to the section on
handling-application-launchers.
