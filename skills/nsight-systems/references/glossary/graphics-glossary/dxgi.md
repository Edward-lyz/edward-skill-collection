# DXGI

**Short:** DirectX Graphics Infrastructure, the Windows layer that owns adapters, outputs, factories, and swap chains and brokers presentation for Direct3D 11 / Direct3D 12.

**Details:**

- DXGI is presentation and display plumbing used by Direct3D: it enumerates GPUs and displays (``IDXGIFactory``, ``IDXGIAdapter``, ``IDXGIOutput``), brokers fullscreen state, and owns the swap chain that puts pixels on screen via ``Present`` / ``Present1``.
- Present-side events bracket the API-thread side of ``Present``: ``Present_Start`` / ``Present_Stop`` carry the swap-chain pointer, target window, present flags, sync interval, and the present id; the Stop event reports the returned HRESULT.
- ``Present_MultiplaneOverlay_Start`` / ``_Stop`` describe DWM / DirectFlip optimized presents, useful for distinguishing composed vs flip-model presents.
- Swap-chain lifecycle surfaces through ``SwapChain_Start`` / ``_Stop``, ``ResizeBuffers_Start`` / ``_Stop``, and ``FullscreenState_Start`` / ``_Stop``.
- DXGI events live in the API thread context, so they sit alongside the application call stack. GPU-side work shows up later as DxgKrnl queue / DMA packets and finally a VSync flip.

**See also:**

- [DX12](dx12.md)
- [Swap chain](swap-chain.md)
- [Command list and queue](command-list-queue.md)
- [Frame boundary / Present](frame-boundary-present.md)
- [ETW](etw.md)
