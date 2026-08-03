---
source_path: UserGuide/topics/ubuntu-and-centos-without-root-privileges.rst
title: ### Ubuntu and CentOS Without Root Privileges
---
### Ubuntu and CentOS Without Root Privileges

-  Choose the directory where dependencies will be installed (``dependencies_path``). This directory
   should be writeable for the current user.

-  Launch the following command (if it has already been run, move to the next step), which will
   install all the required libraries in ``[dependencies_path]``:

   ::

      [installation_path]/host-linux-[arch]/Scripts/DependenciesInstaller/install-dependencies-without-root.sh [dependencies_path]

-  Further, use the following command to launch the Linux GUI:

   ::

      source [installation_path]/host-linux-[arch]/Scripts/DependenciesInstaller/setup-dependencies-environment.sh [dependencies_path] && [installation_path]/host-linux-[arch]/nsys-ui
