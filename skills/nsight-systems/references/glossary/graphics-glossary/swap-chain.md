# Swap chain

**Short:** The ring of back buffers that the windowing system rotates each frame so the application can render to one image while another is displayed.

**Details:**

- On Windows, swap chains are owned by DXGI (``IDXGISwapChain``) and shared across D3D11, D3D12, and other clients; on Vulkan the equivalent is ``VkSwapchainKHR`` provided by the WSI extension.
- Present is the frame boundary: ``IDXGISwapChain::Present``, ``Present1``, and ``vkQueuePresentKHR`` hand the current back buffer to the compositor and advance to the next image.
- Common swap effects are ``FLIP_SEQUENTIAL`` and ``FLIP_DISCARD`` on Windows; flip-model swap chains bypass the legacy blit path and are required for tear-free and HDR presentation.
- Sync interval and present flags control V-sync behavior and tearing (e.g., ``ALLOW_TEARING``), determining whether Present blocks and how frame pacing behaves.
  Waitable swap chains, however, are configured independently at creation time via ``DXGI_SWAP_CHAIN_FLAG_FRAME_LATENCY_WAITABLE_OBJECT``, not through present flags.
- ``ResizeBuffers`` reallocates the back buffer ring when the window changes size or format; all outstanding references must be released first.

**See also:**

- [DX12](dx12.md)
- [DXGI](dxgi.md)
- [Frame boundary / Present](frame-boundary-present.md)
- [FPS and frame time](fps-frame-time.md)
