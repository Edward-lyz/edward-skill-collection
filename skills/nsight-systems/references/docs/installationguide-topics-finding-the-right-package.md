---
source_path: InstallationGuide/topics/finding-the-right-package.rst
title: ## Finding the Right Package
---
## Finding the Right Package

Nsight Systems is available for multiple targets and multiple host OSs. To
choose the right package, first consider the target system to be analyzed.

-  For Tegra target systems, select Nsight Systems Embedded Platforms Edition available as part of
   NVIDIA JetPack SDK . For
   older Tegra targets, see `NVIDIA JetPack Archives
   <https://developer.nvidia.com/embedded/jetpack-archive>`__.

-  For x86_64 or Arm SBSA select from the target packages from Nsight Systems Workstation Edition,
   available from https://developer.nvidia.com/nsight-systems. This web release
   will always contain the latest and greatest Nsight Systems features.

-  The x86_64 and Arm SBSA target versions of Nsight Systems are also available
   in the CUDA Toolkit. 

Each package is limited to one architecture. For example, Tegra packages do not
contain support for profiling x86 targets, and x86 packages do not contain
support for profiling Tegra targets.

After choosing an appropriate target version, select the package corresponding
to the host OS, the OS on the system where results will be viewed. These
packages are in the form of common installer types: .msi for Windows; .run,
.rpm, and .deb for x86 Linux; and .dmg for the macOS installer.

**Tegra packages**

-  Windows host - Install .msi on Windows machine. Enables remote access to
   Tegra device for profiling.

-  Linux host - Install .run on Linux system. Enables remote access to Tegra
   device for profiling.

-  macOS host - Install .dmg on macOS machine. Enables remote access to Tegra
   device for profiling.

**x86_64 packages**

-  Windows host - Install .msi on Windows machine. Enables remote access to
   Linux x86_64 or Windows devices for profiling as well as running on local system.

-  Linux host - Install .run, .rpm, or .deb on Linux system. Enables remote
   access to Linux x86_64 or Windows devices for profiling or running collection
   on localhost.

-  Linux CLI only - The Linux CLI is shipped in all x86 packages, but if you
   just want the CLI, we have a package for that. Install .deb or .rpm on Linux system.
   Enables only CLI collection, report can be imported or opened in x86_64 host.

-  macOS host - Install .dmg on macOS machine. Enables remote access to Linux
   x86_64 device for profiling.

**Arm SBSA packages**

-  Arm SBSA host - Install .run, .rpm, or .deb on Arm SBSA system. Enables
   profiling and report viewing on local system.

-  Arm SBSA CLI only - The Arm SBSA CLI is shipped in all host packages, but
   if you just want the CLI, we have a package for that. Install .deb or .rpm
   on Arm SBSA system. Enables only CLI collection, report can be imported
   or opened in GUI on any supported host platform.

Note:

   On Windows machines we recommend installing Nsight Systems to the default
   secure location under Program Files.
