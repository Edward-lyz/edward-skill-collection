# Sampling marks

**Short:** Small marks on the GUI timeline indicating points where Nsight Systems captured a CPU call stack. Orange = periodic sampling, grey = stacks captured opportunistically from other sources.

**Details:**

- **Orange marks** — Periodic sampling stacks, sourced from ``SAMPLING_CALLCHAINS``. The primary signal for CPU hotspot analysis.
- **Grey marks** — Stacks captured from other event sources (ETW events on Windows, event-based sampling on Linux). Less uniform in time but informative around specific events.
- Hovering a mark reveals the captured stack in a tooltip; clicking pins it for navigation.
- The ``gfx_hotspot`` recipe distinguishes these as "Periodic Sampled Call stacks" (orange-only) vs "All Call stacks" (orange + grey).

**See also:**

- [CPU sampling](cpu-sampling.md)
- [Trace vs. sample](trace-vs-sample.md)
- [Nsight Systems timeline](nsys-timeline.md)
- [ETW](../graphics-glossary/etw.md)
