# nsys-ui

**Short:** The Nsight Systems GUI executable. Loads a ``.nsys-rep`` and renders the interactive timeline view.

**Details:**

- Main view is the timeline: hierarchy of rows on the left, charts on the right. See [Nsight Systems timeline](nsys-timeline.md) for the GUI vocabulary.
- Headless screenshot mode renders the timeline to an image without opening the full GUI: ``nsys-ui --screenshot report.nsys-rep``. Useful for automated pipelines or visual diffs from a CLI.
- Hovering an element opens a tooltip with parameters, call stack, etc.; right-click → **Copy Tooltip** copies it to the clipboard — useful when asking the user for specific event details.

**See also:**

- [Report file](report-file.md)
- [Nsight Systems timeline](nsys-timeline.md)
