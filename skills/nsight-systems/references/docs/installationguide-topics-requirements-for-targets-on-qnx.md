---
source_path: InstallationGuide/topics/requirements-for-targets-on-qnx.rst
title: ## Requirements for QNX targets
---
## Requirements for QNX targets

**Development environment**:

Nsight Systems supports profiling DRIVE OS QNX targets in development environments.

Some features require additional setup, such as deploying specific files to the
target system or creating configuration files. See profiling_embedded_virtual_machines
for detailed instructions.

**Safety environment**:

Nsight Systems provides limited profiling capabilities in QNX Safety environment.

Warning:
    Nsight Systems is a profiling and analysis tool that is not safety-certified.
    It must not be used in environments where software controls driving decisions
    or impacts human safety.

The *prod_debug_extra* overlay is required to enable Nsight Systems in safety environment.

Available features:

+------------------------------------------+----------------------+
| Feature name                             | First supported in   |
+==========================================+======================+
| Tracelogger trace (CPU thread states and | 6.0.8.x              |
| context switches)                        |                      |
+------------------------------------------+----------------------+
| Hypervisor trace (VM context switches,   | 6.0.8.x              |
| interrupts, traps, etc. - collected      |                      |
| through eventlib)                        |                      |
+------------------------------------------+----------------------+
| VMProfiler (Cross-Hypervisor sampling)   | 6.0.8.x              |
+------------------------------------------+----------------------+
| OSRT trace (trace of C runtime functions)| 6.0.8.x              |
+------------------------------------------+----------------------+
| NVTX trace (trace of user-added NVTX     | 6.0.8.x              |
| instrumentation)                         |                      |
+------------------------------------------+----------------------+

Note:
    For DRIVE OS installation details, more information on running environments or filesystem overlays,
    please refer to NVIDIA DRIVE OS Documentation .
