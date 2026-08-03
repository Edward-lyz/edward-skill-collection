---
source_path: UserGuide/topics/gui-troubleshooting-empty-summaries-error.rst
title: #### Empty or Black Pages in Analysis or Diagnostics Summary
---
#### Empty or Black Pages in Analysis or Diagnostics Summary

If the **Analysis Summary** or **Diagnostics Summary** pages appear empty or black when running Nsight Systems, this may be caused by rendering issues, often related to drivers for OpenGL or Vulkan.

To resolve this, try running Nsight Systems with the following command:

::

   QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox" QMLSCENE_DEVICE=softwarecontext [installation_path]/host-linux-[arch]/nsys-ui
