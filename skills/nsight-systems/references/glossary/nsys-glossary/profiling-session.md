# Profiling session

**Short:** The bounded period during which Nsight Systems is actively collecting data from a target application; one session produces one ``.nsys-rep`` report.

**Details:**

- Has an ID, an optional name (published as the ``NSYS_SESSION_NAME`` environment variable for callback scripts), a state, and a wall-clock duration recorded in the report's ``TARGET_INFO_SESSION_START_TIME`` and ``ANALYSIS_DETAILS`` tables.
- The self-contained ``nsys profile`` command creates and tears down a session implicitly. The interactive ``nsys launch`` / ``start`` / ``stop`` commands operate on a session explicitly, selectable with ``--session=<name|id>``.
- The GUI's Analysis Summary view surfaces session metadata under "Profiling session information" — capture time, duration, host info, and report file.
- Sometimes called a *trace session* or *collection session* in different parts of the docs; the concept is the same.

**See also:**

- [Report file](report-file.md)
- [Collection commands](collection-commands.md)
- [Nsight Systems event](nsys-event.md)
- [nsys-ui](nsys-ui.md)
