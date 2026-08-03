# GPU engine

**Short:** A GPU engine is one of the named hardware queues a GPU exposes for a specific class of work: 3D, Compute, Copy, Video Decode, Video Encode, and vendor-specific variants.

**Details:**

- Each engine takes its own command stream and runs largely in parallel, so a frame can rasterize on the 3D engine while a Copy engine moves a texture and Video Decode produces frames for a media surface.
- Engines are addressed by an engine type (a fixed enum: ``3D``, ``Compute``, ``Copy``, ``Video decode``, ``Video encode``, ``Video processing``, ``Scene assembly``, ``Overlay``, ``Crypto``, ``Other``) and a node ordinal distinguishing physical instances, since modern GPUs ship multiple copy or compute engines.
- The OS scheduler tracks utilization, preemption, and residency per engine; a profiler renders one row per (engine type, node ordinal) so users can spot under-used engines or serialization across them.
- D3D12 and Vulkan queues map onto engines: a Direct queue targets 3D, a Compute queue targets Compute, a Copy queue targets Copy. The mapping is set by the driver.
- Engine names shown to users often come from a friendly-name string the driver reports.

**See also:**

- [WDDM](wddm.md)
- [DxgKrnl events](dxgkrnl-events.md)
- [Command list / queue](command-list-queue.md)
