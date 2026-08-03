---
source_path: UserGuide/topics/other-platforms-or-if-the-previous-steps-did-not-help.rst
title: ### Other platforms, or if the previous steps did not help
---
### Other platforms, or if the previous steps did not help

Launch Nsight Systems using the following command line to determine which libraries are missing and install them.

::

   $ QT_DEBUG_PLUGINS=1 [installation_path]/host-linux-[arch]/nsys-ui

If the workload does not run when launched via Nsight Systems or the timeline is empty, check the stderr.log and stdout.log (click on drop-down menu showing **Timeline View** and click on **Files**) to see the errors encountered by the app.

      :alt: Stderr Log
      :class: image
