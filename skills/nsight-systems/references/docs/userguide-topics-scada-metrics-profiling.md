---
source_path: UserGuide/topics/scada-metrics-profiling.rst
title: ## SCADA Metrics Profiling
---
## SCADA Metrics Profiling

NVIDIA SCADA (SCaled Accelerated Data Access) is a storage I/O
architecture where GPUs directly initiate and control storage operations,
removing CPU involvement from both the control path and the data path.
It is optimized for AI workloads that require high-throughput,
fine-grained accesses (< 4 KB) from thousands of parallel GPU threads
to NVMe storage. A SCADA deployment consists of a client library on the
GPU side and a server daemon that manages the NVMe drives.

Nsight Systems can periodically sample performance counters and histograms
from a running SCADA server and display them on the timeline in the GUI.
This enables developers to monitor SCADA server activity and correlate it
with GPU and CPU events.

SCADA metrics profiling is supported on Linux x64 and SBSA operating systems.


#### Enabling SCADA Metrics Collection

To enable SCADA metrics collection, add the following option to the
|cli-name| ``profile`` or ``start`` commands:

::

  --enable scada_metrics[,--sampling-frequency=<value>,--socket-path=<path>]


There are no spaces following the ``scada_metrics`` plugin name. It is
followed by a comma-separated list of arguments or argument=value pairs.

Note:
   A SCADA server must be running on the target system before starting
   the profiling session. The plugin communicates with the server through
   a Unix Domain Socket at the path provided to ``--socket-path`` cli option
   (default path is ``/tmp/scada_profiler_socket``). If the server
   is not running, the plugin will report an error and exit.

Supported arguments are:

  :name: table_scada_metrics_args
  :class: table-compact

  +----------------------------+-------------------+------------------------------+-----------------------------------------------------------+
  | Name                       | Possible Values   | Default                      | Description                                               |
  +============================+===================+==============================+===========================================================+
  | ``-s`` /                   | 1 -- 1000         | 1000                         | Sampling frequency in Hz. Controls how often the plugin   |
  | ``--sampling-frequency``   |                   |                              | requests a new metrics sample from the SCADA server.      |
  +----------------------------+-------------------+------------------------------+-----------------------------------------------------------+
  | ``-p`` /                   | Any non-empty     | /tmp/scada_profiler_socket   | Filesystem path to the Unix Domain Socket used for        |
  | ``--socket-path``          | string            |                              | communication with the SCADA server.                      |
  +----------------------------+-------------------+------------------------------+-----------------------------------------------------------+

**Usage Examples**

-  ``nsys profile --enable scada_metrics <target-application>``
    Collect SCADA metrics at the default sampling frequency of 1000 Hz, and default socket path of ``/tmp/scada_profiler_socket``.
-  ``nsys profile --enable scada_metrics,--sampling-frequency=10 <target-application>``
    Collect SCADA metrics at 10 Hz (one sample every 100 ms).
-  ``nsys profile --enable scada_metrics,-s,100,-p,/path/to/server/socket <target-application>``
    Collect SCADA metrics at 100 Hz using custom socket path of ``/path/to/server/socket``.

For general information on Nsight Systems plugins please refer to
Nsight Systems Plugins system.


#### Viewing SCADA Metrics in the Report

In the report file, under **Timeline view**, SCADA metrics appear in the
**SCADA Metrics** section. Each counter is plotted as a time-series graph
and each histogram is displayed with its bucketed distribution over time.

   :alt: SCADA metrics in the Timeline view
   :class: image

The ``stdout`` and ``stderr`` log files for the SCADA metrics collection
process can be viewed under the **Files** section, which may assist in
debugging connectivity or sampling issues.

   :alt: SCADA metrics log files
   :class: image


#### Available Metrics

The specific metrics collected by the plugin are determined entirely by
the SCADA server. At the start of each profiling session, the plugin
fetches a **metrics schema** from the server that describes the available
metrics — their names, units, and histogram bin definitions. Different
SCADA server configurations may expose different sets of metrics.

There are two types of metrics:

- **Counters** — Scalar values sampled at each collection interval
  (e.g. total received buffers, average latency). Each counter is
  plotted as a time-series graph on the timeline.
- **Histograms** — Distribution metrics with predefined bins
  (e.g. latency distribution, commands-per-buffer distribution). Each
  histogram is displayed with its bucketed distribution over time.

The following screenshots show example metrics from a particular server
configuration:

**Counters**

   :alt: Example SCADA counters in the Timeline view
   :class: image

**Histograms**

   :alt: Example SCADA histograms in the Timeline view
   :class: image
