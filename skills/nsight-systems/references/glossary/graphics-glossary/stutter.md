# Stutter

**Short:** A perceptible hitch in frame pacing: one or more frames take significantly longer than the steady state, so the image on screen jerks even if average frame rate looks healthy.

**Details:**

- Stutter is about variance, not average. A 60 FPS average with a single 100 ms frame is more disruptive than a steady 50 FPS, because the eye latches onto the discontinuity.
- Common causes inside the engine: shader compilation on first use (PSO cache miss), asset streaming, and allocator or GC pauses.
- Common causes outside the engine: VidMm paging an evicted resource back in, a GPU context switch caused by another foreground app, and vsync interaction when frame time straddles the vblank interval.
- Frame-pacing strategies (capping at a fraction of the refresh rate, Reflex, decoupled simulation and render) smooth the delivery cadence.
- A stutter shows up as a spike in the frame-time row plus a long CPU range or GPU bubble on the responsible thread or engine; the matching stack identifies the culprit.

**See also:**

- [Frame boundary / Present](frame-boundary-present.md)
- [FPS and frame time](fps-frame-time.md)
- [CPU bound](cpu-bound.md)
- [GPU bound](gpu-bound.md)
- [Reflex render latency](reflex-render-latency.md)
