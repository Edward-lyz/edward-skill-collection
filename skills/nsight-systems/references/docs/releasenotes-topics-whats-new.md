---
source_path: ReleaseNotes/topics/whats-new.rst
title: What's New
---
# What's New

## Deprecation note:

The new ``--cpu-metrics`` option is designed to replace the existing
``--cpu-core-events``, ``--cpu-core-metrics``, ``--cpu-socket-events``, and
``--cpu-socket-metrics`` options. In upcoming releases,
using either of the old options will produce a deprecation notice. Note that
``--cpu-metrics`` is mutually exclusive with these legacy options and cannot
be combined with them.

**Note:** This deprecation notice does not affect the ``--cpu-core-events``
and ``--cpu-socket-events`` options in Nsight Systems Embedded Platforms Edition.


## Nsight Systems 2026.4.1 Highlights:

*  CUDA improvements

   *  NVTX ranges can now be projected onto the "All Streams" row, in
      addition to individual stream rows.
   *  Nsight Systems now displays readable names for cuTile kernels.
   *  CUDA workloads submitted through Direct3D 12 CUDA-in-Graphics (CiG)
      streams are now traced and displayed in the timeline.

*  PyTorch profiling

   *  The new ``--pytorch=functions-trace-shapes`` option captures PyTorch
      function calls and stores tensor shapes efficiently as binary payloads.
   *  Use the existing ``--pytorch=functions-trace`` option when call ranges
      are sufficient. It captures calls without shapes, reducing profiling
      overhead and trace size.

*  Graphics profiling improvements

   *  Added interception and display support for Direct3D 12 CiG streams.
   *  Added support for tracing Vulkan Reflex applications that use
      ``VK_NV_low_latency2``.
   *  Added support for tracing applications that use Direct3D 12 Runtime
      Bypass.
   *  Added support for the ``ID3D12Device15``,
      ``ID3D12ApplicationIdentity``, and ``ID3D12RuntimeValidationControl``
      Direct3D 12 interfaces.
   *  Added support for the ``VK_KHR_maintenance10``,
      ``VK_EXT_memory_decompression``, and
      ``VK_NV_compute_occupancy_priority`` Vulkan extensions.

*  Agentic AI Skill Pack

   *  Preview release focused on graphics performance analysis and frame
      stutter analysis.
   *  Delivers faster answers with lower token consumption and improved answer
      accuracy.
   *  Agent-agnostic design for use with leading AI agents and models.

*  Network profiling improvements

   *  Added collection of high-frequency NIC metrics through DOCA Telemetry
      Service (DTS). This enables users without root privileges to collect
      high-frequency NIC metrics on systems where DTS is installed.
   *  Improved NCCL recipes, including a new NCCL straggler recipe to pinpoint
      slow MPI ranks.

*  Storage profiling improvements

   *  Added an S3 object storage access summary recipe.
   *  Added NVIDIA SCADA metrics.

*  Time synchronization

   *  Nsight Systems now includes vClock, an unprivileged virtual clock
      designed to provide accurate time synchronization across multiple cluster
      nodes. This enables Nsight Systems to align distributed trace files
      collected across different cluster or cloud nodes.

*  Export

   *  NVTX binary payloads can now be exported as columnar fields using a
      dynamic schema.

*  NVIDIA Nsight Cloud

   *  Nsight Streamer updates.
   *  Docker updates.
   *  Kubernetes updates.
   *  Nsight Operator updates.
   *  Improvements for analysis, OpenTelemetry, and Dynamo.
   *  Learn more through the new docs site.
