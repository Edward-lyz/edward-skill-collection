---
source_path: InstallationGuide/topics/requirements-for-x86_64-and-arm-sbsa-targets-on-linux.rst
title: ## Requirements for x86_64 and Arm SBSA Targets on Linux
---
## Requirements for x86_64 and Arm SBSA Targets on Linux

When attaching to x86_64 or Arm SBSA Linux-based target from the GUI on the host,
the connection is established through SSH.

**Use of Linux Perf**: To collect thread scheduling data and IP (instruction
pointer) samples, the Linux operating system's ``perf_event_paranoid`` level
must be 2 or less. Use the following command to check:


      cat /proc/sys/kernel/perf_event_paranoid

If the output is >2, then do the following to temporarily adjust the paranoid
level (note that this has to be done after each reboot):


      sudo sh -c 'echo 2 >/proc/sys/kernel/perf_event_paranoid'

To make the change permanent, use the following command:


      sudo sh -c 'echo kernel.perf_event_paranoid=2 > /etc/sysctl.d/local.conf'

**Kernel version**: To collect thread scheduling data and IP (instruction
pointer) samples and backtraces, the kernel version must be:

-  3.10.0-693 or later for CentOS and RedHat Enterprise Linux 7.4+

-  4.3 or greater for all other distros including Ubuntu

To check the version number of the kernel on a target device, run the following
command on the device:


      uname -a

Note:

   Only CentOS, RedHat, and Ubuntu distros are tested/confirmed to work correctly.

**glibc version**: To check the glibc version on a target device, run the
following command:


      ldd --version

Nsight Systems requires glibc 2.17 or newer.

**CUDA**: See above for supported CUDA versions in this release. Use the
deviceQuery command to determine the CUDA driver and runtime versions on the
system. The deviceQuery command is available in the CUDA SDK. It is normally
installed at:


      /usr/local/cuda/samples/1_Utilities/deviceQuery

Only pure 64-bit environments are supported. In other words, 32-bit systems or
32-bit processes running within a 64-bit environment are not supported.

Nsight Systems requires write permission to the ``/var/lock`` directory on the
target system.

**Docker**: See Container Support section of the User Guide for
more information.
