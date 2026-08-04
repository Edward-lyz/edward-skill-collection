#!/usr/bin/env python3
"""Export CUDA kernel rows from an Nsight Systems report on a remote host.

The report is intentionally kept as CSV so the alignment builder can be run
without importing Nsight's Python bindings. Use the Nsight Systems version
available in the target development image; report names can differ slightly
between major releases.
"""

from __future__ import annotations

import argparse
import csv
import io
import subprocess
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("report", type=Path, help="input .nsys-rep")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--nsys", default="nsys")
    p.add_argument("--stats-report", default="cuda_gpu_kern_sum")
    p.add_argument("--start-ns", type=int)
    p.add_argument("--end-ns", type=int)
    args = p.parse_args()
    cmd = [args.nsys, "stats", "--force-export=true", "--format", "csv", "--report", args.stats_report, str(args.report)]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    rows = list(csv.reader(io.StringIO(proc.stdout)))
    if args.start_ns is not None or args.end_ns is not None:
        # Filtering is delegated to the generated CSV's timestamp column. The
        # raw export remains available when a report version changes columns.
        header = rows[0] if rows else []
        start_col = next((i for i, x in enumerate(header) if "start" in x.lower()), None)
        end_col = next((i for i, x in enumerate(header) if "end" in x.lower()), None)
        if start_col is not None and end_col is not None:
            kept = [rows[0]]
            for cells in rows[1:]:
                try:
                    s, e = int(float(cells[start_col])), int(float(cells[end_col]))
                except (ValueError, IndexError):
                    continue
                if (args.start_ns is None or e >= args.start_ns) and (args.end_ns is None or s <= args.end_ns):
                    kept.append(line)
            rows = kept
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)


if __name__ == "__main__":
    main()
