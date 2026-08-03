# Parquet export

**Short:** A ``*_pqtdir/`` directory produced by ``nsys export -t parquetdir``, containing one ``.parquet`` file per event table. Best format for columnar analysis pipelines.

**Details:**

- Each ``.parquet`` file inside the directory holds one event table (e.g. ``NVTX_EVENTS.parquet``, ``DX12_API.parquet``, ``VULKAN_MEMORY_OPERATION.parquet``), plus a shared ``StringIds.parquet`` lookup that almost every text column references.
- Parquet is an industry-standard compressed columnar format readable by pandas, Polars, DuckDB, Apache Arrow, Spark, and most data-analysis tools.
- Column-projected reads make it efficient for analytical queries that touch only a few columns of large tables.
- The Arrow directory format (``arrowdir``) is structurally identical but uses ``.arrow`` files instead — choose based on the consumer.
- Same schema and same ``StringIds`` join model as the SQLite export. See [Export tables](export-tables.md) for the full table catalog.

**See also:**

- [Export](export.md)
- [SQLite export](sqlite-export.md)
- [Export tables](export-tables.md)
- [Report file](report-file.md)
