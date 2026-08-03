# GPU context switch

**Short:** A GPU context switch is the point at which the OS GPU scheduler suspends one graphics context running on a GPU engine and resumes another, analogous to a CPU thread context switch but at the engine level.

**Details:**

- A graphics context represents one client's view of a GPU engine: its command stream, residency set, and synchronization state. Many contexts compete for time on the same engine.
- On WDDM, the OS scheduler grants each context a quantum on an engine and swaps it out, recording transitions like idle, ready, running, and ready-standby.
- Each transition is visible in ETW as a scheduling-log event carrying the engine type and node ordinal, so a profiler can show a per-engine timeline of which process owned the GPU when.
- Frequent or long switches on the 3D engine usually mean contention between an application, the compositor, and background GPU work; they are a common cause of frame-time stutter that is invisible to CPU-only profiling.
- With hardware-scheduled GPUs the switch happens on the GPU itself, but state changes are still reported through the same events.

**See also:**

- [WDDM](wddm.md)
- [DxgKrnl events](dxgkrnl-events.md)
- [VidMm / VidSch](vidmm-vidsch.md)
- [ETW](etw.md)
