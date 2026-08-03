# Graphics Glossary

Progressively discoverable reference for graphics-dev terms as they show up in the QuadD / Nsight Systems codebase. Each entry is one Markdown (.md) file: open the file for a short definition, the concept in plain language, common nuances, and links to related terms.

This index lists terms grouped by area. Each link is a one-line hook; click through for the full entry.

For Nsight Systems-specific vocabulary (commands, file formats, GUI elements, recipes), see the sibling [nsys-glossary](../nsys-glossary/index.md).

## Conventions

- Each entry starts with a one-line **Short** definition.
- **Details** gives 2 to 6 short bullets covering the concept itself; entries do not reference QuadD source code, file paths, or class names.

- **See also** lists related entries for quick navigation.
- Entries are concept-level and tool-agnostic; the QuadD code is the source of truth for implementation specifics.

## Frames and timing

- [graphics-frame.md](graphics-frame.md) - one iteration of an app's render loop
- [frame-boundary-present.md](frame-boundary-present.md) - Present / SwapBuffers as the canonical frame boundary
- [cpu-bound.md](cpu-bound.md) - frame whose end is gated by CPU work
- [gpu-bound.md](gpu-bound.md) - frame whose end is gated by GPU work
- [gpu-bubble.md](gpu-bubble.md) - idle gap on a GPU engine while work is pending elsewhere
- [stutter.md](stutter.md) - frame-time spike that breaks pacing even when average FPS is fine
- [reflex-render-latency.md](reflex-render-latency.md) - Reflex SDK markers and sim / render / present latency chain
- [reflex-sdk-row.md](reflex-sdk-row.md) - GUI timeline row visualizing Reflex SDK latency markers
- [vsync.md](vsync.md) - vertical-blank sync
- [fps-frame-time.md](fps-frame-time.md) - frame rate and frame-duration metrics

## Graphics APIs

- [dx12.md](dx12.md) - Direct3D 12: explicit Windows graphics + compute API
- [dx11.md](dx11.md) - Direct3D 11: previous-generation Windows graphics API
- [vulkan.md](vulkan.md) - Khronos cross-platform explicit graphics + compute API
- [opengl.md](opengl.md) - Khronos legacy state-machine graphics API
- [graphics-pipeline.md](graphics-pipeline.md) - shader stages from input assembly to output merger
- [command-list-queue.md](command-list-queue.md) - D3D12 command list / queue / bundle model
- [vulkan-command-buffer.md](vulkan-command-buffer.md) - Vulkan analogue of a D3D12 command list
- [pso.md](pso.md) - pipeline state object: compiled bundle of shaders + fixed-function state
- [fence.md](fence.md) - GPU / CPU sync primitive in D3D12 and Vulkan
- [barrier.md](barrier.md) - resource state / pipeline barriers between GPU work
- [swap-chain.md](swap-chain.md) - DXGI / Vulkan back-buffer rotation
- [present-mode.md](present-mode.md) - FIFO / Mailbox / Immediate / flip vs blit
- [dxgi.md](dxgi.md) - DirectX Graphics Infrastructure and its ETW events
- [render-target.md](render-target.md) - render target view / framebuffer attachment
- [low-level-api.md](low-level-api.md) - umbrella for D3D12, Vulkan, D3D11

## ETW, WDDM, and GPU scheduling

- [etw.md](etw.md) - Event Tracing for Windows
- [etw-provider-mask.md](etw-provider-mask.md) - provider keyword + level bitmask
- [dxgkrnl-events.md](dxgkrnl-events.md) - DirectX graphics kernel ETW events (catalog)
- [wddm.md](wddm.md) - Windows Display Driver Model
- [vidmm-vidsch.md](vidmm-vidsch.md) - WDDM video memory manager and scheduler
- [gpu-context-switch.md](gpu-context-switch.md) - GPU scheduler swapping graphics contexts on an engine
- [gpu-engine.md](gpu-engine.md) - the 3D / Compute / Copy / Video decode / Video encode engines
- [queue-packet.md](queue-packet.md) - dxgkrnl software-queue packet
- [dma-packet.md](dma-packet.md) - GPU engine DMA packet
- [hardware-queue.md](hardware-queue.md) - WDDM 2.7+ hardware-scheduled GPU queue

## GPU memory and resources

- [memory-transfer.md](memory-transfer.md) - SystemToDevice / DeviceToSystem / DeviceToDevice copies; pinned vs pageable
- [resource-migration.md](resource-migration.md) - moving an allocation between memory segments

## Perf markers

- [debug-marker.md](debug-marker.md) - PIX and Vulkan debug-utils labels

For NVTX primitives (domain, range, mark, payload, category, NVTXT) and the ``perf-marker`` umbrella, see the NVTX section of the sibling [nsys-glossary](../nsys-glossary/index.md).
