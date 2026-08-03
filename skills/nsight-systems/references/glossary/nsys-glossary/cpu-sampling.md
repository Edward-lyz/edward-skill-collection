# CPU sampling

**Short:** A profiling technique that periodically interrupts each CPU and records the program counter plus a call stack of whatever was running, then aggregates those snapshots statistically.

**Details:**

- The sampling rate (for example, 1 kHz per core) trades overhead against resolution: faster rates catch shorter functions but cost more.
- Unlike instrumentation, sampling does not modify the program; it estimates time by counting how often each function appears in stacks, so cost scales with cores, not function calls.
- Each sample is attributed to the thread on the core at the interrupt, so idle cores contribute idle samples and busy threads dominate naturally.
- Two well-known artifacts: aliasing, where a periodic workload synced to the sample rate is over- or under-counted, and skid, where the recorded program counter lags the actual hot instruction on out-of-order CPUs.
- Sampling shows only on-CPU code; time spent blocked or descheduled is invisible unless paired with thread-state tracing.
- Symbol and unwind quality decide whether samples land on meaningful function names or on raw addresses.

**See also:**

- [Thread state](thread-state.md)
- [Module view](module-view.md)
