---
source_path: InstallationGuide/topics/installing-gui-on-the-host-system.rst
title: ## Installing GUI on the Host System
---
## Installing GUI on the Host System

Copy the appropriate file to your host system in a directory where you have write and execute permissions. Run the install file, accept the EULA, and Nsight Systems will install on your system.

On Linux, there are special options to enable automated installation. Running the installer with the ``--accept`` flag will automatically accept the EULA, running with the ``--accept`` flag and the ``--quiet`` flag will automatically accept the EULA without printing to stdout. Running with ``--quiet`` without ``--accept`` will display an error.

The installation will create a Host directory for this host and a Target directory for each target this Nsight Systems package supports.

All binaries needed to collect data on a target device will be installed on the target by the host on first connection to the device. There is no need to install the package on the target device.

If installing from the CUDA Toolkit, see the CUDA Toolkit documentation .
