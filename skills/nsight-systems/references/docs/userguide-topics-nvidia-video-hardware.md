---
source_path: UserGuide/topics/nvidia-video-hardware.rst
title: ## NVIDIA Video Hardware Profiling
---
## NVIDIA Video Hardware Profiling


#### Limitations/Requirements

NVIDIA Video Hardware profiling requires:

-  Linux (x86_64 or Arm) and Windows (x86_64)
-  Only covers desktop platforms
-  Driver version >= 535
-  GPU architecture Turing+


No NVIDIA Video Hardware profiling for:


-  Mobile platforms
-  Driver version < 535
-  GPU architecture < Turing
-  GSP is enabled and Driver < 545.31
-  MIG is enabled
-  Confidential computing is enabled
-  vGPU software < 18.0

To learn more about GSP and on which GPUs it’s enabled by default, see the
following link .

To turn off GSP permanently:


   sudo su -c 'echo options nvidia NVreg_EnableGpuFirmware=0 > /etc/modprobe.d/nvidia-gsp.conf'
   sudo update-initramfs -u # for Ubuntu-based systems

Then reboot.

Alternatively if you do not wish to reboot, this will disable
until the next reboot:


   sudo rmmod nvidia_uvm nvidia_drm nvidia_modeset nvidia && \
   sudo insmod /lib/modules/$(uname -r)/updates/dkms/nvidia.ko NVreg_EnableGpuFirmware=0
   for i in $(seq 0 7); do sudo nvidia-smi -i $i -pm ENABLED; done


#### Running from the CLI

The feature is enabled through the ``--gpu-video-devices`` option. It is available
from the ``nsys profile``, ``nsys launch`` and ``nsys start`` commands.

The option behaves exactly like ``--gpu-metrics-device`` and accepts the
following arguments:

-  ``--gpu-video-devices help``  - List supported devices and their IDs, List
   unsupported devices (if any) and the reason.
-  ``--gpu-video-devices none`` - Turn the feature off.
-  ``--gpu-video-devices all`` - Enable the feature on all supported devices. An
   error is returned if no devices support the feature.
-  ``--gpu-video-devices <id1,id2,...>`` - Enable the feature on the specified
   devices. The ID corresponds to what ``help`` returns. An error is returned if
   the ID is invalid.

Example:


   $ nsys profile --gpu-video-devices help
   Possible --gpu-video-devices values are:
       0: NVIDIA GeForce RTX 3070 PCI[0000:65:00.0]
       all: Select all supported GPUs
       none: Disable GPU video accelerator tracing [Default]

   Some GPUs don't support video accelerator tracing:
       Quadro P620 PCI[0000:04:00.0] (reason = Arch Pascal < Turing)

   See the user guide: https://docs.nvidia.com/nsight-systems/UserGuide/index.html


Note that this is a system-wide feature; i.e., it doesn’t require a program to
be launched.
