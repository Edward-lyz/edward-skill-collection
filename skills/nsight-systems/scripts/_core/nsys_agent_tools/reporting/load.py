"""Report input loading and private export/cache preparation."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..tabular_tables import safe_table_name as _safe_table_name
from ..tabular_tables import unique_table_name as _unique_table_name
from .cache_events import cache_event, cache_timer_start, elapsed_ms
from .cache_keys import multi_report_cache_key
from .cache_manifest import write_duckdb_cache_manifest
from .duckdb_backend import _import_duckdb
from .file_utils import file_lock, safe_child_files
from .parquet_cache import build_report_duckdb, prepare_parquet_exports
from .sql_utils import _execute_identifier_sql, _quote_identifier, _sql_string
from .types import ReportError, ReportSession

if TYPE_CHECKING:
    from .runtime import ReportRuntime


def load_report(runtime: ReportRuntime, report: str | Path) -> ReportSession:
    path = Path(report).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path.name)
    suffix = path.suffix.lower()
    if suffix == ".sqlite":
        return ReportSession(path, path, "sqlite")
    if path.is_dir():
        nsys_reports = safe_child_files(path, "*.nsys-rep")
        if nsys_reports:
            if len(nsys_reports) > runtime.max_reports:
                raise ReportError(
                    "Directory contains "
                    f"{len(nsys_reports)} reports, above the configured limit of "
                    f"{runtime.max_reports}. Use a narrower directory or configure a "
                    "larger report limit for this runtime."
                )
            return ReportSession(path, None, "directory_nsys_reports", multi_reports=tuple(nsys_reports))
        sqlite_files = safe_child_files(path, "*.sqlite")
        if len(sqlite_files) == 1:
            return ReportSession(path, sqlite_files[0], "directory_sqlite")
        parquet_files = safe_child_files(path, "*.parquet")
        csv_files = safe_child_files(path, "*.csv")
        if parquet_files or csv_files:
            return load_parquet_dir(runtime, path)
        if sqlite_files:
            raise ReportError(
                "Directory contains multiple exported SQLite files. Prefer passing a native "
                f".nsys-rep report or a directory of .nsys-rep reports: {path.name}"
            )
        raise ReportError(
            "Directory does not contain a native .nsys-rep report or an advanced exported "
            f"SQLite/Parquet/CSV report artifact: {path.name}"
        )
    if suffix in {".parquet", ".csv"}:
        return load_tabular_files(
            runtime,
            input_path=path,
            tabular_files=[path],
            source="tabular_file_duckdb",
            parquet_root=path.parent,
        )
    if suffix == ".nsys-rep":
        return ReportSession(path, None, "native_report", report_count=1)
    raise ReportError(f"Unsupported report input: {path.name}")


def load_native_report_duckdb(
    runtime: ReportRuntime,
    report: Path,
    *,
    table_patterns: tuple[str, ...] = (),
) -> ReportSession:
    """Prepare a native single `.nsys-rep` query backend on demand."""

    start = cache_timer_start()
    base_key = multi_report_cache_key((report,), runtime.nsys_path)
    export_root = runtime.cache_dir / f"report-{base_key}-parquet"
    lock_path = runtime.cache_dir / f"report-{base_key}.lock"
    if table_patterns:
        full_db_path = runtime.cache_dir / f"report-{base_key}.duckdb"
        full_manifest_path = full_db_path.with_suffix(full_db_path.suffix + ".manifest.json")
        if full_db_path.is_file() and full_manifest_path.is_file():
            return _native_report_session(
                report,
                full_db_path,
                export_root,
                cache_event("duckdb_cache", hit=True, start=start, scoped=False),
            )
    key = multi_report_cache_key((report,), runtime.nsys_path, table_patterns=table_patterns)
    db_path = runtime.cache_dir / f"report-{key}.duckdb"
    manifest_path = db_path.with_suffix(db_path.suffix + ".manifest.json")
    if db_path.is_file() and manifest_path.is_file():
        return _native_report_session(
            report,
            db_path,
            export_root,
            cache_event("duckdb_cache", hit=True, start=start, scoped=bool(table_patterns)),
        )
    lock_start = cache_timer_start()
    with file_lock(lock_path, timeout_s=runtime.cache_lock_timeout_s(1)):
        lock_wait_ms = elapsed_ms(lock_start)
        built = False
        if not db_path.is_file():
            exports = prepare_parquet_exports(
                runtime,
                (report,),
                export_root,
                table_patterns=table_patterns,
            )
            build_report_duckdb(db_path, exports)
            built = True
        if built or not manifest_path.is_file():
            write_duckdb_cache_manifest(
                manifest_path,
                nsys_path=runtime.nsys_path,
                inputs=[report],
                db_path=db_path,
                export_type="native-report-parquet-duckdb",
            )
    return _native_report_session(
        report,
        db_path,
        export_root,
        cache_event(
            "duckdb_cache",
            hit=not built,
            start=start,
            scoped=bool(table_patterns),
            lock_wait_ms=lock_wait_ms,
        ),
    )


def load_parquet_dir(runtime: ReportRuntime, directory: Path) -> ReportSession:
    parquet_files = safe_child_files(directory, "*.parquet")
    csv_files = safe_child_files(directory, "*.csv")
    tabular_files = [*parquet_files, *csv_files]
    if not tabular_files:
        raise ReportError(f"No parquet or CSV files found under {directory.name}")
    return load_tabular_files(
        runtime,
        input_path=directory,
        tabular_files=tabular_files,
        source="parquet_duckdb",
        parquet_root=directory,
    )


def load_tabular_files(
    runtime: ReportRuntime,
    *,
    input_path: Path,
    tabular_files: list[Path],
    source: str,
    parquet_root: Path,
) -> ReportSession:
    duckdb = _import_duckdb()
    key = hashlib.sha256(
        "|".join(
            f"{input_path}:{p.name}:{p.stat().st_mtime_ns}:{p.stat().st_size}"
            for p in tabular_files
        ).encode()
    ).hexdigest()[:16]
    db_path = runtime.cache_dir / f"parquet-{key}.duckdb"
    manifest_path = db_path.with_suffix(db_path.suffix + ".manifest.json")
    start = cache_timer_start()
    if db_path.is_file() and manifest_path.is_file():
        return ReportSession(
            input_path,
            None,
            source,
            duckdb_path=db_path,
            parquet_root=parquet_root,
            cache_events=(cache_event("duckdb_cache", hit=True, start=start, scoped=False),),
        )
    built = False
    if not db_path.is_file():
        with file_lock(
            db_path.with_suffix(db_path.suffix + ".lock"),
            timeout_s=runtime.cache_lock_timeout_s(1),
        ):
            if not db_path.is_file():
                tmp_db = db_path.with_suffix(".building.duckdb")
                if tmp_db.exists():
                    tmp_db.unlink()
                with duckdb.connect(str(tmp_db)) as con:
                    used_tables: set[str] = set()
                    for path in tabular_files:
                        table = _unique_table_name(_safe_table_name(path.stem), used_tables)
                        reader = "read_parquet" if path.suffix.lower() == ".parquet" else "read_csv_auto"
                        sql = (
                            "CREATE OR REPLACE TABLE "
                            + _quote_identifier(table)
                            + " AS SELECT * FROM "
                            + reader
                            + "("
                            + _sql_string(str(path))
                            + ")"
                        )
                        _execute_identifier_sql(con, sql)
                tmp_db.replace(db_path)
                built = True
    if built or not manifest_path.is_file():
        write_duckdb_cache_manifest(
            manifest_path,
            nsys_path=runtime.nsys_path,
            inputs=tabular_files,
            db_path=db_path,
            export_type=source,
        )
    return ReportSession(
        input_path,
        None,
        source,
        duckdb_path=db_path,
        parquet_root=parquet_root,
        cache_events=(cache_event("duckdb_cache", hit=not built, start=start, scoped=False),),
    )


def _native_report_session(
    report: Path,
    db_path: Path,
    export_root: Path,
    cache_event: dict[str, Any],
) -> ReportSession:
    return ReportSession(
        report,
        None,
        "nsys_export_parquet_duckdb",
        duckdb_path=db_path,
        parquet_root=export_root,
        report_count=1,
        cache_events=(cache_event,),
    )
