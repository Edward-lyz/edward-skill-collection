---
source_path: UserGuide/topics/vmprofiler.rst
title: Profiling with DRIVE Hypervisor
---
# Profiling with DRIVE Hypervisor

Nsight Systems and DRIVE Hypervisor support periodic CPU sampling with call stacks. It works both on DRIVE Linux and QNX.

The call stacks are collected using frame pointers.  The Linux kernel, QNX kernel, and user space libraries provided by NVIDIA are compiled with frame pointers.  To ensure correct call stacks, we recommend compiling all application code with frame pointer support, using ``-fno-omit-frame-pointer`` with GCC, Clang, and QCC.

This is an experimental feature and is expected to change in the future.

**The symbols can be resolved both for user space code, and for kernel space code:**

- In the user space, the Cross-Hypervisor (XHV) sampling events are matched with the CPU thread state trace coming from Linux Perf and QNX Tracelogger. After that, Nsight Systems can know the module filename, and can resolve symbols directly from these files if they are unstripped, or by looking up additional files with symbols. See more details below.
- In the kernel space (Linux kernel, QNX kernel, and additional service VMs), the symbols are resolved using the ELF file with symbols specified. ``kernel_symbols.json`` input file specifies the location of this ELF file.

**Please follow the steps below to learn how to:**

- Flash the devkit (these steps are given just as an example, the exact steps might differ in your case).
- Copy the necessary files: pct.json, eventlib schema files, and kernel_symbols.json.
- Compose kernel_symbols.json to allow resolving symbols in the Linux kernel, QNX kernel, and additional service VMs.
- See example CLI commands to collect data.

**Known issues:**

- At the moment, this feature is not compatible with standard CPU sampling on Linux and QNX.
- When enabled together, hypervisor trace plus XHV sampling can write too much data into the same eventlib buffers, and the Nsight Systems agent might not be able to keep up with the rate, losing events.  If that happens, please disable hypervisor trace events with ``--xhv-trace-events=none``.


**Flashing DRIVE OS QNX/Linux**

Log into the NVIDIA GPU Cloud (NGC):


   sudo docker login nvcr.io

   Username: ``$oauthtoken``
   credential placeholder redacted API key>

Docker command:

::

   sudo docker run --rm --privileged --net host \
       -v /dev/bus/usb:/dev/bus/usb \
       -v /tmp:/drive_flashing \
       -it <docker image>

``<docker image>`` - docker image link.

Examples:

6.0.8.0 QNX:

::

   sudo docker run --rm --privileged --net host \
       -v /dev/bus/usb:/dev/bus/usb \
       -v /tmp:/drive_flashing \
       -it nvcr.io/{MY_NGC_ORG}/driveos-pdk/drive-agx-orin-qnx-aarch64-pdk-build-x86:6.0.8.0-0003

6.0.9.1 QNX:

::

   sudo docker run --rm --privileged --net host \
       -v /dev/bus/usb:/dev/bus/usb \
       -v /tmp:/drive_flashing \
       -it nvcr.io/{MY_NGC_ORG}/driveos-pdk/drive-agx-orin-qnx-aarch64-pdk-build-x86:6.0.9.1-latest

6.0.8.0 Linux:

::

   sudo docker run --rm --privileged --net host \
       -v /dev/bus/usb:/dev/bus/usb \
       -v /tmp:/drive_flashing \
       -it nvcr.io/{MY_NGC_ORG}/driveos-pdk/drive-agx-orin-linux-aarch64-pdk-build-x86:6.0.8.0-0003

Inside of container, flash with flash.py:

::

   cd /drive
   ./flash.py <aurix> <board>

- ``<board>`` - target board base name: 'p3710' or 'p3663'.
- ``<aurix>`` - Aurix serial port, for example: `/dev/ttyACM1`, `/dev/ttyUSB1`.

Examples:

Firespray p3710:

::

   ./flash.py /dev/ttyACM1 p3710

Drive Orin p3663:

::

   ./flash.py /dev/ttyUSB1 p3663

List the available EMMC and UFS partitions:

::

   df -h

Format a power-safe file system partition, and mount it, example for ``vblk_ufs40``:

