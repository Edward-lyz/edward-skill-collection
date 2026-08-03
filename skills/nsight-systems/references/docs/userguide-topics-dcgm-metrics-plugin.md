---
source_path: UserGuide/topics/dcgm-metrics-plugin.rst
title: ## DCGM
---
## DCGM

NVIDIA Data Center GPU Manager (DCGM) is a suite of tools for managing and
monitoring NVIDIA Datacenter GPUs in cluster environments. It includes active
health monitoring, comprehensive diagnostics, system alerts, and governance
policies including power and clock management. Infrastructure teams can use it
standalone and in addition easily integrate it into cluster management tools,
resource scheduling, and monitoring products from NVIDIA partners. For more 
information, see `DCGM Documentation
<https://docs.nvidia.com/datacenter/dcgm/latest/index.html>`__


Nsight Systems can now directly access metrics from DCGM and integrate them with
other data collected, displaying on the timeline or making available for further
analysis.


Supported arguments are:


   :name: table_dcgm_table
   :class: table-compact table-expandable


   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | Option                        | Available Parameters  | Switch Description                                                                                      |
   |                               | (default in bold)     |                                                                                                         |
   +===============================+=======================+=========================================================================================================+
   | ``--cpu``                     | all, help, dcgm:<ID>  | Indicate which CPU(s) you are interested in or all. If you want to build a combination of CPUs, you can |
   |                               | dcgm:<ID1-ID2>        | build a comma-separated combo like ``dcgm:0,dcgm:2-4``. Help will give a list of available CPUs.        |                                                   
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--gpu``                     | all, cuda-visible,    | Indicate which GPUs you are interested in, or all. If you want to build a combination of GPUs, you can  | 
   |                               | help, dcgm:<ID>,      | build a comma-separated combo like ``dcgm:0,dcgm:2-4``. Help will give a list of available GPUs.        |                                                   
   |                               | dcgm:<ID1-ID2>        |                                                                                                         | 
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--hostengine-addr``         | host:port             | Address of the DCGM hostengine (host:port) or UDS path. When not specified, the plugin connects to      |
   |                               |                       | localhost:5555 and falls back to embedded DCGM if that connection fails.                                |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--metrics``                 | comma-separated list  | Give the list of DCGM metrics that you would like to collect, help will give the list of available      |
   |                               | of metric names or    | metrics for your platform. If no metrics are selected, the tool will collect summary data for the CPUs, |
   |                               | help                  | GPUs, and nvswitches on the system. See default metric options below.                                   |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--nic``                     | all, help, dcgm:<ID>  | Indicate which NIC(s) you are interested in or all. If you want to build a combination of NICs, you can |
   |                               | dcgm:<ID1-ID2>        | build a comma-separated combo like ``dcgm:0,dcgm:2-4``. Help will give a list of available NICs.        |                                                   
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--nvswitch``                | all, help, dcgm:<ID>  | Indicate which nvswitch(es) you are interested in or all. If you want to build a combination of         |
   |                               | dcgm:<ID1-ID2>        | nvswitch(es), you can build a comma-separated combo like ``dcgm:0,dcgm:2-4``. Help will give a list of  |
   |                               |                       | available nvswitch(es).                                                                                 |                                                   
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--sampling-period``         | milliseconds          | Sampling period in milliseconds. Minimum allowed value is 100ms.                                        |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+


Note:

   Unlike in most Nsight Systems collectors, the output from this command will
   not be sent to the standard CLI output, but rather to the output location for
   DCGM.
   
   

**Example 1 - Specifying Metrics**


  nsys profile --enable=dcgm,--metrics=gpu_temp,power_usage_instant,sm_active,
     cpu_power_utilization,cpu_temp,--cpu=dcgm:0,--gpu=dcgm:0,--sampling-period=100
     appname

Screenshot:

   :alt: DCGM screenshot
   :class: image


**Example 2 - Using Presets**

The ``s-`` prefix selects preset metric groups defined in counter_groups.yaml;
available presets are ``gpu``, ``gpu-perf``, ``cpu``, ``nvswitch``, and
``power_smoothing`` (for example, ``s-gpu-perf`` or ``s-nvswitch``).


   nsys profile --enable=dcgm,--metrics=s-gpu-perf,s-nvswitch
      ./nccl-tests/build/alltoall_perf -g 8 -n 100 -b 1M -e 32G -f 2

Screenshot:

   :alt: DCGM screenshot
   :class: image
   
For general information on Nsight Systems plugins please refer to :ref:`Nsight
Systems Plugins`.
