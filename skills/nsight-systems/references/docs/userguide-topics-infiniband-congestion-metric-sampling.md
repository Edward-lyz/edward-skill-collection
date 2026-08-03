---
source_path: UserGuide/topics/infiniband-congestion-metric-sampling.rst
title: #### InfiniBand Switch Congestion Events
---
#### InfiniBand Switch Congestion Events


### Overview

NVIDIA Quantum InfiniBand switches offer high-bandwidth, low-latency communication.

When a switch egress port is congested, packets wait in the egress port queue
before being sent out of the switch. This increases the latency of these
packets.

Nsight Systems Workstation Edition gives you the ability to view when switch egress ports are
congested on the Nsight Systems timeline. This enables developers to better
understand latencies that are caused by the application’s network usage.
Developers can use this information to optimize the application’s performance.


### Limitations/Requirements

IB switch congestion events support requires:

-  Quantum 2 switch or newer
-  Having firmware version 31.2012.1068 or higher
-  User need to have permission to send management datagrams

To get a list of InfiniBand switches, reachable by a given NIC, use:
``sudo ibswitches -C <nic name>``

To check if the current user has permissions to send management datagrams,
check that the user have permission to access ``/dev/infiniband/umad*``

To give user permissions to query InfiniBand switch congestion events on RedHat
systems, follow the directions at `RedHat Solutions
<https://access.redhat.com/solutions/5929621>`__.

### Using the Command Line

To collect InfiniBand switch congestion events, using Nsight Systems CLI, add
the following command line switches:

-  ``ib-switch-congestion-devices``
   This should be followed by a comma separated list of InfiniBand switch GUIDs,
   from which congestion events will be collected.

-  ``ib-switch-congestion-nic-device``
   This should be followed by the name of the NIC (HCA) through which InfiniBand
   switches will be accessed. The profiled InfiniBand switches should be reachable
   by this NIC.

-  ``ib-switch-congestion-percent``
   This defines the percent of InfiniBand switch congestion events to be collected.
   This option enables reducing the network bandwidth consumed by reporting
   congestion events. Values are in the [1,100] range.

-  ``ib-switch-congestion-threshold-high``
   This defines the high threshold for InfiniBand switch egress port queue size.
   When a packet enters an InfiniBand switch, its data is stored at an ingress port
   buffer. A pointer to the packet's data is inserted into the egress port's queue,
   from which the packet will be exiting the switch. At that point, the threshold
   given by this command switch is compared to the egress queue data size. If the
   queue data size exceeds the threshold, a congestion event is reported. The
   threshold is given in percent of the ingress port size. An egress port queue can
   point to data coming from multiple ingress port buffers, therefore the threshold
   can be bigger than 100%. Values are in the (1,1023] range

   :alt: infiniband congestion sampling screenshot
   :class: image
