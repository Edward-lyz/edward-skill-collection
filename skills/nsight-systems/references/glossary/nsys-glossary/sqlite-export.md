# SQLite export

**Short:** A ``.sqlite`` database produced by ``nsys export -t sqlite``. The default export format, and the substrate for ``nsys stats``, ``nsys analyze``, and most recipes.

**Details:**

- Auto-generated (cached next to the ``.nsys-rep``) the first time ``stats``, ``analyze``, or ``recipe`` runs against the report. Force a re-export with ``--force-export``.
- One table per event source (``NVTX_EVENTS``, ``DX12_API``, ``CUPTI_ACTIVITY_KIND_KERNEL``, ``OSRT_API``, ``WDDM_*``, ``ETW_EVENTS``, ``GPU_METRICS``, etc.). See [Export tables](export-tables.md) for the full catalog.
- Almost every text column is an integer ID into a central ``StringIds`` table — joins are needed to resolve names.
- Schema is not forward-compatible: check ``META_DATA_EXPORT.EXPORT_SCHEMA_VERSION``. Per-version notes live at ``<install_dir>/host*/exporter/export_schema_version_notes.txt``.
- Lazy by default (only non-empty tables are created); pass ``--lazy=false`` to emit every table even when empty.

**See also:**

- [Export](export.md)
- [Export tables](export-tables.md)
- [Parquet export](parquet-export.md)
- [Report file](report-file.md)
