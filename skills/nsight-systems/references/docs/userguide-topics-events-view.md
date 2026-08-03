---
source_path: UserGuide/topics/events-view.rst
title: ## Events View
---
## Events View

The Events View provides a tabular display of the trace events. The view contents can be searched and sorted.

Double-clicking an item in the Events View automatically focuses the Timeline View on the corresponding timeline item.

API calls, GPU executions, and debug markers that occurred within the boundaries of a debug marker are displayed nested to that debug marker. Multiple levels of nesting are supported.

Events view recognizes these types of debug markers:

-  NVTX

-  Vulkan VK_EXT_debug_marker markers, VK_EXT_debug_utils labels

-  PIX events and markers

-  OpenGL KHR_debug markers

   :alt: Events View nested debug markers
   :class: image

You can copy and paste from the events view by highlighting rows, using **Shift** or **Ctrl** to enable multi-select. Right clicking on the selection will give you a copy option.

   :alt: Events View copy selection
   :class: image

Pasting into text gives you a tab separated view:

   :alt: Events View paste into notepad
   :class: image

Pasting into spreadsheet properly copies into rows and columns:

   :alt: Events View paste into spreadsheet
   :class: image