::

   mkqnx6fs /dev/vblk_ufs40 -q
   mount -o rw /dev/vblk_ufs40 /


   # df -h
   /dev/vblk_ufs40             116G      7.5G      108G       7%  /
   ifs                          16M       16M         0     100%  /
   ifs                          52M       52M         0     100%  /
   ...

Note:
	For more information about DRIVE OS installation, see the following link: NVIDIA DRIVE OS Documentation  (useful pages: **DRIVE OS Linux Installation Guide**, **DRIVE OS QNX Installation Guide**).

**Create XHV Directory**

Inside of container, examples for p3710, QNX/Linux:

QNX:

::

   cd /drive_flashing
   mkdir -p xhv/hypervisor/configs/t234ref-release/pct/qnx xhv/schemas
   cp -rv /drive/drive-foundation/virtualization/hypervisor/t23x/configs/t234ref-release/pct/p3710-10-a03/qnx/pct.json ./xhv/hypervisor/configs/t234ref-release/pct/qnx/
   cp -rv /drive/drive-foundation/schemas/event ./xhv/schemas/

Linux:

::

   cd /drive_flashing
   mkdir -p xhv/hypervisor/configs/t234ref-release/pct/linux xhv/schemas
   cp -rv /drive/drive-foundation/virtualization/hypervisor/t23x/configs/t234ref-release/pct/p3710-10-a03/linux/pct.json ./xhv/hypervisor/configs/t234ref-release/pct/linux/
   cp -rv /drive/drive-foundation/schemas/event ./xhv/schemas/

Example of XHV directory (Linux):


   xhv/
   ├── hypervisor
   │             └── configs
   │                 └── t234ref-release
   │                     └── pct
   │                         └── linux
   │                             └── pct.json
   └── schemas
       └── event
           ├── audioserver_events.json
           ├── bpmp_events.json
           ├── cem_events.json
           ├── hv_events.json
           ├── i2c_events.json
           ├── Makefile.gen-event-headers.tmk
           ├── monitor_events.json
           ├── se_events.json
           ├── sysmgr_events.json
           └── vsc_events.json

Copy XHV directory to target:


   scp -r xhv <user>@<target-IP>

eventlib_dump tool (QNX/Linux):

::

   cp -rv /drive/drive-qnx/nvidia-bsp/aarch64le/sbin/eventlib_dump /drive_flashing/
   cp -rv /drive/drive-linux/filesystem/contents/bin/eventlib_dump /drive_flashing/

**Specific Command Line Options**

   :name: table_xhvcli_table
   :class: table-compact   

   +-----------------------------------+---------------------------------------+--------------+-------------------------------------------------------------+
   | Option                            | Possible Parameters                   | Default      | Switch Description                                          |
   +===================================+=======================================+==============+=============================================================+
   +-----------------------------------+---------------------------------------+--------------+-------------------------------------------------------------+
   | ``--sample``                      | process-tree, system-wide,            | process-tree | Select 'xhv' or 'xhv-system-wide' to enable                 |
   |                                   | xhv, xhv-system-wide, none            |              | Cross-Hypervisor (XHV) sampling, requires root privileges.  |
   +-----------------------------------+---------------------------------------+--------------+-------------------------------------------------------------+
   | ``--xhv-vm-symbols``              | < filepath kernel_symbols.json >      | none         | XHV sampling config (optional, for kernel symbols).         |
   +-----------------------------------+---------------------------------------+--------------+-------------------------------------------------------------+
   | ``--xhv-trace``                   | < filepath pct.json >                 | none         | Collect hypervisor trace.                                   |
   +-----------------------------------+---------------------------------------+--------------+-------------------------------------------------------------+
   | ``--xhv-trace-events``            | all, none, core, sched,               | all          | HV trace events.                                            |
   |                                   | irq, trap                             |              |                                                             |
   +-----------------------------------+---------------------------------------+--------------+-------------------------------------------------------------+

Examples:

