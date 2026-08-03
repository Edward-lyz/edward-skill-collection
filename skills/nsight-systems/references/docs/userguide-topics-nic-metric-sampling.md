---
source_path: UserGuide/topics/nic-metric-sampling.rst
title: ## Network Interface Controller (NIC) Profiling
---
## Network Interface Controller (NIC) Profiling


#### NVIDIA NIC Metric Sampling

**Overview**

NVIDIA ConnectX smart network interface cards (smart NICs) offer advanced hardware offloads and
accelerations for network operations. Viewing smart NICs metrics, on Nsight Systems timeline,
enables developers to better understand their application’s network usage. Developers can use this
information to optimize the application’s performance.

**Limitations/Requirements**

-  NIC metric sampling supports NVIDIA ConnectX boards starting with ConnectX 5
-  NIC metric sampling is supported on Linux x86_64 and Arm Server (SBSA) machines only, having
   minimum Linux kernel 4.12 and minimum MLNX_OFED 4.1. You can download the latest OFED driver
   through the DOCA-Host package as doca-ofed at NVIDIA DOCA Downloads .
   For archived versions of the OFED driver you can visit
   MLNX_OFED Download Center .
   If collecting NIC metrics within a container, make sure that the container has access to the
   driver on the host machine. To check manually if OFED is installed and get its version you can
   run:

   -  ``/usr/bin/ofed_info``
   -  ``cat /sys/module/"$(cat /proc/modules | grep -o -E "^mlx._core")"/version``

For the high frequency metrics, the following requirements must be met:

-  The NICs must be ConnectX-7, BlueField 3 or newer.
-  The NICs must have firmware XY.43.1000 or newer.
-  The DOCA telemetry (libdoca_telemetry.so.2) and common (libdoca_common.so.2) libraries must be
   installed. The libraries can be installed through DOCA SDK 2.9 or newer.
-  All NICs on the target machine must have the same type of clock, Real Time Clock (RTC) or Free
   Running Clock (FRC). The clock can be set through the NIC's firmware.
-  If collecting with the ``--nic-metrics=hf`` option additionally:

   -  The mlx5_fwctl driver module must be loaded.
   -  The user must have elevated privileges.

-  If collecting through the DOCA Telemetry Service API (DTS) with the ``--nic-metrics=hf-via-dts``
   option additionally:

   -  DTS must already be running with ``enable-http-api=true`` on the target system.
   -  The default DTS HTTP port is 9117 and can be overridden with ``--dts-api-port``.
   -  The DTS server has version 1.26.0 or newer. DTS server 1.26.0 is released with DOCA SDK 3.5.0.

To check if the target system meets the requirements for NIC metrics collection you can run ``nsys status --network``.

**Collecting NIC Metrics Using the Command Line**

To collect NIC performance metrics, using Nsight Systems CLI, add the ``--nic-metrics`` command line switch:

::

   nsys profile --nic-metrics=lf my_app

To collect high frequency NIC metrics through the DOCA Telemetry Service API:

::

   nsys profile --nic-metrics=hf-via-dts --dts-api-port=9117 my_app

   :alt: NIC metric sampling screenshot
   :class: image

Note:
   The high frequency option, ``hf``, collects samples at a higher frequency compared to the ``lf``
   option. ``--nic-metrics=hf`` will not collect counters for RoCE, IPoIB traffic and the Send
   waits metric. The ``hf-via-dts`` option also collects high frequency NIC metrics, via the DOCA
   Telemetry Service API.

**Available Metrics**

-  **Bytes sent** - Number of bytes sent through the NIC port.
-  **Bytes received** - Number of bytes received by the NIC port.
-  **Average sent packet size** - Average byte size of packets sent through the NIC port.
-  **Average received packet size** - Average byte size of packets received by the NIC port.
-  **CNPs sent** - Number of congestion notification packets sent by the NIC.
-  **CNPs received** - Number of congestion notification packets received and handled by the NIC.
-  **Send waits** - The number of ticks during which the port had data to transmit but no data was sent
   during the entire tick (either because of insufficient credits or because of lack of arbitration)

Note:
   The counters for RoCE traffic reflect the sum of unicast and multicast traffic.

**Usage Examples**

-  The ``Bytes sent/sec`` and the ``Bytes received/sec`` metrics enables identifying idle and busy NIC times.

   -  Developers may shift network operations from busy to idle times to reduce network congestion and latency.
   -  Developers can use idle NIC times to send additional data without reducing application performance.

-  CNPs (congestion notification packets) received/sent and Send waits metrics may explain network
   latencies. A developer seeing the time periods when the network was congested may rewrite his
   algorithm to avoid the observed congestions.
