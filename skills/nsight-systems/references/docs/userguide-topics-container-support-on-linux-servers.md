---
source_path: UserGuide/topics/container-support-on-linux-servers.rst
title: Container, Scheduler, and Cloud Support
---
# Container, Scheduler, and Cloud Support

## Collecting Data Within a Container

While examples in this section use Docker container semantics, other containers
work much the same.

The following information assumes the reader is knowledgeable regarding Docker
containers. For further information about Docker use in general, see the
Docker documentation .

We strongly recommend using the CLI to profile in a container. Best container
practice is to split services across containers when they do not require
colocation. The Nsight Systems GUI is not needed to profile and brings in many
dependencies, so the CLI is recommended. If you wish, the GUI can be in a
separate side-car container you use to view your report. All you need is
a shared folder between the containers. See section on GUI VNC Container
for more information.

#### Enable Docker Collection

When starting the Docker to perform a Nsight Systems collection, additional
steps are required to enable the ``perf_event_open`` system call. This is
required in order to utilize the Linux kernel’s perf subsystem which provides
sampling information to Nsight Systems.

There are three ways to enable the ``perf_event_open`` syscall. You can enable
it by using the ``--privileged=true`` switch, adding ``--cap-add=SYS_ADMIN``
switch to your docker run command file, or you can enable it by setting the
seccomp security profile if your system meets the requirements.

Secure computing mode (seccomp) is a feature of the Linux kernel that can be
used to restrict an application's access. This feature is available only if
the kernel is enabled with seccomp support. To check for seccomp support:

::

   $ grep CONFIG_SECCOMP= /boot/config-$(uname -r)

The official Docker documentation says:

::

   "Seccomp profiles require seccomp 2.2.1 which is not available on Ubuntu
   14.04, Debian Wheezy, or Debian Jessie. To use seccomp on these distributions,
   you must download the latest static Linux binaries (rather than packages)." 

Download the default seccomp profile file, ``default.json``, relevant to your Docker
version. If ``perf_event_open`` is already listed in the file as guarded by
``CAP_SYS_ADMIN``, then remove the ``perf_event_open`` line. Add the following
lines under "syscalls" and save the resulting file as ``default_with_perf.json``.

::

   {
       "name": "perf_event_open",
       "action": "SCMP_ACT_ALLOW",
       "args": []
   },

Then you will be able to use the following switch when starting the Docker to
apply the new seccomp profile.

::

   --security-opt seccomp=default_with_perf.json

#### Launch Docker Collection

Here is an example command that has been used to launch a Docker for testing
with Nsight Systems:

::

   sudo nvidia-docker run --network=host --security-opt seccomp=default_with_perf.json --rm -ti caffe-demo2 bash

There is a known issue where Docker collections terminate prematurely with older
versions of the driver and the CUDA Toolkit. If collection is ending
unexpectedly, please update to the latest versions.
														
After the Docker has been started, use the Nsight Systems CLI to launch a
collection within the Docker. The resulting file can be imported into the
Nsight Systems host like any other CLI result.


## Profiling Services in the Cloud

Nsight Cloud is a set of utilities designed to simplify the process of launching
and controlling NVIDIA tools in cloud environments. For more information and 
download see:
NVIDIA Nsight Cloud .


#### Profiling Services Launched via Kubernetes (Nsight Operator)

Nsight Systems now can provide profiling via sidecar injection without need to
modify your containers or k8/helm specs.

      :alt: workflow graph for nsys profiling Kubernetes
      :class: image

Once the sidecar is enabled, the data collected data can be filtered by namespace or
pod using Kubernetes labels, or within a container process by using
command-line regex.

This functionality is compatible with various cloud service provider's in-house
managed Kubernetes variants including AKS, EKS, GKE, and OKE.

Documentation and download for this sidecar is available at
NGC Nsight Operator .


#### Streaming GUI (Nsight Streamer)

A self-hosted NVIDIA Nsight Systems GUI running inside a Docker container
enables remote access through a web browser. This configuration is particularly
useful for analyzing data on remote servers or clusters.

For more information and instructions on running the container, visit:
`Nsight Streamer for Nsight Systems on
NGC <https://catalog.ngc.nvidia.com/orgs/nvidia/teams/devtools/containers/nsight-streamer-nsys>`__.
