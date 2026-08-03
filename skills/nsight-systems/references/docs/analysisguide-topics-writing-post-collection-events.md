---
source_path: AnalysisGuide/topics/writing-post-collection-events.rst
title: Writing Post-Collection Events
---
# Writing Post-Collection Events

The ``nsys_writer`` Python module writes NVTX events to a ``.nsys-rep`` file
during post-collection analysis. It can augment Nsight Systems reports with
analysis results or data from external profiling sources.

``nsys_writer`` is the Nsight Systems integration for the ``nvtx.writer``
module. For the writer object model and API, see `NVTX Python Writer
<https://nvidia.github.io/NVTX/python/writer.html>`__.

## Set up the writer

Install ``nvtx`` version 0.2.16 or later in the Python environment that will
run ``nsys_writer``. For the default Linux ``nsys recipe`` environment, after
the environment has been created, run:


   $HOME/.nsightsystems/venv/bin/python -m pip install "nvtx>=0.2.16"

For another recipe environment or a standalone script, use the Python
executable for that environment.

When ``nsys_writer`` is used from an ``nsys recipe``, Nsight Systems
automatically selects the writer backend.

For a standalone Python script, install ``nsys_writer`` package
in the Python environment. For example, on Linux x86-64:


   /path/to/python -m pip install <nsys-install-folder>/target-linux-x64/python/packages/nsys_writer

Also set the ``NSYS_WRITER_BACKEND`` environment variable to the
Nsight Systems writer backend library. For example, on Linux:


   export NSYS_WRITER_BACKEND=<nsys-install-folder>/host-linux-x64/libNvtxwBackend.so

On Windows, the backend library is named ``NvtxwBackend.dll``. The backend is
loaded when the first ``Session`` is created.

## Create a report

The following example uses the default UTC time base to write a
three-millisecond range to ``analysis.nsys-rep``. ``time.time_ns()`` provides
timestamps in nanoseconds since the Unix epoch:


   import time

   from nsys_writer import Session


   start = time.time_ns()
   with Session("analysis") as session:
       domain = session.get_domain("My Analysis")
       with session.create_stream("My Stream", domain=domain) as stream:
           stream.write_pushpop(
               start=start,
               end=start + 3_000_000,
               message="My Message",
               color="green",
           )

The session name determines the output path. Specify the desired path without
the ``.nsys-rep`` suffix.

## Add events to an existing report

Pass ``report_merge`` to copy an existing report and add events to the copy.
The session name determines the output path, which must differ from the
``report_merge`` path. Using the same path can truncate the source report on
Linux. With distinct paths, the original report is not modified. This example
creates ``profile-annotated.nsys-rep`` and places the range on a custom scope
for derived analysis results:


   from nsys_writer import Session, TimeBase


   with Session(
       name="profile-annotated",
       report_merge="profile.nsys-rep",
       time_base=TimeBase.RELATIVE,
   ) as session:
       domain = session.get_domain("Analysis Results")
       scope = domain.get_scope("Derived Analysis")
       with session.create_stream(
           "Post-Processing", domain=domain, scope=scope
       ) as stream:
           stream.write_pushpop(
               start=2_000_000,
               end=6_000_000,
               message="derived range",
           )

The ``report_merge`` path must identify an existing ``.nsys-rep`` file.

## Choose a timestamp base

Use a timestamp base that matches the source of the event timestamps:

* ``TimeBase.RELATIVE``: nanoseconds relative to the report analysis start.
* ``TimeBase.UTC`` (default): nanoseconds since the Unix epoch.
* ``TimeBase.CLOCK_MONOTONIC_RAW``: Linux ``CLOCK_MONOTONIC_RAW`` nanoseconds.
* ``TimeBase.CNTVCT``: ARM virtual counter ticks.

Use ``TimeBase.CLOCK_MONOTONIC_RAW`` or ``TimeBase.CNTVCT`` when merging into a
report that contains matching clock-conversion data.

## API reference

``nsys_writer.Session`` inherits the event, counter, schema, domain, scope, and
stream APIs from ``nvtx.writer.Session``.
``nsys_writer.Session.create_stream`` does not expose the stream ordering and
skid controls available in ``nvtx.writer.Session.create_stream`` because they
have no effect in this context.
For the complete API, including counter and batch-writing examples, see
the `NVTX Python Writer API reference
<https://nvidia.github.io/NVTX/python/writer_reference.html>`__.