::

   nsys profile --sample=xhv --trace=nvtx,osrt,cuda --xhv-vm-symbols=/root/kernel_symbols.json --xhv-trace=/root/xhv/hypervisor/configs/p3710-10-a01/pct/qnx/pct.json --xhv-trace-events=none sleep 5
   nsys profile --sample=xhv-system-wide --xhv-vm-symbols=/root/kernel_symbols.json --xhv-trace=/root/xhv/hypervisor/configs/p3710-10-a01/pct/qnx/pct.json --xhv-trace-events=none sleep 5

Example screenshot:

   :alt: VMProfiler screenshot
   :class: image

**Config File (for kernel symbols)**

Examples:

QNX, ``kernel_symbols.json`` file:


   {
       "guest_cfg": [
           {
               "guest_id": 0,
               "guest_name": "Guest VM 0",
               "symbols": "/root/symbols/procnto-smp-instr-safety.guest_vm.bin.sym"
           },
           {
               "guest_id": 1,
               "guest_name": "Update service",
               "symbols": "/root/symbols/procnto-smp-instr-safety.update_vm.bin.sym"
           },
           {
               "guest_id": 2,
               "guest_name": "Resource Manager Server"
           },
           {
               "guest_id": 3,
               "guest_name": "Storage Server"
           },
           {
               "guest_id": 4,
               "guest_name": "Ethernet Server"
           },
           {
               "guest_id": 5,
               "guest_name": "Debug Server"
           }
       ],
       "symbol_files": {
           "Sidekick": "/root/symbols/sidekick.unstripped"
       }
   }

Linux, ``kernel_symbols.json`` file:


   {
       "guest_cfg": [
           {
               "guest_id": 0,
               "guest_name": "Guest VM 0",
               "symbols": "/home/<user>/vmlinux"
           },
           {
               "guest_id": 1,
               "guest_name": "Update service"
           }
       ],
       "symbol_files": {
       }
   }

**Symbol Files**

The list of directories with symbol files:

- CLI: ``DbgFileSearchPath`` config option, for example:
  ``DbgFileSearchPath="/lib:/root/symbols"`` - list of directories with symbol/debug files.
  On Linux, the default path is ``/usr/lib/debug``.
  On QNX, there is no default path.

  Example:


     NSYS_CONFIG_DIRECTIVES='DbgFileSearchPath="/lib:/root/symbols"' nsys profile --sample=xhv  --xhv-vm-symbols=/root/kernel_symbols.json --xhv-trace=/root/xhv/hypervisor/configs/p3710-10-a01/pct/qnx/pct.json --xhv-trace-events=none sleep 5

- GUI: ``Symbol location`` button.

The search is non-recursive.

There are several ways of searching for symbol files - Nsight Systems tries them sequentially for each target file:

- Build-id debug files (CLI only)

  <symbol directory>/.build-id/… - directories with debug files (or links to debug files).

  Example:


     .build-id/
     ├── 00
          └── 6627b119cc2aee77e10e0535fc243fce8fe66e.debug
     ├── 01
          ├── 3e4007e3cb24359203fc02b63bb90f16db5b23.debug
          └── fb938bc0f029c41a8e1e88f01f88f75cf3a0d3.debug
     ...

- Debuglink files (CLI only)

  <symbol directory>/<symbol file> - both filename and CRC from debuglink section must be matched for the symbol file.

- File name and build-id (CLI/GUI)

  <symbol directory>/<symbol file> - by filename and build-id.


**XHV profiling from the GUI**

XHV options:

   :alt: VMProfiler GUI screenshot
   :class: image

Use this dialog to specify XHV parameters:

- ``Collect HV Trace`` - Enable XHV tracing.

- The location of ``pct.json`` file on the host. There is predefined hierarchy of XHV JSON files, for example:


   xhv/
   ├── hypervisor
   │             └── configs
   │                 └── t234ref-release
   │                     └── pct
   │                         └── linux
   │                             └── pct.json
   └── schemas
       └── event
           ...
           ├── hv_events.json
           ...

- ``Collect VM Profile`` - Enable XHV sampling, depends on ``Collect HV Trace``.

- ``Event mask`` - Select XHV trace events, this option can be specified as ``None``.

- The location of ``kernel_symbols.json`` file on the host. Note that this file contains target paths to the kernel symbol files (see examples above).

- ``Skip idle`` and ``Combine EL0`` checkboxes are deprecated.
