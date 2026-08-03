# Module view

**Short:** A profile aggregated by binary module - the main executable and each loaded shared library (DLL on Windows, .so on Linux, .dylib on macOS) - showing how much sampled CPU time landed inside each one.

**Details:**

- A useful first cut: before chasing individual symbols, see whether cost is in your code, a graphics driver, a runtime library, third-party middleware, or the kernel.
- Each row sums samples that resolved to addresses inside that module's loaded range, regardless of which function was running.
- Pairs naturally with a symbol view: pick a hot module, then drill into its hot functions; or filter call-tree views to one module to cut noise.
- Unwind-result counts here also reveal where stack capture struggled (a module shipped without unwind information), which explains gaps elsewhere.
- Modules without symbols collapse into a single anonymous bucket, so missing debug info hides structure rather than cost.

**See also:**

- [CPU sampling](cpu-sampling.md)
- [Thread state](thread-state.md)
