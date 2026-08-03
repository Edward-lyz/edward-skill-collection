---
source_path: UserGuide/topics/launcher.rst
title: #### Launcher
---
#### Launcher

The second mechanism can be used with any binary. Use ``[installation_directory]/launcher`` to launch your application, for example:

::

   $ /opt/nvidia/nsight_systems/launcher ./my-binary --arguments

The process will be launched, daemonized, and wait for ``SIGUSR1`` signal. After attaching to the process with Nsight Systems, the user needs to manually resume execution of the process from command line:

::

   $ pkill -USR1 launcher

Note:

   Note that ``pkill`` will send the signal to any process with the matching name. If that is not desirable, use ``kill`` to send it to a specific process. The standard output and error streams are redirected to ``/tmp/stdout_<PID>.txt`` and ``/tmp/stderr_<PID>.txt``.

The launcher mechanism is more complex and less automated than the LD_PRELOAD option, but gives more control to the user.
