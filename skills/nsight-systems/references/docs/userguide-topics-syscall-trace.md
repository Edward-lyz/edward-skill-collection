---
source_path: UserGuide/topics/syscall-trace.rst
title: Syscall Trace
---
# Syscall Trace

Nsight Systems for Linux and Nsight Systems Embedded Platforms Edition are capable of tracing Linux system calls in kernel space. This feature uses Linux's eBPF technology, and is supported on systems running Linux v5.11 or newer, specifically those that are built with ``CONFIG_DEBUG_INFO_BTF`` enabled, which is the default on most major Linux distros. This feature requires ``CAP_BPF`` and ``CAP_PERFMON`` capabilities (alternatively, ``CAP_SYS_ADMIN`` or root privileges) for the ``nsys`` process, see the capabilities man page  for details.

To enable this feature:

**CLI** — Add the ``--syscall`` option to the ``nsys start`` or ``nsys profile`` commands (setting ``syscall`` in the ``--trace`` option is deprecated and will be ignored). The following values are supported:

- ``none`` — No syscall tracing [default].
- ``process-tree`` — Collect syscalls for the profiled application process and its child processes.
- ``pid-namespace`` — Collect syscalls made by all processes in the current PID namespace and its child namespaces. This is very close to how other features work in the ``system-wide`` mode, e.g. inside a container, tracing will be limited to this container.

**GUI** — Select the **Collect syscall trace** checkbox. Currently, equivalent to the ``--syscall=process-tree`` option.

      :alt: Syscall trace GUI selection
      :class: image

Please note that only syscalls running 1000ns and more are traced.

Example screenshot:

      :alt: Syscall trace timeline example
      :class: image

Long running (more than 80 microseconds) syscalls are also collected with their backtraces:

      :alt: Syscall backtrace example
      :class: image
