---
source_path: UserGuide/topics/verbose-cli-logging-on-linux-targets.rst
title: #### Verbose CLI Logging on Linux Targets
---
#### Verbose CLI Logging on Linux Targets

To enable verbose logging of the Nsight Systems CLI and the target application's
injection behavior:

#. In the target-linux-x64 directory, rename the nvlog.config.template file
   to nvlog.config.

#. Inside that file, change the line:
   ::

      $ nsys-ui.log

   to:
   
   
   ::

      $ nsys-agent.log

#. Run a collection, either explicitly giving the path to the config file or with
   the config file in the same directory with the application. The
   ``target-linux-x64`` directory will then include a file named
   ``nsys-agent.log``.
   

   nsys profile --trace=osrt \
      --env-var=NVLOG_CONFIG_FILE="<install-dir>/target-linux-x64/nvlog.config" \
      sleep 1
 


Note:
   In some cases, debug logging can significantly slow down the profiler.
