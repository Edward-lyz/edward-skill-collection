---
source_path: UserGuide/topics/gpu-metrics-cli.rst
title: #### Launching GPU Metrics from the CLI
---
#### Launching GPU Metrics from the CLI

GPU Metrics feature is controlled with 3 CLI switches:

-  ``--gpu-metrics-devices=[none|all|cuda-visible|(<index>[,...])]`` selects GPUs to
   sample (default is none).
-  ``--gpu-metrics-set=[<alias>|file:<file name>][,...]``
   selects the metric set per GPU (default is the 1st suitable from the list). A single
   value is assigned to all selected GPUs; a comma-separated list assigns one metric set
   per GPU, in the same order as ``--gpu-metrics-devices``.
-  ``--gpu-metrics-frequency=[10..200000][,...]`` selects sampling
   frequency in Hz per GPU (default is 10000). A single value is assigned to all
   selected GPUs; a comma-separated list assigns one frequency per GPU,
   in the same order as ``--gpu-metrics-devices``.

To profile with default options and sample GPU Metrics on GPU 1:
::

   # Must have elevated permissions (see https://developer.nvidia.com/ERR_NVGPUCTRPERM) or be root (Linux) or Administrator (Windows)
   $ nsys profile --gpu-metrics-devices=1 ./my-app

To list available GPUs, use:
::

   $ nsys profile --gpu-metrics-devices=help
   Possible --gpu-metrics-devices values are:
       1: Turing TU104 | GeForce RTX 2070 SUPER PCI[0000:65:00.0]
       all: Select all supported GPUs
       cuda-visible: Select GPUs that match CUDA_VISIBLE_DEVICES
       none: Disable GPU Metrics [Default]
   Some GPUs are not supported:
       0: Volta GV100 | Quadro GV100 PCI[0000:17:00.0]
   See the user guide: https://docs.nvidia.com/nsight-systems/UserGuide/index.html#gpu-metrics

By default, the first **metric set** which supports all selected GPUs is used.
You can manually select another metric set from the list, or specify a different
metric set per GPU using a comma-separated list (one value per GPU, in the same
order as ``--gpu-metrics-devices``). To see metric sets available for the
selected GPUs, use:
::

   $ nsys profile --gpu-metrics-devices=all --gpu-metrics-set=help
   Possible --gpu-metrics-set values are:
       tu10x        : General Metrics for NVIDIA TU10x (any frequency)
       tu10x-gfxt   : Graphics Throughput Metrics for NVIDIA TU10x (frequency >= 10kHz)
       file:<file name> : use metric set from a given file

To assign the same metric set to all selected GPUs:
::

   --gpu-metrics-devices=0,1 --gpu-metrics-set=tu10x

To assign different metric sets per GPU (GPU 0 with ``tu10x``, GPU 1 with ``tu10x-gfxt``):
::

   --gpu-metrics-devices=0,1 --gpu-metrics-set=tu10x,tu10x-gfxt

By default, **sampling frequency** is set to 10 kHz. You can set it globally
from 10 Hz to 200 kHz, or specify a different rate per selected GPU using a
comma-separated list (one value per GPU, in the same order as
``--gpu-metrics-devices``). Abbreviated suffixes ``k`` and ``M`` are accepted.

To set the same rate for all selected GPUs:
::

   --gpu-metrics-frequency=50k

To set different rates per GPU (GPU 0 at 50 kHz, GPU 1 at 4 kHz):
::

   --gpu-metrics-devices=0,1 --gpu-metrics-frequency=50k,4k
