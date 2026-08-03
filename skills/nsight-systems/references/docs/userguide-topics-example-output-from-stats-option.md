---
source_path: UserGuide/topics/example-output-from---stats-option.rst
title: ## Example Output from ``--stats`` Option
---
## Example Output from ``--stats`` Option

The ``nsys stats`` command can be used post analysis to generate specific or personalized reports. For a default fixed set of summary statistics to be automatically generated, you can use the ``--stats`` option with the ``nsys profile`` or ``nsys start`` command to generate a fixed set of useful summary statistics.

If your run traces CUDA, these include CUDA API, Kernel, and Memory Operation statistics:

   :alt: CUDA Statistics
   :class: image

If your run traces OS runtime events or NVTX push-pop ranges:

   :alt: OS runtime and NVTX Statistics
   :class: image

If your run traces graphics debug markers these include DX11 debug markers, DX12 debug markers, Vulkan debug markers or KHR debug markers:

   :alt: Graphics Vulkan debug markers Statistics
   :class: image

Recipes for these statistics as well as documentation on how to create your own metrics will be available in a future version of the tool.
