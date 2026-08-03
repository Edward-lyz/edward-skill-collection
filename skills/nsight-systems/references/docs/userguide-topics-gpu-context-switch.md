---
source_path: UserGuide/topics/gpu-context-switch.rst
title: ## GPU Context Switch
---
## GPU Context Switch


|Product-name| provides the ability to trace GPU context switches.

To enable trace, run from the CLI using the ``--gpuctxsw`` option

From the GUI:

   :alt: GUI GPU context switch trace control
   :class: image 

Specifically, the behavior is as follows:

When collecting GPU context switch data as root, you will get records about
contexts from all processes. The records have valid context IDs and process IDs,
and have full-precision timestamps.

When collecting GPU context switch data as a normal user, you will still get
records about contexts from all processes. For processes running as your user,
the records have valid context ID and process IDs, and full-precision timestamps.
For processes running as a different user, the records have context ID = 0 and
process ID = 0, and reduced-precision timestamps (which are still guaranteed to
be in the correct order).

When collecting GPU context switch data in a virtual machine using vGPU, the
above rules apply to records relating to your VM.  No records are collected for
contexts running on other VMs, so the timeline may show gaps when the vGPU is
switched to another VM's context(s). We do not currently support collecting GPU
context switch data on a host system where vGPUs are in use by VMs.

   :alt: screenshot of gpu context switch information
   :class: image
