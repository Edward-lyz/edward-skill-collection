---
source_path: UserGuide/topics/broken-backtraces-on-tegra.rst
title: #### Broken Backtraces on Tegra
---
#### Broken Backtraces on Tegra

In Nsight Systems Embedded Platforms Edition, in the symbols table there is a special entry called **Broken backtraces**. This entry is used to denote the point in the call chain where the unwinding algorithms used by Nsight Systems could not determine what is the next (caller) function.

Broken backtraces happen because there is no information related to the current function that the unwinding algorithms can use. In the Top-Down view, these functions are immediate children of the Broken backtraces row.

One can eliminate broken backtraces by modifying the build system to provide at least one kind of unwind information. The types of unwind information, used by the algorithms in Nsight Systems, include the following:

For ARMv7 binaries:

-  DWARF information in ELF sections: ``.debug_frame``, ``.zdebug_frame``, ``.eh_frame``, ``.eh_frame_hdr``. This information is the most precise. ``.zdebug_frame`` is a compressed version of ``.debug_frame``, so at most one of them is typically present. ``.eh_frame_hdr`` is a companion section for ``.eh_frame`` and might be absent.

   Compiler flag: ``-g``.

-  Exception handling information in EHABI format provided in ``.ARM.exidx`` and ``.ARM.extab`` ELF sections. ``.ARM.extab`` might be absent if all information is compact enough to be encoded into ``.ARM.exidx``.

   Compiler flag: ``-funwind-tables``.

-  Frame pointers (built into the ``.text`` section).

   Compiler flag: ``-fno-omit-frame-pointer``.

For Aarch64 binaries:

-  DWARF information in ELF sections: ``.debug_frame``, ``.zdebug_frame``, ``.eh_frame``, ``.eh_frame_hdr``. See additional comments above.

   Compiler flag: ``-g``.

-  Frame pointers (built into the ``.text`` section).

   Compiler flag: ``-fno-omit-frame-pointer``.

The following ELF sections should be considered empty if they have size of 4 bytes: ``.debug_frame``, ``.eh_frame``, ``.ARM.exidx``. In this case, these sections only contain termination records and no useful information.

For GCC, use the following compiler invocation to see which compiler flags are enabled in your toolchain by default (for example, to check if ``-funwind-tables`` is enabled by default):

::

   $ gcc -Q --help=common

For GCC and Clang, add ``-###`` to the compiler invocation command to see which compiler flags are actually being used.

Since EHABI and DWARF information is compiled on per-unit basis (every ``.cpp`` or ``.c`` file, as well as every static library, can be built with or without this information), presence of the ELF sections does not guarantee that every function has necessary unwind information.

Frame pointers are required by the Aarch64 Procedure Call Standard. Adding frame pointers slows down execution time, but in most cases the difference is negligible.
