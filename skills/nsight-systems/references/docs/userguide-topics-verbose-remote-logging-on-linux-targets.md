---
source_path: UserGuide/topics/verbose-remote-logging-on-linux-targets.rst
title: #### Verbose Remote Logging on Linux Targets
---
#### Verbose Remote Logging on Linux Targets

Verbose logging is available when connecting to a Linux-based device from the
GUI on the host. This extra debug information is not available when launching
via the command line. Nsight Systems installs its executable and library files
into the following directory:

::

   /opt/nvidia/nsight_systems/

To enable verbose logging on the target device, when launched from the host,
follow these steps:

#. Close the host application.

#. Restart the target device.

#. Place ``nvlog.config`` from host directory to the ``/opt/nvidia/nsight_systems`` directory on target.

#. From SSH console, launch the following command:

   ::

      sudo /opt/nvidia/nsight_systems/nsys --daemon --debug

#. Start the host application and connect to the target device.

Logs on the target devices are collected into this file (if enabled):

::

   nsys.log

in the directory where ``nsys`` command was launched.

Please note that in some cases, debug logging can significantly slow down the profiler.
