---
source_path: UserGuide/topics/timeline-hierarchy.rst
title: #### Timeline Hierarchy
---
#### Timeline Hierarchy

When reports are added to the same timeline Nsight Systems will automatically
line them up by timestamps as described above. If you want Nsight Systems to
also recognize matching process or hardware information, you will need to set
environment variables ``NSYS_SYSTEM_ID`` and ``NSYS_HW_ID`` as shown below at
the time of report collection (such as when using the "nsys profile ..." command).

When loading a pair of given report files into the same timeline, they will be
merged in one of the following configurations:

-  **Different hardware** — is used when reports are coming from different physical
   machines, and no hardware resources are shared in these reports. This mode
   is used when neither ``NSYS_HW_ID`` or ``NSYS_SYSTEM_ID`` is set and target
   hostnames are different or absent, and can be additionally signalled by
   specifying different ``NSYS_HW_ID`` values.

-  **Different systems, same hardware** — is used when reports are collected on
   different virtual machines (VMs) or containers on the same physical machine.
   To activate this mode, specify the same value of ``NSYS_HW_ID`` when
   collecting the reports.

-  **Same system** — is used when reports are collected within the same operating
   system (or container) environment. In this mode a process identifier (PID)
   100 will refer to the same process in both reports. To manually activate this
   mode, specify the same value of ``NSYS_SYSTEM_ID`` when collecting the
   reports. This mode is automatically selected when target hostnames are the
   same and neither ``NSYS_HW_ID`` or ``NSYS_SYSTEM_ID`` is provided.

The following diagrams demonstrate typical cases:

   :alt: TODO
   :class: image
