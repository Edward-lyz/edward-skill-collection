---
source_path: UserGuide/topics/openshmem-library-trace.rst
title: ## OpenSHMEM Library Trace
---
## OpenSHMEM Library Trace

If OpenSHMEM library trace is selected Nsight Systems will trace the subset of OpenSHMEM API functions that are most likely be involved in performance bottlenecks. To keep overhead low Nsight Systems does not trace all functions.

**OpenSHMEM 1.5 Functions Not Traced**

::

   shmem_my_pe
   shmem_n_pes
   shmem_global_exit
   shmem_pe_accessible
   shmem_addr_accessible
   shmem_ctx_{create,destroy,get_team}
   shmem_global_exit
   shmem_info_get_{version,name}
   shmem_{my_pe,n_pes,pe_accessible,ptr}
   shmem_query_thread
   shmem_team_{create_ctx,destroy}
   shmem_team_get_config
   shmem_team_{my_pe,n_pes,translate_pe}
   shmem_team_split_{2d,strided}
   shmem_test*
