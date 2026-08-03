---
source_path: UserGuide/topics/connecting-to-the-target-device.rst
title: #### Connecting to the Target Device
---
#### Connecting to the Target Device

Nsight Systems provides a simple interface to profile on localhost or manage
multiple connections to Linux or Windows based devices via SSH. The network
connections manager can be launched through the device selection dropdown:

On x86_64:

      :alt: Empty device list
      :class: image

On Tegra:

      :alt: Empty device list
      :class: image

The dialog has simple controls that allow adding, removing, and modifying connections:

      :alt: Network connection
      :class: image


Warning:

   **Security notice**: SSH is only used to establish the initial connection to
   a target device, perform checks, and upload necessary files. The actual
   profiling commands and data are transferred through a raw, unencrypted
   socket. Nsight Systems should not be used in a network setup where
   attacker-in-the-middle attack is possible, or where untrusted parties may
   have network access to the target device.

While connecting to the target device, you will be prompted to input the user's
password. Note that if you choose to remember the password, it will be stored
in plain text in the configuration file on the host. Stored passwords are bound
to the public key fingerprint of the remote device.

The **No authentication** option is useful for devices configured for
passwordless login using ``root`` username. To enable such a configuration, edit
the file ``/etc/ssh/sshd_config`` on the target and specify the following option:

::

   PermitRootLogin yes

Then set empty password using ``passwd`` and restart the SSH service with ``service ssh restart``.

**Open ports**: The Nsight Systems agent requires port 22 and port 45555 to be
open for listening. You can confirm that these ports are open with the following
command:

::

   sudo firewall-cmd --list-ports --permanent 
   sudo firewall-cmd --reload

To open a port use the following command, skip ``--permanent`` option to open only for this session:

::

   sudo firewall-cmd --permanent --add-port 45555/tcp 
   sudo firewall-cmd --reload

Likewise, if you are running on a cloud system, you must open port 22 and port 45555 for ingress.

**Kernel Version Number** - To check for the version number of the kernel support
of Nsight Systems on a target device, run the following command on the remote device:

::

   cat /proc/quadd/version

Minimal supported version is 1.82.

Additionally, presence of Netcat command (``nc``) is required on the target
device. For example, on Ubuntu this package can be installed using the following
command:

::

   sudo apt-get install netcat-openbsd
