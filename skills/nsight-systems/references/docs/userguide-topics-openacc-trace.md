---
source_path: UserGuide/topics/openacc-trace.rst
title: OpenACC Trace
---
# OpenACC Trace

Nsight Systems for Linux x86_64 is capable of capturing information about
OpenACC execution in the profiled process.

OpenACC versions 2.0, 2.5, and 2.6 are supported when using PGI runtime version
15.7 or later. In order to differentiate constructs (see tooltip below), a PGI
runtime of 16.0 or later is required. Note that Nsight Systems does not support
the GCC implementation of OpenACC at this time.

Under the CPU rows in the timeline tree, each thread that uses OpenACC will show
OpenACC trace information. You can click on an OpenACC API call to see
correlation with the underlying CUDA API calls (highlighted in teal):

   :alt: OpenACC rows
   :class: image

If the OpenACC API results in GPU work, that will also be highlighted:

   :alt: OpenACC rows
   :class: image

Hovering over a particular OpenACC construct will bring up a tooltip with
details about that construct:

      :alt: OpenACC construct tooltip
      :class: image

To capture OpenACC information from the Nsight Systems GUI, select the
**Collect OpenACC trace** checkbox under **Collect CUDA trace** configurations.
Note that turning on OpenACC tracing will also turn on CUDA tracing.

      :alt: Configure CUDA trace
      :class: image

Note:
   If your application crashes before all collected OpenACC trace data has been copied out, some or all data might be lost and not present in the report.
