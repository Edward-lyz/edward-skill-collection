---
source_path: UserGuide/topics/commands.rst
title: #### Commands
---
#### Commands

**Info**

To find out report's start and end time use **info** command.

Usage:

::

   ImportNvtxt --cmd info -i [--input] arg

Example:

::

   ImportNvtxt info Report.nsys-rep
   Analysis start (ns) 83501026500000
   Analysis end (ns)   83506375000000

**Create**

You can create a report file using existing NVTXT with **create** command.

Usage:

::

   ImportNvtxt --cmd create -n [--nvtxt] arg -o [--output] arg [-m [--mode] mode_name mode_args]

Available modes are:

-  **lerp** — insert with linear interpolation.

-  **lin** — insert with linear equation.

Usage for **lerp** mode is:

::

   --mode lerp --ns_a arg --ns_b arg [--nvtxt_a arg --nvtxt_b arg]

with:

-  ``ns_a`` — a nanoseconds value.

-  ``ns_b`` — a nanoseconds value (greater than ``ns_a``).

-  ``nvtxt_a`` — an nvtxt file's time unit value corresponding to ``ns_a`` nanoseconds.

-  ``nvtxt_b`` — an nvtxt file's time unit value corresponding to ``ns_b`` nanoseconds.

If ``nvtxt_a`` and ``nvtxt_b`` are not specified, they are respectively set to nvtxt file's minimum and maximum time value.

Usage for **lin** mode is:

::

   --mode lin --ns_a arg --freq arg [--nvtxt_a arg]

with:

-  ``ns_a`` — a nanoseconds value.

-  ``freq`` — the nvtxt file's timer frequency.

-  ``nvtxt_a`` — an nvtxt file's time unit value corresponding to ``ns_a`` nanoseconds.

If ``nvtxt_a`` is not specified, it is set to nvtxt file's minimum time value.

**Examples:**

::

   ImportNvtxt --cmd create -n Sample.nvtxt -o Report.nsys-rep

The output will be a new generated report file which can be opened and viewed by Nsight Systems.

**Merge**

To merge NVTXT file with an existing report file use **merge** command.

Usage:

::

   ImportNvtxt --cmd merge -i [--input] arg -n [--nvtxt] arg -o [--output] arg [-m [--mode] mode_name mode_args]

Available modes are:

-  **lerp** — insert with linear interpolation.

-  **lin** — insert with linear equation.

Usage for **lerp** mode is:

::

   --mode lerp --ns_a arg --ns_b arg [--nvtxt_a arg --nvtxt_b arg]

with:

-  ``ns_a`` — a nanoseconds value.

-  ``ns_b`` — a nanoseconds value (greater than ``ns_a``).

-  ``nvtxt_a`` — an nvtxt file's time unit value corresponding to ``ns_a`` nanoseconds.

-  ``nvtxt_b`` — an nvtxt file's time unit value corresponding to ``ns_b`` nanoseconds.

If ``nvtxt_a`` and ``nvtxt_b`` are not specified, they are respectively set to nvtxt file's minimum and maximum time value.

Usage for **lin** mode is:

::

   --mode lin  --ns_a arg --freq arg [--nvtxt_a arg]

with:

-  ``ns_a`` — a nanoseconds value.

-  ``freq`` — the nvtxt file's timer frequency.

-  ``nvtxt_a`` — an nvtxt file's time unit value corresponding to ``ns_a`` nanoseconds.

If ``nvtxt_a`` is not specified, it is set to nvtxt file's minimum time value.

Time values in ``<filename.nvtxt>`` are assumed to be nanoseconds if no mode specified.

Example

::

   ImportNvtxt --cmd merge -i Report.nsys-rep -n Sample.nvtxt -o NewReport.nsys-rep
