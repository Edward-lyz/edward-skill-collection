---
source_path: UserGuide/topics/symbol-locations-on-linux-and-qnx.rst
title: ## Symbol Locations on Linux and QNX
---
## Symbol Locations on Linux and QNX

On Linux and QNX, user can specify local directories with symbol/debug files and
Debuginfod symbol servers.

**The list of directories with symbol files**

-  ``--debug-symbols`` CLI option, for example:


      --debug-symbols=/lib:/root/symbols

-  Alternatively, ``DbgFileSearchPath`` config option can be used, for example:


      NSYS_CONFIG_DIRECTIVES='DbgFileSearchPath="/lib:/root/symbols"' nsys profile <app>

On Linux, the default path is ``/usr/lib/debug``. On QNX, there is no default path.
The search is recursive.

**Debuginfod symbol servers**

-  Nsight Systems automatically queries and downloads missing symbols from Debuginfod servers.

-  Official public servers exist for Ubuntu, Debian, Fedora and other distributions.

-  Federated servers for multiple distros .

-  At least one server URL should be provided by ``DEBUGINFOD_URLS`` environment variable to enable Debuginfod functionality.
   ``DEBUGINFOD_URLS`` contains a list of Debuginfod servers (space separated URLs), example (local and public servers):


      export DEBUGINFOD_URLS="http://localhost:8002 https://debuginfod.ubuntu.com"
      nsys profile <app>

**Debuginfod cache directory**

-  Nsight Systems stores downloaded files in:

   -  ``$DEBUGINFOD_CACHE_PATH/debuginfod_client`` - if ``DEBUGINFOD_CACHE_PATH`` is set.

   -  Otherwise, if ``XDG_CACHE_HOME`` is set, then ``$XDG_CACHE_HOME/debuginfod_client`` directory will be used.

   -  Otherwise, if neither DEBUGINFOD_CACHE_PATH nor XDG_CACHE_HOME are set, ``$HOME/.cache/debuginfod_client/`` directory is the default location for downloaded files.

-  Nsight Systems uses cached files only if Debuginfod functionality is enabled (``DEBUGINFOD_URLS`` environment variable is set).

-  Nsight Systems also support reading LLVM cache files (``$HOME/.cache/llvm-debuginfod/``).

Nsight Systems shows the download progress (fetching the files from remote HTTP servers can take a long time, especially for system wide CPU sampling mode):

-  The total amount of files and how many files are already downloaded.

-  User is able to cancel the download process (Ctrl+C):


      Press Ctrl-C to stop symbol files downloading
      [1/16] Downloaded symbol information for /usr/lib/x86_64-linux-gnu/libnss_files-2.31.so
      ...
