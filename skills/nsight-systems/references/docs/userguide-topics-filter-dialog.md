---
source_path: UserGuide/topics/filter-dialog.rst
title: #### Filter Dialog
---
#### Filter Dialog

      :alt: Filter dialog
      :class: image

-  **Collapse unresolved lines** is useful if some of the binary code does not have symbols. In this case, subtrees that consist of only unresolved symbols get collapsed in the Top-Down view, since they provide very little useful information.
-  **Hide functions with CPU usage below X%** is useful for large applications, where the sampling profiler hits lots of function just a few times. To filter out the "long tail," which is typically not important for CPU performance bottleneck analysis, this checkbox should be selected.
