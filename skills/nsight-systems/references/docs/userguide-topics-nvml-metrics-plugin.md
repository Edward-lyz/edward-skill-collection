---
source_path: UserGuide/topics/nvml-metrics-plugin.rst
title: ## NVML power and temperature metrics
---
## NVML power and temperature metrics

Nsight Systems can now periodically sample power and temperature metrics from GPUs and plot them on
the timeline in the GUI.
These metrics are provided by the NVML API calls ``nvmlDeviceGetPowerUsage`` and
``nvmlDeviceGetTemperature`` respectively. The power metrics are provided in milliwatts (mW) and
the temperature in degrees Celcius (C).

To enable the power and temperature sampling add the following option to the |cli-name|
``profile`` or ``start`` commands:

::

  --enable nvml_metrics[,arg1[=value1],arg2[=value2], ...]


There are no spaces following ``nvml_metrics`` plugin name. It is followed by a
comma separated list of arguments or argument=value pairs. Arguments with spaces
should be enclosed in double quotes.

Supported arguments are:

  :name: table_nvmlpowertemp_table
  :class: table-compact

  +------------+-------------------+---------------------+--------------+-------------------------------------+
  | Short name | Long name         | Possible Parameters | Default      | Switch Description                  |
  +============+===================+=====================+==============+=====================================+
  | ``-i``     | ``--interval``    | integer             | 100          | Sampling interval in milliseconds   |
  +------------+-------------------+---------------------+--------------+-------------------------------------+
  | ``-h``     | ``--help``        |                     |              | Print help message                  |
  +------------+-------------------+---------------------+--------------+-------------------------------------+
  | ``-g``     | ``--gpu-devices`` | all, cuda-visible,  | cuda-visible | Set the GPUs to be sampled.         |
  |            |                   | comma-separated GPU |              | `cuda-visible` will sample the GPUs |
  |            |                   | IDs list            |              | set with `CUDA_VISIBLE_DEVICES`. An |
  |            |                   |                     |              | empty `CUDA_VISIBLE_DEVICES` will   |
  |            |                   |                     |              | result in all GPUs being sampled.   |
  |            |                   |                     |              | `all` and a GPU IDs list will       |
  |            |                   |                     |              | precede `CUDA_VISIBLE_DEVICES`.     |
  +------------+-------------------+---------------------+--------------+-------------------------------------+

**Usage Examples**

-  ``nsys profile --enable nvml_metrics ...``
    Sample power and temperature on all available GPUs every 100ms.
-  ``nsys profile --enable nvml_metrics,-i10``
    Sample power and temperature on all available GPUs every 10ms.

For general information on Nsight Systems plugins please refer to Nsight Systems Plugins
system.
