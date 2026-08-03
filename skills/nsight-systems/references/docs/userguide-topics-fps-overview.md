---
source_path: UserGuide/topics/fps-overview.rst
title: ## FPS Overview
---
## FPS Overview

The Frame Duration section displays frame durations on both the CPU and the GPU.

      :alt: FPS overview
      :class: image

The frame duration row displays live FPS statistics for the current timeline viewport. Values shown are:

#. Number of CPU frames shown of the total number captured.

#. Average, minimal, and maximal CPU frame time of the currently displayed time range.

#. Average FPS value for the currently displayed frames.

#. The 99th percentile value of the frame lengths (such that only 1% of the frames in the range are longer than this value).

The values will update automatically when scrolling, zooming or filtering the timeline view.

..

      :alt: FPS stutter row
      :class: image

The stutter row highlights frames that are significantly longer than the other frames in their immediate vicinity.

The stutter row uses an algorithm that compares the duration of each frame to the median duration of the surrounding 19 frames. Duration difference under 4 milliseconds is never considered a stutter, to avoid cluttering the display with frames whose absolute stutter is small and not noticeable to the user.

For example, if the stutter threshold is set at 20%:

#. Median duration is 10 ms. Frame with 13 ms time will not be reported (relative difference > 20%, absolute difference < 4 ms).

#. Median duration is 60 ms. Frame with 71 ms time will not be reported (relative difference < 20%, absolute difference > 4 ms).

#. Median duration is 60 ms. Frame with 80 ms is a stutter (relative difference > 20%, absolute difference > 4 ms, both conditions met).

**OSC detection**

The "19 frame window median" algorithm by itself may not work well with some cases of "oscillation" (consecutive fast and slow frames), resulting in some false positives. The median duration is not meaningful in cases of oscillation and can be misleading.

To address the issue and identify if oscillating frames, the following method is applied:

#. For every frame, calculate the median duration, 1st and 3rd quartiles of 19-frames window.

#. Calculate the delta and ratio between 1st and 3rd quartiles.

#. If the 90th percentile of 3rd - 1st quartile delta array > 4 ms AND the 90th percentile of 3rd/1st quartile array > 1.2 (120%) then mark the results with "OSC" text.

Right-clicking the Frame Duration row caption lets you choose the target frame rate (30, 60, 90 or custom frames per second).

   :alt: FPS pick
   :class: image

By clicking the **Customize FPS Display** option, a customization dialog pops up. In the dialog, you can now define the frame duration threshold to customize the view of the potentially problematic frames. In addition, you can define the threshold for the stutter analysis frames.

   :alt: fps_customizations
   :class: image

Frame duration bars are color-coded:

-  Green, the frame duration is shorter than required by the target FPS ratio.

-  Yellow, duration is slightly longer than required by the target FPS rate.

-  Red, duration far exceeds that required to maintain the target FPS rate.

   :alt: Bad FPS
   :class: image

The CPU Frame Duration row displays the CPU frame duration measured between the ends of consecutive frame boundary calls:

-  The OpenGL frame boundaries are ``eglSwapBuffers/glXSwapBuffers/SwapBuffers`` calls.

-  The D3D11 and D3D12 frame boundaries are ``IDXGISwapChainX::Present`` calls.

-  The Vulkan frame boundaries are ``vkQueuePresentKHR`` calls.

The timing of the actual calls to the frame boundary calls can be seen in the blue bar at the bottom of the CPU frame duration row

The GPU Frame Duration row displays the time measured between:

-  The start time of the first GPU workload execution of this frame.

-  The start time of the first GPU workload execution of the next frame.

**Reflex SDK**

NVIDIA Reflex SDK is a series of NVAPI calls that allow applications to integrate the Ultra Low Latency driver feature more directly into their game to further optimize synchronization between simulation and rendering stages and lower the latency between user input and final image rendering. For more details about Reflex SDK, see the Reflex SDK Site .

Nsight Systems will automatically capture NVAPI functions when either Direct3D 11, Direct3D 12, or Vulkan API trace are enabled.

The Reflex SDK row displays timeline ranges for the following types of latency markers:

-  RenderSubmit

-  Simulation

-  Present

-  Driver

-  OS Render Queue

-  GPU Render

   :alt: Reflex SDK
   :class: image

**Performance Warnings row**

This row shows performance warnings and common pitfalls that are automatically detected based on the enabled capture types. Warnings are reported for:

-  ETW performance warnings.

-  Vulkan calls to ``vkQueueSubmit`` and D3D12 calls to ``ID3D12CommandQueue::ExecuteCommandList`` that take a longer time to execute than the total time of the GPU workloads they generated.

-  D3D12 Memory Operation warnings .

-  Usage of Vulkan API functions that may adversely affect performance.

-  Creation of a Vulkan device with memory zeroing, whether by physical device default or manually.

-  Vulkan command buffer barrier which can be combined or removed, such as subsequent barriers or read-to-read barriers.

   :alt: Performance Warnings row
   :class: image
