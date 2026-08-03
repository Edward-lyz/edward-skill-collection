---
source_path: UserGuide/topics/gui-vnc-container.rst
title: ## GUI VNC container
---
## GUI VNC container

Nsight Systems provides a build script to build a self-isolated Docker container
with the Nsight Systems GUI and VNC server.

You can find the ``build.py`` script in the ``host-linux-x64/Scripts/VncContainer``
directory (or similar on other architectures) under your Nsight Systems
installation directory. You will need to have
Docker , and Python 3.5 or later.

**Available Parameters**

   :name: table_guivnc_table
   :class: table-compact 

   +------------+----------------------------------+-----------------------------------------------------------------------+
   | Short Name | Full Name                        | Description                                                           |
   +============+==================================+=======================================================================+
   |            | ``--vnc-password``               | (optional) Default password for VNC access (at least 6 characters).   |
   |            |                                  | If it is specified and empty user will be asked during the build.     |
   |            |                                  | Can be changed when running a container.                              |
   +------------+----------------------------------+-----------------------------------------------------------------------+
   | -aba       | ``--additional-build-arguments`` | (optional) Additional arguments, which will be passed to the          |
   |            |                                  | ``docker build`` command.                                             |
   +------------+----------------------------------+-----------------------------------------------------------------------+
   | -hd        | ``--nsys-host-directory``        | (optional) The directory with Nsight Systems host binaries (with GUI).|
   +------------+----------------------------------+-----------------------------------------------------------------------+
   | -td        | ``--nsys-target-directory``      | (optional, repeatable) The directory with Nsight Systems target       |
   |            |                                  | binaries (can be specified multiple times).                           |
   +------------+----------------------------------+-----------------------------------------------------------------------+
   |            | ``--tigervnc``                   | (optional) Use TigerVNC instead of x11vnc.                            |
   +------------+----------------------------------+-----------------------------------------------------------------------+
   |            | ``--http``                       | (optional) Install noVNC in the Docker container for HTTP access.     |
   +------------+----------------------------------+-----------------------------------------------------------------------+
   |            | ``--rdp``                        | (optional) Install xRDP in the Docker for RDP access.                 |
   +------------+----------------------------------+-----------------------------------------------------------------------+
   |            | ``--geometry``                   | (optional) Default VNC server resolution in the format WidthxHeight   |
   |            |                                  | (default 1920x1080).                                                  |
   +------------+----------------------------------+-----------------------------------------------------------------------+
   |            | ``--build-directory``            | (optional) The directory to save temporary files (with the write      |
   |            |                                  | access for the current user). By default, script or tmp directory     |
   |            |                                  | will be used.                                                         |
   +------------+----------------------------------+-----------------------------------------------------------------------+

**Ports**

These ports can be published from the container to provide access to the Docker container:

   :name: table_ports_table
   :class: table-compact   

   +---------------------+--------------------------------------+----------------------------------------------------+
   | Port                | Purpose                              | Condition                                          |
   +=====================+======================================+====================================================+
   | TCP 5900            | Port for VNC access                  |                                                    |
   +---------------------+--------------------------------------+----------------------------------------------------+
   | TCP 80 (optional)   | Port for HTTP access to noVNC server | Container is build with ``--http`` parameter       |
   +---------------------+--------------------------------------+----------------------------------------------------+
   | TCP 3389 (optional) | Port for RDP access                  | Container is build with ``--rdp`` parameter        |
   +---------------------+--------------------------------------+----------------------------------------------------+

**Volumes**

   :name: table_volumes_table
   :class: table-compact   

   +--------------------+---------------------------------+-----------------------------------------------------------------------------------------+
   | Docker folder      | Purpose                         | Description                                                                             |
   +====================+=================================+=========================================================================================+
   | /mnt/host          | Root path for shared folders    | Folder owned by the Docker user (inner content can be accessed from Nsight Systems GUI) |
   +--------------------+---------------------------------+-----------------------------------------------------------------------------------------+
   | /mnt/host/Projects |                                 | Folder with projects and reports, created by Nsight Systems UI in container             |
   +--------------------+---------------------------------+-----------------------------------------------------------------------------------------+
   | /mnt/host/logs     | Folder with inner services logs | May be useful to send reports to developers                                             |
   +--------------------+---------------------------------+-----------------------------------------------------------------------------------------+

**Environment variables**

   :name: table_envvar_table
   :class: table-compact   
     

   ================== ===============================================
   Variable Name      Purpose
   ================== ===============================================
   VNC_PASSWORD       Password for VNC access (at least 6 characters)
   NSYS_WINDOW_WIDTH  Width of VNC server display (in pixels)
   NSYS_WINDOW_HEIGHT Height of VNC server display (in pixels)
   ================== ===============================================

**Examples**

With VNC access on port 5916:

::

   sudo docker run -p 5916:5900/tcp -ti nsys-ui-vnc:1.0

With VNC access on port 5916 and HTTP access on port 8080:

::

   sudo docker run -p 5916:5900/tcp -p 8080:80/tcp -ti nsys-ui-vnc:1.0

With VNC access on port 5916, HTTP access on port 8080, and RDP access on port 33890:

::

   sudo docker run -p 5916:5900/tcp -p 8080:80/tcp -p 33890:3389/tcp -ti nsys-ui-vnc:1.0

With VNC access on port 5916, shared "HOME" folder from the host, VNC server
resolution 3840x2160, and custom VNC credential placeholder redacted

   sudo docker run -p 5916:5900/tcp -v $HOME:/mnt/host/home -e NSYS_WINDOW_WIDTH=3840 -e NSYS_WINDOW_HEIGHT=2160 -e VNC_credential placeholder redacted -ti nsys-ui-vnc:1.0

With VNC access on port 5916, shared "HOME" folder from the host, and the
projects folder to access reports created by the Nsight Systems GUI in container:

::

   sudo docker run -p 5916:5900/tcp -v $HOME:/mnt/host/home -v /opt/NsysProjects:/mnt/host/Projects -ti nsys-ui-vnc:1.0
