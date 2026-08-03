---
source_path: UserGuide/topics/handling-application-launchers.rst
title: ## Handling Application Launchers (mpirun, deepspeed, etc)
---
## Handling Application Launchers (mpirun, deepspeed, etc)

Nsight Systems has built-in API trace support for various communication APIs,
such as MPI, OpenSHMEM, UCX, NCCL and NVSHMEM.
To execute respective programs on multiple different machines (compute nodes),
usually launchers are used, e.g., ``mpirun``/``mpiexec`` (MPI),
``shmemrun``/``oshrun`` (OpenSHMEM), ``srun`` (SLURM) or ``deepspeed``.

In **single-node profiling** sessions, the Nsight Systems CLI can be prefixed before
the program (binary) or the launcher. In the latter case, the execution of the
launcher will also be profiled and all processes will be recorded into the same
report file, e.g for mpirun

    ``nsys profile [nsys args] mpirun [mpirun args] ...``

In **multi-node profiling** sessions, the Nsight Systems CLI has to be prefixed
before the application, but not before the launcher command, e.g. for mpirun

    ``mpirun [mpirun args] nsys profile [nsys args] ...``

You can use ``%q{OMPI_COMM_WORLD_RANK}`` (Open MPI), ``%q{PMI_RANK}`` (MPICH),
``%q{SLURM_PROCID}`` (Slurm) or ``%p`` in the ``-o|--output`` option to include
the rank or process ID into the report file name.

Warning:
  An error will occur if several processes want to write to the same report file at the same time.


#### Profile a Single Process or a Subset of Processes

It might be reasonable to profile only a single or a few representative
processes of a program run, e.g., to reduce the amount of measurement data.

To achieve this, a wrapper script can be used. The following script called
*nsys_profile.sh* uses nsys to profile MPI rank 0 only.

::

   #!/bin/bash

   # Use $PMI_RANK for MPICH and $SLURM_PROCID with srun.
   if [ $OMPI_COMM_WORLD_RANK -eq 0 ]; then
     nsys profile -e NSYS_MPI_STORE_TEAMS_PER_RANK=1 -t mpi "$@"
   else
     "$@"
   fi

You can change the profiling options accordingly and execute with
``mpirun [mpirun options] ./nsys_profile.sh ./myapp [app options]``.
The above code can be easily adapted for OpenSHMEM and SLURM launchers.

Note:

   If only a subset of MPI ranks is profiled, set the environment variable
   ``NSYS_MPI_STORE_TEAMS_PER_RANK=1`` to store all members of custom MPI
   communicators per MPI rank. Otherwise, the execution might hang or fail with
   an MPI error.

#### DeepSpeed

DeepSpeed provides a parallel launcher, which launches a Python script on
multiple nodes and/or GPUs. For multi-node runs, a simple wrapper script
(*nsys_profile.sh*) is required to profile with Nsight Systems.

::

    #! /bin/bash
    nsys profile -t cuda,mpi,nvtx,cudnn -o rname.%p python ...

This above script has to be used with the `--no-python`
option:

::

   deepspeed --no_python [deepspeed args] ./nsys_profile.sh


#### Torchrun/Pytorch

Here is an example of using Nsight Systems to selectively profile GPUs in a
multi-gpu system using torchrun.


::

   $ cat run.py
 
   import subprocess
   import sys
   import os local_rank = int(os.environ["LOCAL_RANK"])
 
   args = sys.argv[1:]
   args_string = ' '.join(args)

   #Define the command to execute
   print(f"Profile local rank {local_rank} only")
   if local_rank == 0:
     command = "nsys profile -t cuda,nvtx -o test_run python " + args_string
   else:
     command = "python " + args_string
 
   #Run the command
   subprocess.run(command, shell=True)
 
   $ torchrun --nnodes=1 --nproc-per-node=8 run.py target_python_script.py


#### GPU and NIC metrics collection
If multiple instances of ``nsys profile`` are executed concurrently on the same
node, and GPU and/or NIC metrics collection is enabled, each process will collect
metrics for all available NICs and tries to collect GPU metrics for the
specified devices. This can be avoided with a simple bash script similar to the
following:

::

   #!/bin/bash

   # Use $SLURM_LOCALID with srun.
   if [ $OMPI_COMM_WORLD_LOCAL_RANK -eq 0 ]; then
     nsys profile --nic-metrics=lf --gpu-metrics-devices=all "$@"
   else
     nsys profile "$@"
   fi

This above script will collect NIC and GPU metrics only for one rank, the node-local rank 0.
Alternatively, if one rank per GPU is used, the GPU metrics devices can be specified based on the
node-local rank in a wrapper script as follows:

::

   #!/bin/bash

   # Use $SLURM_LOCALID with srun.
   nsys profile -e CUDA_VISIBLE_DEVICES=${OMPI_COMM_WORLD_LOCAL_RANK} \
     --gpu-metrics-devices=${OMPI_COMM_WORLD_LOCAL_RANK} "$@"
