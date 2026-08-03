---
source_path: UserGuide/topics/mpi-api-trace.rst
title: ## MPI API Trace
---
## MPI API Trace

Nsight Systems has built-in API trace support for Open MPI and MPICH
based MPI implementations via ``--trace=mpi`` or by selecting the *MPI* checkbox
under *Network profiling options*. If the auto-detection of the MPI
implementation fails, it is possible to specify
it via ``--mpi-impl=[openmpi|mpich]`` or the respective checkbox in the GUI.

Nsight Systems will trace a subset of the MPI API, including blocking and
non-blocking point-to-point and collective communications as well as MPI
one-sided communications, file I/O, and pack operations
(see  MPI functions traced).


If you require more control over the list of traced APIs or if you are using a
different MPI implementation, you can use the
NVTX wrappers for MPI 
on GitHub. Choose an NVTX domain name other than "MPI," since it is filtered out
by Nsight Systems when MPI tracing is not enabled. Use the NVTX-instrumented MPI
wrapper library as follows:


   nsys profile -e LD_PRELOAD=${PATH_TO_YOUR_NVTX_MPI_LIB} --trace=nvtx


   :alt: MPI API trace
   :class: image
   
Note:
   If not all ranks are traced, ``NSYS_MPI_STORE_TEAMS_PER_RANK`` has to be set to ``1``.
   If communicator tracking is still causing issues, it can be disabled by setting
   ``NSYS_MPI_DISABLE_COMMUNICATOR_TRACKING=1``.
   

#### MPI Communication Parameters

Nsight Systems can get additional information about MPI communication parameters. Currently, the parameters are only visible in the mouseover tooltips or in the event log. This means that the data is only available via the GUI. Future versions of the tool will export this information into the SQLite data files for postrun analysis.

In order to fully interpret MPI communications, data for all ranks associated with a communication operation must be loaded into Nsight Systems.

Here is an example of ``MPI_COMM_WORLD`` data. This does not require any additional team data, since local rank is the same as global rank.

(Screenshot shows communication parameters for an MPI_Bcast call on rank 3.)

   :alt: MPI communication parameter trace
   :class: image

When not all processes that are involved in an MPI communication are loaded into Nsight Systems the following information is available.

-  Right-hand screenshot shows a reused communicator handle (last number increased).
-  Encoding: ``MPI_COMM[\*team size\*]*global-group-root-rank\*.*group-ID\*``

   :alt: MPI communication parameter trace
   :class: image

When all reports are loaded into Nsight Systems:

-  World rank is shown in addition to group-local rank "(world rank X)."
-  Encoding: MPI_COMM[\*team size\*]{rank0, rank1, ...}.
-  At most 8 ranks are shown (the numbers represent world ranks, the position in the list is the group-local rank).

   :alt: MPI communication parameter trace
   :class: image


#### MPI functions traced

::

   MPI_Init[_thread], MPI_Finalize
   MPI_Send, MPI_{B,S,R}send, MPI_Recv, MPI_Mrecv
   MPI_Sendrecv[_replace]

   MPI_Barrier, MPI_Bcast
   MPI_Scatter[v], MPI_Gather[v]
   MPI_Allgather[v], MPI_Alltoall[{v,w}]
   MPI_Allreduce, MPI_Reduce[_{scatter,scatter_block,local}]
   MPI_Scan, MPI_Exscan

   MPI_Isend, MPI_I{b,s,r}send, MPI_I[m]recv
   MPI_{Send,Bsend,Ssend,Rsend,Recv}_init
   MPI_Start[all]
   MPI_Ibarrier, MPI_Ibcast
   MPI_Iscatter[v], MPI_Igather[v]
   MPI_Iallgather[v], MPI_Ialltoall[{v,w}]
   MPI_Iallreduce, MPI_Ireduce[{scatter,scatter_block}]
   MPI_I[ex]scan
   MPI_Wait[{all,any,some}]

   MPI_Put, MPI_Rput, MPI_Get, MPI_Rget
   MPI_Accumulate, MPI_Raccumulate
   MPI_Get_accumulate, MPI_Rget_accumulate
   MPI_Fetch_and_op, MPI_Compare_and_swap

   MPI_Win_allocate[_shared]
   MPI_Win_create[_dynamic]
   MPI_Win_{attach, detach}
   MPI_Win_free
   MPI_Win_fence
   MPI_Win_{start, complete, post, wait}
   MPI_Win_[un]lock[_all]
   MPI_Win_flush[_local][_all]
   MPI_Win_sync

   MPI_File_{open,close,delete,sync}
   MPI_File_{read,write}[_{all,all_begin,all_end}]
   MPI_File_{read,write}_at[_{all,all_begin,all_end}]
   MPI_File_{read,write}_shared
   MPI_File_{read,write}_ordered[_{begin,end}]
   MPI_File_i{read,write}[_{all,at,at_all,shared}]
   MPI_File_set_{size,view,info}
   MPI_File_get_{size,view,info,group,amode}
   MPI_File_preallocate

   MPI_Pack[_external]
   MPI_Unpack[_external]
