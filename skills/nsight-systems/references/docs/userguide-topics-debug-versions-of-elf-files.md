---
source_path: UserGuide/topics/debug-versions-of-elf-files.rst
title: #### Debug Versions of ELF Files
---
#### Debug Versions of ELF Files

Often, after a binary is built, especially if it is built with debug information (``-g`` compiler flag), it gets stripped before deploying or installing. In this case, ELF sections that contain useful information, such as non-export function names or unwind information, can get stripped as well.

One solution is to deploy or install the original unstripped library instead of the stripped one, but in many cases this would be inconvenient. Nsight Systems can use missing information from alternative locations.

For target devices with Ubuntu, see Debug Symbol Packages . These packages typically install debug ELF files with ``/usr/lib/debug`` prefix. Nsight Systems can find debug libraries there, and if it matches the original library (e.g., the built-in ``BuildID`` is the same), it will be picked up and used to provide symbol names and unwind information.

Many packages have debug companions in the same repository and can be directly installed with APT (``apt-get``). Look for packages with the ``-dbg`` suffix. For other packages, refer to the Debug Symbol Packages  wiki page on how to add the debs package repository. After setting up the repository and running apt-get update, look for packages with ``-dbgsym`` suffix.

To verify that a debug version of a library has been picked up and downloaded from the target device, look in the **Module Summary** section of **Analysis Summary**:

      :alt: Debug library has been used
      :class: image
