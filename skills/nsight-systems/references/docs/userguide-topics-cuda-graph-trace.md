---
source_path: UserGuide/topics/cuda-graph-trace.rst
title: ## CUDA Graph Trace
---
## CUDA Graph Trace

Nsight Systems is capable of capturing information about CUDA graphs in your
application at either the graph or node granularity. This can be set in the CLI
using the ``--cuda-graph-trace`` option, or in the GUI by setting the appropriate
drop-down.

      :alt: Configure CUDA graph trace
      :class: image

The CLI syntax is:


   --cuda-graph-trace=<granularity>[:<launch origin>][:<nvtx mode>]

The optional launch origin and NVTX projection mode modifiers can appear in any
order after the granularity.

When CUDA graph trace is set to ``graph``, the user sees each graph as one item
on the timeline:

      :alt: CUDA Graph trace at the graph level
      :class: image

When CUDA graph trace is set to ``node``, the user sees each graph as a set of
nodes on the timeline:

      :alt: CUDA Graph trace at the node level
      :class: image

Tracing CUDA graphs at the graph level rather than tracing the underlying nodes
results in significantly less overhead. This option requires CUDA driver version
11.7 or higher. If CUDA driver version 11.7 or higher is available, the default
granularity is ``graph``. Otherwise, the default granularity is ``node``.

Use the ``host-only`` launch origin to trace only CUDA graphs launched from host
code. Use ``host-and-device`` to trace CUDA graphs launched from both host code
and device code. For graph granularity, ``host-and-device`` requires CUDA driver
version 12.3 or higher. For node granularity, ``host-and-device`` requires
hardware trace with CUDA driver version 13.0 or higher, and ``--trace=cuda`` must
be enabled without ``--trace=cuda-sw``. Tracing graphs launched from device code
may cause significant runtime overhead.

If granularity is set to ``graph`` and CUDA driver version 12.3 or higher is
available, the default launch origin is ``host-and-device``. For ``node``, the
default launch origin is ``host-only`` unless hardware trace is enabled and CUDA
driver version 13.0 or higher is available.

Use ``nvtx-live`` to project NVTX ranges for CUDA graphs constructed while
profiling is active. This is the default NVTX projection mode and adds no
overhead.

Use ``nvtx-precapture`` to record CUDA API and NVTX events during graph
construction before profiling starts. This enables NVTX projection for graphs
built before collection begins, such as graphs built before a
``--capture-range=cudaProfilerApi`` collection starts. This mode is experimental,
adds overhead during graph construction, and increases memory usage. It requires
``node`` granularity, CUDA tracing with ``--trace=cuda`` or ``-t cuda``, and NVTX
tracing with ``--trace=nvtx`` or ``-t nvtx``.
