---
source_path: UserGuide/topics/limitations.rst
title: ## Limitations
---
## Limitations

-  Nsight Systems only traces syscall wrappers exposed by the C runtime. It is not able to trace syscall invoked through assembly code.

-  Additional thread states, as well as backtrace collection on long calls, are only enabled if sampling is turned on.

-  It is not possible to configure the depth and duration threshold when collecting backtraces. Currently, only OS runtime libraries calls longer than 80 μs will generate a backtrace with a maximum of 24 frames. This limitation will be removed in a future version of the product.

-  It is required to compile your application and libraries with the ``-funwind-tables`` compiler flag in order for Nsight Systems to unwind the backtraces correctly.
