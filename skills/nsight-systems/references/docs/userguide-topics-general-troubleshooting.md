---
source_path: UserGuide/topics/general-troubleshooting.rst
title: ## General Troubleshooting
---
## General Troubleshooting

**Profiling**

If the profiler behaves unexpectedly during the profiling session, or the
profiling session fails to start, try the following steps:

-  Close the host application.
-  Restart the target device.
-  Start the host application and connect to the target device.

Nsight Systems uses a settings file (``NVIDIA Nsight Systems.ini``) on the host
to store information about loaded projects, report files, window layout
configuration, etc. Location of the settings file is described in the
**Help → About** dialog. Deleting the settings file will restore Nsight Systems
to a fresh state, but all projects and reports will disappear from the Project
Explorer.


**Profiling Games**

In launcher-based platforms (like Steam), if you attempt to run the game
executable directly from Nsight Systems the game will detect that the
launcher is missing. It will therefore launch the launcher and then
self-terminate.

To avoid this, Nsight Systems on Windows automatically attaches to child
processes spawned by the target process that Nsight Systems launched. Instead
of setting Nsight Systems to launch the game, set Nsight Systems to launch the
game platform client, and use the client GUI to launch the game.

Nsight Systems is configured to ignore the game platform client and launcher
apps, and will attach to the game executable that the client launches.

An example workflow:

#. Verify the Steam client is not running. Select the Quit command to terminate
   Steam if it is running.
	
#. Configure Nsight Systems to launch the Steam client with a manual collection
   option. It is recommended you check the hotkey checkbox to begin data
   collection from within the game without requiring you to switching window
   focus.
	
#. Click Start. Nsight Systems will launch the Steam client.

#. Use Steam GUI to launch the game.

#. When the game is running and you have reached the scene you want to profile,
   press the ``F12`` hotkey to start Nsight Systems data collection. Let the game
   continue running while Nsight Systems collects its profiling data
   (typically 10-60 seconds, or however long is relevant for you). Press
   ``F12`` again to end the collection.


**Environment Variables**

By default, Nsight Systems writes temporary files to the system temporary
directory (``/tmp`` on Linux, ``%TEMP%`` on Windows). You can override this
by setting the ``NSYS_TMPDIR`` environment variable. This is the recommended
approach when:

-  ``/tmp`` is read-only or has limited storage (e.g., containers, HPC nodes).
-  You need Nsight Systems's temporary files in a specific location for organizational
   or debugging purposes.
-  Your application uses ``/tmp`` or ``TMPDIR`` on Linux to store its temporary
   files and you do not want any conflicts with Nsight Systems's temporary files.

Example on Linux:


   NSYS_TMPDIR=/testdata nsys profile -t cuda matrixMul

Example on Windows (PowerShell):


   $env:NSYS_TMPDIR = "C:\NsysTemp"
   nsys profile -t cuda myapp.exe

The ``TMPDIR`` environment variable (Linux) and ``TEMP``/``TMP`` (Windows)
are also respected as fallbacks when ``NSYS_TMPDIR`` is not set.

Note:

   When using ``--defer-report``, make sure ``NSYS_TMPDIR`` is set to the
   same value for both the profiling run and the ``nsys finalize`` command.

Environment variable control support for Windows target trace is not available,
but there is a quick workaround:

-  Create a batch file that sets the env vars and launches your application.
-  Set Nsight Systems to launch the batch file as its target; i.e., set the
   project settings target path to the path of batch file.
-  Start the trace. Nsight Systems will launch the batch file in a new cmd
   instance and trace any child process it launches. In fact, it will trace the
   whole process tree whose root is the cmd running your batch file.

**WebGL Testing**

Nsight Systems cannot profile using the default Chrome launch command. To profile
WebGL please follow the following command structure:


   “C:\Program Files (x86)\Google\Chrome\Application\chrome.exe”
          --inprocess-gpu --no-sandbox --disable-gpu-watchdog --use-angle=gl
          https://webglsamples.org/aquarium/aquarium.html
          

**Common Issues with QNX Targets**

-  Make sure that ``tracelogger`` utility is available and can be run on the target.

-  Make sure that ``/tmp`` directory is accessible and supports sub-directories.

-  When switching between Nsight Systems versions, processes related to the
   previous version, including profiled applications forked by the daemon, must be
   killed before the new version is used. If you experience issues after switching
   between Nsight Systems versions, try rebooting the target.
