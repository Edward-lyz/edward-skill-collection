---
source_path: UserGuide/topics/network-interface-plugin.rst
title: ## Network Interface Device Profiling
---
## Network Interface Device Profiling

Network Interface Devices (NIDs) are devices (usually ISP-owned) separating
public and private networks. Nsight Systems can now periodically sample
performance counters for network interface devices and plot them on the timeline
in the GUI.

To enable the network devices metrics add the following option to the |cli-name|
``profile`` or ``start`` commands:

::

  --enable network_interface[,arg1[=value1],arg2[=value2], ...]


There are no spaces following ``network_interface`` plugin name. It is followed by a
comma separated list of arguments or argument=value pairs. Arguments with spaces
should be enclosed in double quotes.

Supported arguments are:

  :name: table_netinterface_table
  :class: table-compact

  +------------+----------------+---------------------+-------------------------------------------+-----------------------------------+
  | Short name | Long name      | Possible Parameters | Default                                   | Switch Description                |
  +============+================+=====================+===========================================+===================================+
  | ``-i``     | ``--interval`` | integer             | 100000                                    | Sampling interval in microseconds |
  +------------+----------------+---------------------+-------------------------------------------+-----------------------------------+
  | ``-d``     | ``--devices``  | regular expression  | ".+" (and filtering for physical devices) | Device(s) to sample               |
  +------------+----------------+---------------------+-------------------------------------------+-----------------------------------+
  | ``-m``     | ``--metrics``  | regular expression  | ".*_bytes"                                | Metric(s) to sample               |
  +------------+----------------+---------------------+-------------------------------------------+-----------------------------------+
  | ``-h``     | ``--help``     |                     |                                           | Print help message                |
  +------------+----------------+---------------------+-------------------------------------------+-----------------------------------+

**Usage Examples**

-  ``nsys profile --enable network_interface ...``
    Sample bytes metrics for all physical network devices every 100ms.
-  ``nsys profile --enable network_interface,-dall ...``
    Sample bytes metrics for all network devices every 100ms.
-  ``nsys profile --enable network_interface,-i10000,-dall,-m".+"``
    Sample all metrics, for all network devices, every 10ms.

For general information on Nsight Systems plugins please refer to Nsight Systems Plugins
system.
