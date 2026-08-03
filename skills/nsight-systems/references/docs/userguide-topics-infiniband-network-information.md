---
source_path: UserGuide/topics/infiniband-network-information.rst
title: ## InfiniBand Network Information
---
## InfiniBand Network Information

**Overview**

By default, Nsight Systems displays low-level identifiers like LIDs (Local
Identifiers) and GUIDs (Globally Unique Identifiers). Instead, Nsight Systems
can leverage InfiniBand network information to display the actual names of nodes
and switches. This makes the Nsight Systems reports much more intuitive and
easier to understand at a glance.

InfiniBand network information discovery is done using the ibdiagnet utility.
Either:

 -  Run ibdiagnet and store the generated network information files to be later
    used by Nsight Systems. 

    - This method is useful for large networks, where
       ibdiagnet’s network discovery time may be long, and for networks where only
       administrators have permissions to query the network information.

 -  A user can ask Nsight Systems to run ibdiagnet to collect the network
    information during the profiling session. 

    - This method is useful for small networks.

**Limitations/Requirements**

The user needs to have permission to send MADs (management datagrams). To check
if you have permission to send MADs, check if you can access the
``/dev/infiniband/umad*`` files. To give user permissions to send MADs on RedHat
systems, follow the directions at `RedHat Solutions
<https://access.redhat.com/solutions/5929621>`__.

**Relevant Switches**

The following Nsight Systems command line switches enable collecting InfiniBand
network information:

 -  ``ib-net-info-devices``
     This should be followed by a comma separated list
     of NIC names, from which ibdiagnet will run network discovery. The results
     of the network discovery will be automatically loaded into Nsight Systems.
 -  ``ib-net-info-files``
     This should be followed by a comma separated list of
     pre-generated ibdiagnet db_csv file paths, which Nsight Systems will read.
 -  ``ib-net-info-output``
     This should be followed by a path of a directory
     into which Nsight Systems will store the ibdiagnet network discovery data.
     These files will be used by the ``ib-net-info-devices`` command
     line switch. This command line switch can only be used together with the
     ``ib-net-info-devices`` command line switch.


      :scale: 50%
      :alt: InfiniBand network information
      :class: image
      
      
The above image displays a congestion event. InfiniBand network information is
used for displaying node and switch names instead of LIDs.
