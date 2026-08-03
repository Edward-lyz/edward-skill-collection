---
source_path: UserGuide/topics/nvtx-trace.rst
title: NVTX Trace
---
# NVTX Trace

The NVIDIA Tools Extension Library (NVTX) is a powerful mechanism that allows
users to manually instrument their application. Nsight Systems can then collect
the information and present it on the timeline.

NVTX is shipped as a C-based, header-only library. NVIDIA also supports and
provides library-specific wrappers for C++, Python, and Rust. See the
NVTX GitHub repository .

Nsight Systems supports version 3.0 of the NVTX specification.

The most commonly used features:

-  Domains

   ::

      nvtxDomainCreate(), nvtxDomainDestroy()

   ::

      nvtxDomainRegisterString()


-  Push-pop ranges (nested ranges that start and end in the same thread).

   ::

      nvtxRangePush(), nvtxRangePushEx()

   ::

      nvtxRangePop()

   ::

      nvtxDomainRangePushEx()

   ::

      nvtxDomainRangePop()

-  Start-end ranges (ranges that are global to the process and are not restricted
   to a single thread)

   ::

      nvtxRangeStart(), nvtxRangeStartEx()

   ::

      nvtxRangeEnd()

   ::

      nvtxDomainRangeStartEx()

   ::

      nvtxDomainRangeEnd()

-  Marks

   ::

      nvtxMark(), nvtxMarkEx()

   ::

      nvtxDomainMarkEx()

-  Thread names

   ::

      nvtxNameOsThread()

-  Categories

   ::

      nvtxNameCategory()

   ::

      nvtxDomainNameCategory()

To learn more about specific features of NVTX, please refer to the NVTX header
file: ``nvToolsExt.h`` or the NVTX documentation .

Note:

   It is strongly recommended that you use registered strings for your range names.
   This enables profiling tools to use a more performant match algorithm. For
   more information about creating registered strings, see `NVTX String
   Registration
   <https://docs.nvidia.com/cuda/profiler-users-guide/index.html#nvtx-string-registration>`__.


To use NVTX in your application, follow these steps:

#. Add ``#include "nvtx3/nvToolsExt.h"`` in your source code. The nvtx3
   directory is located in the Nsight Systems package in the
   ``Target-<architecture>/nvtx/include`` directory and is available via github at
   http://github.com/NVIDIA/NVTX.

#. Add the following compiler flag: ``-ldl``

#. Add calls to the NVTX API functions. For example, try adding
   ``nvtxRangePush("main")`` in the beginning of the ``main()`` function, and
   ``nvtxRangePop()`` just before the return statement in the end.

   For convenience in C++ code, consider adding a wrapper that implements RAII
   (resource acquisition is initialization) pattern, which would guarantee that
   every range gets closed.

#. In the project settings, select the **Collect NVTX trace** checkbox.

In addition, by enabling the "Insert NVTX Marker hotkey" option it is possible
to add NVTX markers to a running non-console applications by pressing the
F11 key. These will appear in the report under the NVTX Domain named "HotKey
markers."

Typically, calls to NVTX functions can be left in the source code even if the
application is not being built for profiling purposes, since the overhead is
very low when the profiler is not attached.

NVTX is not intended to annotate very small pieces of code that are being called
very frequently. A good rule of thumb to use: if code being annotated usually
takes less than 1 microsecond to execute, adding an NVTX range around this code
should be done carefully.

Note:

   Range annotations should be matched carefully. If many ranges are opened but
   not closed, Nsight Systems has no meaningful way to visualize it. A rule of
   thumb is to not have more than a couple dozen ranges open at any point in
   time. Nsight Systems does not support reports with many unclosed ranges.


**Sample with C++ Wrapper**

The following example uses the NVTX C++ wrapper to create a range around
``some_function()`` and a nested range for each loop iteration.


::


   #include <nvtx3/nvtx3.hpp>
   #include <thread>
   #include <chrono>

   void some_function()
   {
       NVTX3_FUNC_RANGE();  // Range around the whole function

       for (int i = 0; i < 6; ++i) {
           nvtx3::scoped_range loop{"loop range"};  // Range for iteration

           // Make each iteration last for one second
           std::this_thread::sleep_for(std::chrono::seconds{1});
       }
   }


A complete program that calls ``some_function()`` does not require linking to
an NVTX library. Compile the program as usual.

::

   g++ -o example example.cpp

Run the executable with ``nsys`` to collect and view the data.

::

   nsys profile ./example
   nsys-ui report1.nsys-rep


The NVTX C++ header is available in the ``<target-platform-folder>/nvtx/include``
directory of the Nsight Systems installation.

::

   export NSYS_NVTX_PATH=<nsys_install_dir>/<target-platform-folder>/nvtx
   g++ -o example example.cpp -I${NSYS_NVTX_PATH}/include


Using the NVTX C API, the following example creates the same function and loop ranges.


::

   #include <nvtx3/nvToolsExt.h>
   #include <thread>
   #include <chrono>

   void some_function()
   {
       nvtxRangePush(__func__);

       for (int i = 0; i < 6; ++i) {
           nvtxRangePush("loop range");

           std::this_thread::sleep_for(std::chrono::seconds{1});

           nvtxRangePop();
       }

       nvtxRangePop();
   }


   :alt: NVTX range from a simple C++ example shown in Nsight Systems
   :class: image


The NVTX row shows the function's name "some_function" in the top-level range
and the "loop range" message in the nested ranges. The loop iterations each last
for the expected one second.


If the function returns or throws before calling ``nvtxRangePop``, the range is
left unclosed and tool behavior is undefined. The C++ API is safer because the
range object ends the range from its destructor.


**NVTX Payloads and Counters**

NVTX Extended Payloads and NVTX Counters increase the flexibility of NVTX
annotations by allowing users to pass arbitrary structured data
to NVTX events. This then will allow users to define the layout of this data in
the Nsight Systems UI without additional data conversion.

For more information, see NVTX documentation .


      :alt: NVTX Payloads and Counters
      :class: image


**NVTX Domains and Categories**

NVTX domains enable scoping of annotations. Unless specified differently, all
events and annotations are in the default domain. Additionally, categories can
be used to group events.

Nsight Systems gives the user the ability to include or exclude NVTX events from
a particular domain. This can be especially useful if you are profiling across
multiple libraries and are only interested in nvtx events from some of them.

   :alt: NVTX domain selection screen
   :class: image

This functionality is also available from the CLI. See the CLI documentation
for ``--nvtx-domain-include`` and ``--nvtx-domain-exclude`` for more details.

Categories that are set in by the user will be recognized and displayed in the
GUI.

   :alt: NVTX screenshot with domains and categories
   :class: image
