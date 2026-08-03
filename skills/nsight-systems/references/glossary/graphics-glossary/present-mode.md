# Present mode

**Short:** How a Present call interacts with the swap chain and the display, controlling buffering, tearing, and pacing.

**Details:**

- DXGI offers a legacy blit model and a modern flip model; flip lets the desktop compositor scan out the back buffer directly, enabling lower latency and Independent Flip.
- DXGI swap effects include ``DXGI_SWAP_EFFECT_FLIP_DISCARD`` and ``DXGI_SWAP_EFFECT_FLIP_SEQUENTIAL`` (flip model) and the older ``DXGI_SWAP_EFFECT_DISCARD`` and ``DXGI_SWAP_EFFECT_SEQUENTIAL`` (blit model).
- Vulkan present modes include ``VK_PRESENT_MODE_FIFO_KHR`` (vsync, no tearing), ``VK_PRESENT_MODE_MAILBOX_KHR`` (replace pending image, no tearing), ``VK_PRESENT_MODE_IMMEDIATE_KHR`` (tearing allowed), and ``VK_PRESENT_MODE_FIFO_RELAXED_KHR`` (tear only on late frames).
- Independent Flip bypasses the Desktop Window Manager so the swap chain image is scanned out directly, and Multi-Plane Overlay (MPO) lets the display engine composite multiple planes in hardware.
- A presented frame is first queued at the runtime, then handed to the driver/kernel queue, then scanned out at vsync; profiling distinguishes these stages because latency and bubbles can appear at any of them.

**See also:**

- [Swap chain](swap-chain.md)
- [DXGI](dxgi.md)
- [Vsync](vsync.md)
- [Frame boundary / Present](frame-boundary-present.md)
- [Reflex render latency](reflex-render-latency.md)
