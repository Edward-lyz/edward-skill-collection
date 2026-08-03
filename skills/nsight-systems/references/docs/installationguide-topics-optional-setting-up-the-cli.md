---
source_path: InstallationGuide/topics/optional-setting-up-the-cli.rst
title: ## Optional: Setting up the CLI
---
## Optional: Setting up the CLI

All Nsight Systems targets can be profiled using the CLI. Arm SBSA targets can
only be profiled using the CLI. The CLI is especially helpful when scripts are
used to run unattended collections or when access to the target system via ssh
is not possible. In particular, this can be used to enable collection in a
Docker container.

The CLI can be found in the Target directory of the Nsight Systems installation.
Users who want to install the CLI as a standalone tool can do so by copying the
files within the Target directory to the location of their choice.

If you wish to run the CLI without root (recommended mode) you will want to
install in a directory where you have full access.

Once you have the CLI set up, you can use the ``nsys status -e`` command to
check your environment.

::

   ~$ nsys status -e
   
   Sampling Environment Check
   Linux Kernel Paranoid Level = 1: OK
   Linux Distribution = Ubuntu
   Linux Kernel Version = 4.15.0-109-generic: OK
   Linux perf_event_open syscall available: OK
   Sampling trigger event available: OK
   Intel(c) Last Branch Record support: Available
   Sampling Environment: OK
          

This status check allows you to ensure that the system requirements for CPU
sampling using Nsight Systems are met in your local environment. If the
Sampling Environment is not OK, you will still be able to run various trace
operations.

Intel(c) Last Branch Record allows tools, including Nsight Systems to use
hardware to quickly get limited stack information. Nsight Systems will use this
method for stack resolution by default if available.

For information about changing these environment settings, see System
Requirements section in the Installation Guide. For information about changing
the backtrace method, see Profiling from the CLI in the User Guide.

To get started using the CLI, run ``nsys --help`` for a list of options or see
Profiling Applications from the CLI in the User Guide for full documentation.
