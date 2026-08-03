# Reflex render latency

**Short:** NVIDIA Reflex is a set of SDK markers that bracket the per-frame stages between input and on-screen photons so end-to-end render latency can be measured.

**Details:**

- Reflex breaks a frame into stages such as ``Input Sample``, ``Simulation``, ``Render Submit``, ``Present``, ``Driver``, ``OS Render Queue``, and ``GPU Render``. Secondary stages also exist (``OOB Render Submit``, ``OOB Present``, ``Late Warp Present``, ``Late Warp Submit``, ``PC Latency Ping``, ``Trigger Flash``, ``Camera Constructed``, ``Controller Input Sample``, ``Delta T Calculation``).
- Each stage is delimited by start and end markers carrying a frame identifier, which lets a tool reconstruct exactly which work belongs to which frame.
- End-to-end render latency is the time from the input that drove a frame until the resulting image is scanned out to the display.
- Reflex also exposes a low-latency mode that paces the CPU so it does not run far ahead of the GPU, shrinking the input-to-display window.
- Latency is most visible in fast, aim-driven games, where even a few milliseconds change how responsive the controls feel.
- Because the markers are per-stage, they make it possible to attribute latency to a specific stage rather than guessing from the overall frame time.

**See also:**

- [NVTX domain](../nsys-glossary/nvtx-domain.md)
- [NVTX range](../nsys-glossary/nvtx-range.md)
- [FPS and frame time](fps-frame-time.md)
- [Graphics frame](graphics-frame.md)
