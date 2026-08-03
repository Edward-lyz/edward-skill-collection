---
source_path: UserGuide/topics/example-mpi.rst
title: #### Example: MPI
---
#### Example: MPI

A typical scenario is when a computing job is run using one of the MPI
implementations. Each instance of the app can be profiled separately, resulting
in multiple report files. For example:

::

   # Run MPI job without the profiler:
   mpirun <mpirun-options> ./myApp
   # Run MPI job and profile each instance of the application:
   mpirun <mpirun-options> nsys profile -o report-%p <nsys-options>./myApp

When each MPI rank runs on a different node, the command above works fine, since
the default pairing mode (different hardware) will be used.

When all MPI ranks run the localhost only, use this command (value "A" was
chosen arbitrarily, it can be any non-empty string):

   
   NSYS_SYSTEM_ID=A mpirun <mpirun-options> nsys profile -o report-%p < nsys -options> ./myApp

For convenience, the MPI rank can be encoded into the report filename. For
Open MPI, use the following command to create report files based on the global
rank value:

   
   mpirun <mpirun-options> nsys profile -o report-%q{OMPI_COMM_WORLD_RANK} < nsys -options> ./myApp

MPICH-based implementations set the environment variable ``PMI_RANK`` and Slurm
(``srun``) provides the global MPI rank in ``SLURM_PROCID``.
