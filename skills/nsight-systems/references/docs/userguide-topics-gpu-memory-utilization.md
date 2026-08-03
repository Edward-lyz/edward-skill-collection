---
source_path: UserGuide/topics/gpu-memory-utilization.rst
title: ## Windows GPU Memory Utilization
---
## Windows GPU Memory Utilization

Each GPU has two rows detailing its memory utilization: **GPU VRAM**, showing
the memory consumed on the device, and **GPU WDDM SYSMEM**, showing the memory
consumed on the host computer RAM.

   :alt: Memory Utilization rows
   :class: image

These rows show a green-colored line graph for the memory budget for this memory
segment, and an orange-colored line graph for the actual amount of memory used.
Note that these graphs are scaled to fit the highest value enconutered, as
indicated by the "Y axis" value in the row header. You can use the vertical zoom
slider in the top-right of the timeline view to make the row taller and view the
graph in more detail.

   :alt: Vertical Zoom slider
   :class: image

Note that the value in the GPU VRAM row is not the same as the CUDA kernel
memory allocation graph, see CUDA GPU Memory Allocation Graph for that
functionality.

The GPU VRAM row also has several child rows, accessed by expanding the row in
the tree view

The events will be captured if "Collect WDDM Trace" is enabled along with either "Collect WDDM memory trace"
or "Extensive trace including Hardware Scheduling queues..." in the Nsight Systems Project Settings.

   :alt: GPU VRAM row expanded
   :class: image

**VidMm Device Suspension**

This row displays time ranges when the GPU memory manager suspended all memory
transfer operations, pending the completion of a single memory transfer.

The events will be captured if "Collect WDDM Trace" and "Extensive trace including Hardware Scheduling queues,
context status, allocations, sync wait and signal events, etc." are enabled in the
Nsight Systems Project Settings.

**Demoted Memory**

This row displays the amount of VRAM that was demoted from GPU local memory to
non-local memory (possibly due to exceeding the VRAM budget) as a blue-colored
line graph. High amounts of demoted memory could be indicative of video memory
leaks or poor memory management. Note that the Demoted memory row is scaled to
its highest value, similar to the GPU VRAM and GPU WDDM SYSMEM rows.

The events will be captured if "Collect WDDM Trace" is enabled along with either "Collect WDDM memory trace"
or "Extensive trace including Hardware Scheduling queues..." in the Nsight Systems Project Settings.

**Resource Allocations**

   :alt: Resource Allocations row
   :class: image

This row shows markers indicating resource allocation events. VRAM resources are
shown as green markers while SYSMEM resources are shown in gray. Hovering over a
marker or selecting it in the Events view  will display
all the allocation parameters as well as the call stack that led to the
allocation event.

The events will be captured if "Collect WDDM Trace" is enabled along with either "Collect WDDM memory trace"
or "Extensive trace including Hardware Scheduling queues..." in the Nsight Systems Project Settings.

**Resource Migrations**

   :alt: Resource Migrations row
   :class: image

This row displays a breakdown of resources' movement between VRAM and SYSMEM,
focusing on resource evictions. The main row shows a timeline of total evicted
resource memory and count as a red-colored line graph.

Each child row displays a timeline of the status of each resource, as reflected
by WDDM events related to it. If the object has been named using PIX or
``ID3D11Object::SetName`` / ``ID3D12Object::SetName``, the name will be shown
in the row title. Whether named or not, the row title will also show the
resource dimensions, format, priority, and the memory size migrated. If the
resource was migrated in parts using subresources, the row can be expanded to
show the status for each subresource at any given time.

Expanding the row for a resource will show the individual WDDM events relevant
to it and the call stacks that led to each event.

By default, the resources are sorted by Relevance (most / largest migrations).
Right-clicking the main Resource Migrations row header allows choosing between
the following sorting options:

* Relevance
* Name
* Format
* Priority
* Earliest allocation timestamp (order of appearance on the host)
* Earliest migration timestamp (order of appearance on the device)

The top 5 resources are shown initially. If more than 5 resources exist, a row
showing the number of hidden resources and buttons allowing to show more or
fewer of them will appear below them. Right-click this row and select "show all"
or "show all collapsed" to display all the resources at once.

The events will be captured if "Collect WDDM Trace" is enabled along with either "Collect WDDM memory trace"
or "Extensive trace including Hardware Scheduling queues..." in the Nsight Systems Project Settings.
Additionally, to correlate Graphics API debug name events with resource migration events, the "Collect DX12"
or "Collect Vulkan" option should be enabled.

**Memory Transfer**

   :alt: Memory Transfer row
   :class: image

This row shows an overview of all memory transfer operations. Device-to-host
transfers are shown in orange, host-to-device transfers are shown in green,
discarded device memory is shown in light green, and unknown events are shown
in dark gray. The height of each event marker corresponds to the amount of
memory that the event affected. Hovering over the marker will show the exact amount.

Expanding the row will show a breakdown of the events by each specific type.

The events will be captured if "Collect WDDM Trace" is enabled along with either "Collect WDDM memory trace"
or "Extensive trace including Hardware Scheduling queues..." in the Nsight Systems Project Settings.

**System Committed VRAM**

   :alt: System Committed VRAM
   :class: image

This row represents the total size of committed VRAM by all processes currently using the GPU.
The stacked chart displays colored layers. Each layer corresponds to the VRAM commitment of a
specific process.

To track VRAM commitment, enable "Collect WDDM Trace" along with either "Collect WDDM memory trace"
or "Extensive trace including Hardware Scheduling queues..." in Nsight Systems Project Settings.

**VRAM Resource Types Distribution**

   :alt: VRAM Resource Types Distribution
   :class: image

This row shows the distribution of VRAM usage across different resource types per process. it
is color-coded to show the different resource types, and the height of each segment corresponds
to the amount of VRAM used by that resource type.
Expand the chart's parent row to expose detailed separate rows for individual resource categories.

The events will be captured if "Collect WDDM Trace" is enabled along with either "Collect WDDM memory trace"
or "Extensive trace including Hardware Scheduling queues..." in the Nsight Systems Project Settings.
Additionally, to correlate Graphics API debug name events with resource migration events, the "Collect DX12"
or "Collect Vulkan" option should be enabled.
