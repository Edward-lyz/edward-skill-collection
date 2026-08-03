---
source_path: InstallationGuide/topics/overview.rst
title: Overview
---
# Overview

Nsight Systems is a statistical sampling profiler with tracing features. It is
designed to work with devices and devkits based on NVIDIA Tegra SoCs
(system-on-chip), Arm SBSA (server based system architecture) systems, and
systems based on the x86_64 processor architecture that also include NVIDIA GPU(s).

Throughout this document we will refer to the device on which profiling happens
as the **target**, and the computer on which the user works and controls the
profiling session as the **host**. Note that for x86_64 based systems these may
be on the same device, whereas with Tegra or Arm based systems they will always
be separate.

Furthermore, three different activities are distinguished as follows:

-  **Profiling** — The process of collecting any performance data. A profiling
   session in Nsight Systems typically includes sampling and tracing.
-  **Sampling** — The process of periodically stopping the *profilee* (the
   application under investigation during the profiling session), typically to
   collect backtraces (call stacks of active threads), which allows you to
   understand statistically how much time is spent in each function.
   Additionally, hardware counters can also be sampled. This process is
   inherently imprecise when a low number of samples have been collected.
-  **Tracing** — The process of collecting precise information about various
   activities happening in the profilee or in the system. For example, profilee
   API execution may be traced providing the exact time and duration of a
   function call.

Nsight Systems supports multiple generations of Tegra SoCs, NVIDIA discrete GPUs,
and various CPU architectures, as well as various target and host operating
systems. This documentation describes the full set of features available in any
version of Nsight Systems. In the event that a feature is not available in all
versions, that will be noted in the text. In general, Nsight Systems Embedded Platforms Edition indicates
the package that supports Tegra processors for the embedded and automotive
market and Nsight Systems Workstation Edition supports x86_64 and Arm server (SBSA) processors
for the workstation, cluster, and cloud markets.

Common features that are supported by Nsight Systems on most platforms include
the following:

-  Sampling of the profilee and collecting backtraces using multiple algorithms
   (such as frame pointers or DWARF data). Building top-down, bottom-up, and
   flat views as appropriate. This information helps identify performance
   bottlenecks in CPU-intensive code.

-  Sampling or tracing system power behaviors, such as CPU frequency.

-  (Only on Nsight Systems Embedded Platforms Edition)Sampling counters from Arm PMU (Performance Monitoring
   Unit). Information such as cache misses gets statistically correlated with
   function execution.

-  Support for multiple windows. Users with multiple monitors can see multiple
   reports simultaneously, or have multiple views into the same report file.

With Nsight Systems, a user could:

-  Identify call paths that monopolize the CPU.

-  Identify individual functions that monopolize the CPU (across different call
   paths).

-  For Nsight Systems Embedded Platforms Edition, identify functions that have poor cache utilization.

-  If platform supports CUDA, see visual representation of CUDA Runtime and
   Driver API calls, as well as CUDA GPU workload. Nsight Systems uses the CUDA
   Profiling Tools Interface (CUPTI), for more information, see: `CUPTI
   documentation <https://docs.nvidia.com/cuda/cupti/index.html>`__.

-  If the user annotates with NVIDIA Tools Extension (NVTX), see visual
   representation of NVTX annotations: ranges, markers, and thread names.

-  For Windows targets, see visual representation of D3D12: which API calls are
   being made on the CPU, graphic frames, stutter analysis, as well as GPU
   workloads (command lists and debug ranges).

-  For x86_64 targets, see visual representation of Vulkan: which API calls are
   being made on the CPU, graphic frames, stutter analysis, as well as Vulkan
   GPU workloads (command buffers and debug ranges).
