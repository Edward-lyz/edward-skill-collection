---
source_path: UserGuide/topics/symbol-locations.rst
title: #### Symbol Locations
---
#### Symbol Locations

Symbol resolution happens on host, and therefore does not affect performance of profiling on the target.

Press the **Symbol locations...** button to open the **Configure debug symbols location** dialog.

      :alt: Configure debug symbols location
      :class: image

Use this dialog to specify:

-  Paths of PDB files

-  Symbols servers

-  The location of the local symbol cache

To use a symbol server:

#. Install **Debugging Tools for Windows**, a part of the Windows 10 SDK .

#. Add the symbol server URL using the **Add Server** button.

   Information about Microsoft's public symbol server, which enables getting Windows operating system related debug symbols can be found here .
