# Collection commands

**Short:** Two ways to start capturing data into a ``.nsys-rep``: the one-shot ``nsys profile``, or the interactive ``nsys launch`` + ``start`` + ``stop`` sequence.

**Details:**

- ``nsys profile`` — Self-contained one-shot collection. Launches the target app, collects according to its switches, writes the report when the app exits or the capture range ends. The common case.
- ``nsys launch`` **+** ``nsys start`` **+** ``nsys stop`` — Interactive lifecycle. ``launch`` prepares the app inside a profiling session, ``start`` toggles collection on, ``stop`` ends it. Useful when collection start / end need external control (driven by a script, attached to an already-running scenario, etc.).
- Common switch families on ``profile``: trace selection (``-t cuda,nvtx,vulkan,dx12,opengl,osrt,wddm,...``), sampling (``--sample``, ``--cpuctxsw``, ``--backtrace``), GPU metrics (``--gpu-metrics-devices``), output (``-o``, ``--auto-report-name``).
- All four commands operate on a profiling session; ``--session=<name|id>`` selects a specific session in the interactive flow when multiple are active.

**See also:**

- [Profiling session](profiling-session.md)
- [Report file](report-file.md)
- [nsys-ui](nsys-ui.md)
