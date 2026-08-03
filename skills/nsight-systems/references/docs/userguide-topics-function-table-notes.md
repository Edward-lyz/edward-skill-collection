---
source_path: UserGuide/topics/function-table-notes.rst
title: #### Function Table Notes
---
#### Function Table Notes

**Last Branch Records vs. Frame Pointers**

Two of the mechanisms available for collecting backtraces are Intel Last Branch Records (LBRs) and frame pointers. LBRs are used to trace every branch instruction via a limited set of hardware registers. They can be configured to generate backtraces but have finite depth based on the CPU’s microarchitecture. LBRs are effectively free to collect but may not be as deep as you need in order to fully understand how the workload arrived a specific Instruction Pointer (IP).

Frame pointers only work when a binary is compiled with the ``-fno-omit-frame-pointer`` compiler switch. To determine if frame pointers are enabled on an x86_64 binary running on Linux, dump a binary’s assembly code using the ``objdump -d [binary_file]`` command and look for this pattern at the beginning of all functions;


      push   %rbp
      mov    %rsp,%rbp

When frame pointers are available in a binary, full stack traces will be captured. Note that libraries that are frequently used by applications and ship with the operating system, such as libc, are generated in release mode and therefore do not include frame pointers. Frequently, when a backtrace includes an address from a system library, the backtrace will fail to resolve further as the frame pointer trail goes cold due to a missing frame pointer.

A simple application was developed to show the difference. The application calls function a(), which calls b(), which calls c(), etc. Function z() calls a heavy compute function called matrix_multiply(). Almost all of the IP samples are collected while matrix_multiple is executing. The next two screen shots show one of the main differences between frame pointers and LBRs.

      :alt: frame pointer backtrace
      :class: image

..

      :alt: lbr backtrace
      :class: image

Note that the frame pointer example shows the full stack trace, while the LBR example only shows part of the stack due to the limited number of LBR registers in the CPU.

**Kernel Samples**

When an IP sample is captured while a kernel mode (i.e. operating system) function is executing, the sample will be shown with an address that starts with 0xffffffff and map to the [kernel.kallsyms] module.

      :alt: kernel mode sample backtrace
      :class: image

**[vdso]**

Samples may be collected while a CPU is executing functions in the Virtual Dynamic Shared Object. In this case, the sample will be resolved (i.e., mapped) to the [vdso] module. The vdso man page  provides the following description of the vdso:


       The “vDSO“ (virtual dynamic shared object) is a small shared library
       that the kernel automatically maps into the address space of all
       user-space applications.  Applications usually do not need to concern
       themselves with these details as the vDSO is most commonly called by
       the C library.  This way you can code in the normal way using
       standard functions and the C library will take care of using any
       functionality that is available via the vDSO.
       
       Why does the vDSO exist at all?  There are some system calls the
       kernel provides that user-space code ends up using frequently, to the
       point that such calls can dominate overall performance. This is due
       both to the frequency of the call as well as the context-switch
       overhead that results from exiting user space and entering the
       kernel.

**[Unknown]**

When an address can not be resolved (i.e., mapped to a module), its address within the process’ address space will be shown and its module will be marked as [Unknown].
