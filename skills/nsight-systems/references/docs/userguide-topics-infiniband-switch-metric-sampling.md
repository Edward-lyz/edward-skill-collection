---
source_path: UserGuide/topics/infiniband-switch-metric-sampling.rst
title: ## Network Switch Profiling
---
## Network Switch Profiling


#### InfiniBand Switch Metric Sampling

NVIDIA Quantum InfiniBand switches offer high-bandwidth, low-latency
communication. Viewing switch metrics, on Nsight Systems timeline, enables
developers to better understand their application’s network usage. Developers
can use this information to optimize the application’s performance.

**Limitations/Requirements**

IB switch metric sampling supports all NVIDIA Quantum switches. The user needs
to have permission to query the InfiniBand switch metrics.

To check if the current user has permissions to query the InfiniBand switch
metrics, check that the user have permission to access ``/dev/infiniband/umad*``

To give user permissions to query InfiniBand switch metrics on RedHat systems,
follow the directions at `RedHat Solutions
<https://access.redhat.com/solutions/5929621>`__.

To collect InfiniBand switch performance metric, using Nsight Systems CLI, add
the ``--ib-switch-metrics-devices`` command line switch, followed by a comma
separated list of InfiniBand switch GUIDs. For example:

::

         nsys profile --ib-switch-metrics-devices=<IB switch GUID> my_app


To get a list of InfiniBand switches, reachable by a given NIC, use:
::

   sudo ibswitches -C <nic name>

   :alt: InfiniBand Switch performance metrics sampling screenshot
   :class: image

**Available Metrics**

-  **Bytes sent** - Number of bytes sent through all switch ports
-  **Bytes received** - Number of bytes received by all switch ports
-  **Send waits** - The number of ticks during which switch ports, selected by
     PortSelect, had data to transmit but no data was sent during the entire
     tick (either because of insufficient credits or of lack of arbitration)
-  **Average sent packet size** - Average sent InfiniBand packet size
-  **Average received packet size** - Average received InfiniBand packet size
