---
source_path: UserGuide/topics/import-nvtxt.rst
title: ## Import NVTXT
---
## Import NVTXT

**ImportNvtxt** is an utility which allows conversion of a
NVTXT  
file to a Nsight Systems report file (\*.nsys-rep) or to merge it with an
existing report file.

Note:
   NvtxtImport supports custom **TimeBase** values. Only the following values are supported:

-  **Manual** — timestamps are set using absolute values.

-  **Relative** — timestamps are set using relative values with regards to
   report file which is being merged with the NVTXT file.

-  **ClockMonotonicRaw** — timestamps values in the NVTXT file are considered to be
   gathered on the same target as the report file which is to be merged with
   NVTXT using ``clock_gettime(CLOCK_MONOTONIC_RAW, ...)`` call.

-  **CNTVCT** — timestamps values in the NVTXT file are considered to be gathered
    on the same target as the report file which is to be merged with NVTXT using
    CNTVCT values.

You can get usage info via the help message.

Print the help message:

::

   -h [ --help ]

Show information about the report file:

::

   --cmd info -i [--input] arg

Create the report file from an existing NVTXT file:

::

   --cmd create -n [--nvtxt] arg -o [--output] arg [-m [--mode] mode_name mode_args] [--target <Hw:Vm>] [--update_report_time]

Merge the NVTXT file to an existing report file:

::

   --cmd merge -i [--input] arg -n [--nvtxt] arg -o [--output] arg [-m [--mode] mode_name mode_args] [--target <Hw:Vm>] [--update_report_time]

Modes' descriptions:

-  lerp - Insert with linear interpolation

   ::

      --mode lerp --ns_a arg --ns_b arg [--nvtxt_a arg --nvtxt_b arg]

-  lin - insert with linear equation

   ::

      --mode lin  --ns_a arg --freq arg [--nvtxt_a arg]

Modes' parameters:

-  ``ns_a`` - a nanoseconds value

-  ``ns_b`` - a nanoseconds value (greater than ``ns_a``)

-  ``nvtxt_a`` - an nvtxt file's time unit value corresponding to ``ns_a`` nanoseconds

-  ``nvtxt_b`` - an nvtxt file's time unit value corresponding to ``ns_b`` nanoseconds

-  ``freq`` - the nvtxt file's timer frequency

-  ``--target <Hw:Vm>`` - specify target id, e.g. ``--target 0:1``

-  ``--update_report_time`` - prolong report's profiling session time while
    merging if needed. Without this option all events outside the profiling
    session time window will be skipped during merging.
