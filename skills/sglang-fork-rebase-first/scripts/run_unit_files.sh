#!/bin/bash
# Run the CPU unit tests of the touched subsystems file by file inside a container that
# carries the built delivery image (a deployed P/D pod works). One file per pytest process
# with its own timeout: a whole-directory run stops at the first collection error and one
# hanging file (network, GPU) hides every result behind it.
#
#   run_unit_files.sh [OUT_DIR] [DIRS...]     # run inside the container
#
# Results: OUT_DIR/summary.txt (one line per file), OUT_DIR/failed.txt (FAILED ids), OUT_DIR/*.log.
# Keep OUT_DIR on a volume that survives a container restart (/shared in the EPD YAMLs): a
# pod whose startup probe keeps failing restarts every ~50 min and wipes /tmp.
OUT=${1:-/shared/ut}; shift
DIRS=${*:-"entrypoints function_call managers disaggregation parser observability"}
TIMEOUT=${UT_TIMEOUT:-240}; PAR=${UT_PARALLEL:-6}
cd "${SGLANG_ROOT:-/sgl-workspace/sglang}/test/registered/unit" || exit 2
mkdir -p "$OUT"; rm -f "$OUT"/*.txt
for d in $DIRS; do ls "$d"/test_*.py 2>/dev/null; done > "$OUT/files.lst"
run_one() {
  f=$1; n=$(echo "$f" | tr / _)
  timeout "$UT_TIMEOUT" python3 -m pytest "$f" -q -rf -p no:cacheprovider > "$UT_OUT/$n.log" 2>&1; rc=$?
  echo "$f rc=$rc $(grep -E ' passed| failed| error' "$UT_OUT/$n.log" | tail -1)" >> "$UT_OUT/summary.txt"
  grep -E '^FAILED|^ERROR' "$UT_OUT/$n.log" | cut -c1-220 >> "$UT_OUT/failed.txt"
}
export -f run_one; export UT_TIMEOUT=$TIMEOUT UT_OUT=$OUT
xargs -P "$PAR" -I{} bash -c 'run_one {}' < "$OUT/files.lst"
echo ALLDONE >> "$OUT/summary.txt"
