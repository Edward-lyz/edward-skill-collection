---
source_path: UserGuide/topics/windows-system-wide-api-trace.rst
title: ## System Wide API Trace on Windows
---
## System Wide API Trace on Windows

On Windows, Nsight Systems can trace certain APIs (currently supported: DX11, DX12
and Vulkan) in already-running applications, by way of system-wide API trace from
the CLI.
       
To initiate system-wide API tracing, run the Nsight Systems CLI with the
``--trace`` option including one or more of the supported APIs, the
``--system-wide`` option set to ``true``, and without specifying a target
application. System-wide API tracing may be combined with trace types that are
always system-wide such as ``--trace=wddm``.

To trace a DX11 or DX12 target application, it must gain the system focus, the
user must either click on the application window or use Alt+Tab to select it.

For example, to trace multiple DX12 applications with PIX markers and GPU
workload trace, as well as WDDM events for the next 20 seconds, run the command:


   nsys profile --trace=dx12-annotations,wddm --dx12-gpu-workload=individual
   --duration=20
    
    
Then click each of the target applications' windows to give them focus.

To trace a Vulkan target application, it must be launched after the ``nsys profile``
command has been executed.
