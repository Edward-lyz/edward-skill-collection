---
source_path: UserGuide/topics/pytorch-autograd-nvtx.rst
title: ## PyTorch Profiling
---
## PyTorch Profiling

Nsight Systems for Arm server (SBSA) platforms, x86 Linux and Windows targets, is capable of automatically annotating common PyTorch operations with execution time ranges.

The Python source code does not require any changes. This feature requires CPython interpreter, release 3.8 or later.

To enable PyTorch autograd nvtx , run Nsight Systems from the CLI using the ``--pytorch`` option:

Set ``--pytorch=autograd-nvtx`` for enabling ``torch.autograd.profiler.emit_nvtx(record_shapes=False)`` or ``--pytorch=autograd-shapes-nvtx`` for enabling ``torch.autograd.profiler.emit_nvtx(record_shapes=True)`` (implies ``--trace=nvtx``).

Set ``--pytorch=functions-trace`` for automatically annotating
PyTorch operations like forward operations ,
backward operations ,
step operations , etc.
with execution time ranges.

Set ``--pytorch=functions-trace-shapes`` to attach additional data to each annotated range,
such as tensor shapes, training parameters, etc.
``functions-trace`` and ``functions-trace-shapes`` are mutually exclusive.

Both ``--pytorch=functions-trace`` and ``--pytorch=functions-trace-shapes`` imply ``--python-functions-trace=<nsys_install_dir>/<target-arch>/PythonFunctionsTrace/pytorch.json``.

``autograd-nvtx`` and ``autograd-shapes-nvtx`` options can be combined with ``functions-trace`` or ``functions-trace-shapes`` by adding them separated by a comma.

When profiling a vLLM  application,
the ``functions-trace`` option also automatically annotates vLLM-specific methods
such as ``AsyncLLM.generate()``, ``Worker.execute_model()``, and ``Worker.sample_tokens()``
under a dedicated *vLLM* NVTX domain. These annotations include correlated request IDs
for tracking individual requests across the inference pipeline.

Example screenshots:

   :alt: PyTorch Autograd NVTX
   :class: image

   :alt: PyTorch Functions Trace with vLLM
   :class: image
