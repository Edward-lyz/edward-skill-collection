---
source_path: UserGuide/topics/ld_preload.rst
title: #### LD_PRELOAD
---
#### LD_PRELOAD

The first mechanism uses ``LD_PRELOAD`` environment variable. It only works with dynamically linked binaries, since static binaries do not invoke the runtime linker, and therefore are not affected by the ``LD_PRELOAD`` environment variable.

-  For ARMv7 binaries, preload

   ::

      /opt/nvidia/nsight_systems/libLauncher32.so

-  Otherwise if running from host, preload

   ::

      /opt/nvidia/nsight_systems/libLauncher64.so

-  Otherwise if running from CLI, preload

   ::

      [installation_directory]/libLauncher64.so

The most common way to do that is to specify the environment variable as part of the process launch command, for example:

::

   $ LD_PRELOAD=/opt/nvidia/nsight_systems/libLauncher64.so ./my-aarch64-binary --arguments

When loaded, this library will send itself a ``SIGSTOP`` signal, which is equivalent to typing ``Ctrl+Z`` in the terminal. The process is now a background job, and you can use standard commands like jobs, ``fg`` and ``bg`` to control them. Use ``jobs -l`` to see the PID of the launched process.

When attaching to a stopped process, Nsight Systems will send ``SIGCONT`` signal, which is equivalent to using the ``bg`` command.
