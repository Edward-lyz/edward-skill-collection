# VSync

**Short:** Vertical-blank synchronization; the display refresh boundary at which a new scanout begins.

**Details:**

- A display refreshes at a fixed rate, and the vertical blank is the brief interval between scanning out one image and starting the next.
- VSync ties the present of a new frame to that boundary so the display never shows two frames stitched together, which would appear as tearing.
- The cost is added latency and frame-time quantization: a frame that misses the boundary waits a full refresh interval before being shown.
- Variable refresh rate displays relax this by letting the display wait for the GPU within a range, removing most of the wait without tearing.
- Each connected display has its own VSync cadence, so multi-monitor setups can have several independent timelines.
- Lining VSync events up with CPU and GPU frame timings is the standard way to diagnose stutter, dropped frames, and present-time hitches.

**See also:**

- [DxgKrnl events](dxgkrnl-events.md)
- [WDDM](wddm.md)
- [Graphics frame](graphics-frame.md)
- [FPS and frame time](fps-frame-time.md)
