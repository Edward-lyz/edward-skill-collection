---
source_path: UserGuide/topics/aws-efa-sample-plugin.rst
title: #### Amazon AWS EFA NIC Metrics
---
#### Amazon AWS EFA NIC Metrics

Nsight Systems can now periodically sample performance counters for
AWS Elastic Fabric Adapters (EFAs) and plot it on the timeline in the GUI.
This enables developers to analyze how network communications may be
involved with the critical path of their multi-node application.
Created in collaboration with AWS, this plugin will
work on `AWS EC2 NVIDIA GPU accelerated compute instances
<https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/efa.html#efa-instance-types/>`__ .

To enable the AWS EFA metrics add the following option to the |cli-name|
``profile`` or ``start`` commands:

::

  --enable efa_metrics[,arg1[=value1],arg2[=value2], ...]


There are no spaces following ``efa_metrics`` plugin name. It is followed by a
comma separated list of arguments or argument=value pairs. Arguments with spaces
should be enclosed in double quotes.

Supported arguments are:

  :name: table_awsefa_table
  :class: table-compact

  +-------------------------+------------------------------------------------+------------------------+-------------------------------------------------+
  | Name                    | Possible Parameters                            | Default                | Switch Description                              |
  +=========================+================================================+========================+=================================================+
  | ``-efa-non-rdma``       | true, false                                    | false                  | Sample Infiniband non-RDMA counters             |
  +-------------------------+------------------------------------------------+------------------------+-------------------------------------------------+
  | ``-efa-sysfs``          | <path>                                         | /sys/class/infiniband  | Root directory for EFA counters sysfs           |
  +-------------------------+------------------------------------------------+------------------------+-------------------------------------------------+
  | ``-efa-work-requests``  | true, false                                    | false                  | Sample Infiniband WorkRequest counters          |
  +-------------------------+------------------------------------------------+------------------------+-------------------------------------------------+
  | ``-errors``             | true, false                                    | false                  | Sample error counters                           |
  +-------------------------+------------------------------------------------+------------------------+-------------------------------------------------+
  | ``-freq``               | integer, a negative value means 1/F frequency  | 10                     | Target sample frequency in hertz                |
  +-------------------------+------------------------------------------------+------------------------+-------------------------------------------------+
  | ``-mode``               | throughput, delta, total                       | throughput             | Report sampled counters as a value per second,  |
  |                         |                                                |                        | delta since previous sample, or an accumulated  |
  |                         |                                                |                        | sum.                                            |
  +-------------------------+------------------------------------------------+------------------------+-------------------------------------------------+
  | ``-packets``            | true, false                                    | false                  | Sample packet counters                          |
  +-------------------------+------------------------------------------------+------------------------+-------------------------------------------------+

**Usage Examples**

-  ``nsys profile --enable efa_metrics ...``
    Sample all EFA adapters, display as bytes per second.
-  ``nsys profile --enable efa_metrics,-packets,-errors,-efa-non-rdma ...``
    Sample all available EFA adapter counters.
-  ``nsys profile --enable efa_metrics,-mode=total ...``
    Sample all EFA adapters, display as total value sum since profiling start.
-  ``nsys profile --enable efa_metrics,-efa-counters-sysfs="/mnt/nv/sys", ...``
    Look for EFA counters in a different sysfs directory. Useful in some k8s environments.

This collector is the first use case for the Nsight Systems Plugins
system.
