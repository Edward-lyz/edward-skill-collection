---
source_path: UserGuide/topics/locking-a-resource.rst
title: ## Locking a Resource
---
## Locking a Resource

The functions listed below receive a special treatment. If the tool detects that the resource is already acquired by another thread and will induce a blocking call, we always trace it. Otherwise, it will never be traced.

::

   pthread_mutex_lock
   pthread_rwlock_rdlock
   pthread_rwlock_wrlock
   pthread_spin_lock
   sem_wait

Note that even if a call is determined as potentially blocking, there is a chance that it may not actually block after a few cycles have elapsed. The call will still be traced in this scenario.
