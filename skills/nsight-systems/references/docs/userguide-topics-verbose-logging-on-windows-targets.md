---
source_path: UserGuide/topics/verbose-logging-on-windows-targets.rst
title: #### Verbose Logging on Windows Targets
---
#### Verbose Logging on Windows Targets

Verbose logging is available when connecting to a Windows-based device from the GUI on the host. Nsight Systems installs its executable and library files into the following directory by default:


   C:\Program Files\NVIDIA Corporation\Nsight Systems 2023.3

To enable verbose logging on the target device, when launched from the host, follow these steps:

#. Close the host application.

#. Terminate the ``nsys`` process.

#. Place ``nvlog.config`` from host directory next to Nsight Systems Windows agent on the target device.

   -  Local Windows target:


         C:\Program Files\NVIDIA Corporation\Nsight Systems 2023.3\target-windows-x64

   -  Remote Windows target:


         %USERPROFILE%\AppData\Local\Temp\nvidia\nsight_systems

#. Start the host application and connect to the target device.

Logs on the target devices are collected into this file (if enabled):


   nsight-sys.log

in the same directory as Nsight Systems Windows agent.

Note:
   In some cases, debug logging can significantly slow down the profiler.
