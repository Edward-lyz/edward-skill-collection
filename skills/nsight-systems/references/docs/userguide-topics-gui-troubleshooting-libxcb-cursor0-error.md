---
source_path: UserGuide/topics/gui-troubleshooting-libxcb-cursor0-error.rst
title: #### xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin
---
#### xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin

If you encounter the following error, you may be missing the required `xcb-cursor` package:

::

   qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.

This issue typically occurs on RHEL but may also affect other distributions. To resolve it, install the required `xcb-cursor` package based on your OS:

-  **RHEL/CentOS/Fedora**:

   ::

      sudo dnf install -y xcb-util-cursor

-  **OpenSUSE**:

   ::

      sudo dnf install -y xcb-util-cursor

-  **Debian/Ubuntu**:

   ::

      sudo apt-get install -y libxcb-cursor0
