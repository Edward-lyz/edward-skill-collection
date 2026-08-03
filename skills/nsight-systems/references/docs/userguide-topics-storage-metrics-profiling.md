---
source_path: UserGuide/topics/storage-metrics-profiling.rst
title: Network Storage Profiling
---
# Network Storage Profiling

Nsight Systems can profile several major storage / remote storage protocols. It
also ships with the ``storage_util_map`` and ``file_access_sum`` recipes for
post-collection analysis. See
Post-Collection Analysis Guide<Post-Collection Analysis Guide>

Note:
   Storage metrics profiling requires additional kernel support and is tailored
   for HPC systems.
   
   

To activate this feature, use the Nsight Systems CLI ``--storage-metrics``
option, followed by a comma-separated list of the desired arguments.

**Available arguments:**

- ``--nfs-volumes={all | volume1[,volume2][,volume3..]}``: enable NFS storage
  profiling for the specified volume(s) (specify ``all`` to profile all volumes).
- ``--lustre-volumes={all | volume1[,volume2][,volume3..]}``: enable Lustre
  storage profiling for the specified volume(s) (specify ``all`` to profile all
  volumes).
- ``--lustre-llite-dir=<path>``: specifies the path of the llite directory
  mount. This is the ``/sys/kernel/debug/lustre/llite`` directory mount point
  (mandatory if Lustre profiling is enabled).
- ``--storage-devices={all | device1[,device2][,device3..]}``: enable storage
  profiling of the specified local storage or NVMe-oF device(s) (specify ``all``
  to profile all devices).
- ``--interval=<value>``: sampling interval in milliseconds. Valid range is
  1-60000 (default: 1).
- ``--cache-samples=<value>``: number of samples to cache before submitting
  the events. Valid range is 1-1000 (default: 100).


**Usage Examples**

   :alt: Multiple storage protocols report file (Timeline view)
   :class: image

In the report file, under 'Timeline view', the storage metrics can be viewed
in the **Mounts** section. Each row contains metrics for one volume or device,
with the storage type next to the volume / device name.
Expanding each row will show the collected metrics for that volume / device.

   :alt: Multiple storage protocols report file (Files)
   :class: image

The ``stdout`` and ``stderr`` log files for the storage metrics collection
process can be viewed under the 'Files' section, which may assist in debugging.

It is also possible to use combinations of these arguments to profile multiple
storage protocols at once. For example:


   ./nsys profile --storage-metrics --nfs-volumes=all,--lustre-volumes=all,--storage-devices=<device_name1>,<device_name2>,--lustre-llite-dir=<path_to_llite_directory> <target-application>

Note:
   There are two types of Read/Write metrics:

   Application-level Read/Write - Displays **quantities** of data read/written
   to the storage device **by applications** (in Bytes).

   Driver-level Read/Write - Displays **throughput** of data read/written to
   the storage device **by the driver** (in bytes/s).

   For example, when an application uses the "write" POSIX function to write
   10 MB of data into a file, the entire 10 MB will appear, in a single
   sampling point, at the Application-level Write counter.
   The same 10 MB of data may be spread across multiple Driver-level Write
   counter sampling points, since it may take a bit of time for the NFS driver
   to write 10 MB of data into the NFS storage server.


## NFS volumes counters

Example Nsight Systems command line for NFS storage profiling:


   ./nsys profile --storage-metrics --nfs-volumes=all <target-application>

   :alt: NFS storage report file with expanding counters
   :class: image


## Lustre volumes counters

Example Nsight Systems command line for Lustre storage profiling:


   ./nsys profile --storage-metrics --lustre-volumes=dtdata_test,--lustre-llite-dir=/mnt/lustre-stats/llite <target-application>

   :alt: Lustre storage report file with expanding counters
   :class: image

**Exposing Lustre driver counters to non-privileged users**

The Lustre driver exposes performance counters via virtual files residing under
``/sys/kernel/debug/lustre``. However, this path is not accessible to
non-privileged users.

To expose the Lustre counters to non-privileged users, a superuser should create
a mount point to ``/sys/kernel/debug/lustre``. For example:


    su - root
    mkdir /mnt/lustre-stats
    mount --bind /sys/kernel/debug/lustre /mnt/lustre-stats


The ``--lustre-llite-dir=`` command line argument should point to the ``llite``
directory under this mount point; this will enable Nsight Systems to read the
Lustre counters.
For example: ``--lustre-llite-dir=/mnt/lustre-stats/llite``


## Local and NVMe-oF volumes counters

Example Nsight Systems command line for local storage and NVMe-oF device profiling:


   ./nsys profile --storage-metrics --storage-devices=all <target-application>

   :alt: Local / NVMe-oF storage report file with expanding counters
   :class: image
