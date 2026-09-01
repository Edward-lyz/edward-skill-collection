#!/usr/bin/env bash
# Run every gate in this skill in one shot and print a summary that can be
# pasted into the review description.
#
# Required:
#   REPO         integration worktree
#   TARGET_SHA   frozen target/fork parent
#   SOURCE_SHA   frozen source/upstream parent
#   ARTIFACTS    output directory
# Optional:
#   FINAL_REV        merged revision; empty means the working tree
#   REVIEW_BASE_SHA  base the candidate must sit on for review_preflight
#                    (default TARGET_SHA; for a two-parent merge this is the
#                    frozen review branch tip, not the fork parent)
#   PATHS_FILE       files for interface/duplicate/absent gates (default: files
#                    both parents changed, capped by PATHS_LIMIT)
#   PATHS_LIMIT      cap on the derived paths file (default 400)
#   CRITICAL_PATHS   space-separated globs the delivery actually executes
#   DEPLOY_YAMLS     space-separated release YAMLs (flag safety net)
#   CONFIG_FILE      config dataclass file for flag_inventory
#   CONFIG_CLASS     config dataclass name (default ServerArgs)
#   TEST_COMMAND     repo test command with a {tree} placeholder
#   COLLECT_COMMAND  optional test-listing command with the same placeholder
#   CARD_PATTERN     ticket regex for review_preflight
#   FLAG_WAIVERS     dispositioned DROPPED/NO-OP flags: name<TAB>reason
#   SYMBOL_WAIVERS   dispositioned REAL-LOSS symbols: symbol<TAB>reason
#   MODE             pick or squash (default squash)
#   PYTHON           interpreter (default python3)
set -uo pipefail

: "${REPO:?set REPO}"
: "${TARGET_SHA:?set TARGET_SHA}"
: "${SOURCE_SHA:?set SOURCE_SHA}"
: "${ARTIFACTS:?set ARTIFACTS}"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
FINAL_REV="${FINAL_REV:-}"
PATHS_LIMIT="${PATHS_LIMIT:-400}"
CRITICAL_PATHS="${CRITICAL_PATHS:-}"
DEPLOY_YAMLS="${DEPLOY_YAMLS:-}"
CONFIG_FILE="${CONFIG_FILE:-python/sglang/srt/server_args.py}"
CONFIG_CLASS="${CONFIG_CLASS:-ServerArgs}"
TEST_COMMAND="${TEST_COMMAND:-}"
COLLECT_COMMAND="${COLLECT_COMMAND:-}"
CARD_PATTERN="${CARD_PATTERN:-}"
FLAG_WAIVERS="${FLAG_WAIVERS:-}"
SYMBOL_WAIVERS="${SYMBOL_WAIVERS:-}"
MODE="${MODE:-squash}"
REVIEW_BASE_SHA="${REVIEW_BASE_SHA:-$TARGET_SHA}"
mkdir -p "$ARTIFACTS"

final_args=()
[[ -n "$FINAL_REV" ]] && final_args=(--final "$FINAL_REV")

# Default review scope: files both parents touched. Those are the only places a
# three-way merge had to decide anything.
PATHS_FILE="${PATHS_FILE:-$ARTIFACTS/gate-paths.txt}"
if [[ ! -s "$PATHS_FILE" ]]; then
  git -C "$REPO" diff --name-only "$TARGET_SHA" "$SOURCE_SHA" -- "*.py" \
    | head -n "$PATHS_LIMIT" > "$PATHS_FILE"
fi

critical_args=()
for glob in $CRITICAL_PATHS; do critical_args+=(--critical-path "$glob"); done
deploy_args=()
for yaml in $DEPLOY_YAMLS; do deploy_args+=(--deploy-yaml "$yaml"); done
flag_waiver_args=()
[[ -n "$FLAG_WAIVERS" ]] && flag_waiver_args=(--waiver-file "$FLAG_WAIVERS")
symbol_waiver_args=()
[[ -n "$SYMBOL_WAIVERS" ]] && symbol_waiver_args=(--waiver-file "$SYMBOL_WAIVERS")

declare -a NAMES=() CODES=() FILES=()
record() { NAMES+=("$1"); CODES+=("$2"); FILES+=("$3"); }

run_gate() {
  local name="$1" out="$2"; shift 2
  echo "== $name"
  "$@" > "$out.stdout" 2>&1
  local code=$?
  tail -3 "$out.stdout"
  record "$name" "$code" "$out"
}

run_gate import-audit "$ARTIFACTS/import-audit.md" \
  "$PYTHON" "$SKILL_DIR/scripts/import_audit.py" --repo "$REPO" \
  --parent "$TARGET_SHA" --parent "$SOURCE_SHA" "${final_args[@]}" \
  "${critical_args[@]}" --output "$ARTIFACTS/import-audit.md"

run_gate flag-inventory "$ARTIFACTS/flag-inventory.md" \
  "$PYTHON" "$SKILL_DIR/scripts/flag_inventory.py" --repo "$REPO" \
  --target "$TARGET_SHA" --source "$SOURCE_SHA" "${final_args[@]}" \
  --file "$CONFIG_FILE" --class-name "$CONFIG_CLASS" --consumer-parity \
  "${flag_waiver_args[@]}" --output "$ARTIFACTS/flag-inventory.md"

run_gate duplicate-definitions "$ARTIFACTS/duplicate-definition.md" \
  "$PYTHON" "$SKILL_DIR/scripts/duplicate_definition_check.py" --repo "$REPO" \
  --base "$TARGET_SHA" --final "${FINAL_REV:-HEAD}" --paths-file "$PATHS_FILE" \
  --output "$ARTIFACTS/duplicate-definition.md"

run_gate interface-delta "$ARTIFACTS/interface-delta.md" \
  "$PYTHON" "$SKILL_DIR/scripts/interface_delta.py" --repo "$REPO" \
  --source "$SOURCE_SHA" --target "$TARGET_SHA" --final "${FINAL_REV:-HEAD}" \
  --paths-file "$PATHS_FILE" --output "$ARTIFACTS/interface-delta.md"

if [[ -s "$ARTIFACTS/interface-delta.md" ]]; then
  run_gate absent-symbol-triage "$ARTIFACTS/absent-symbol-triage.md" \
    "$PYTHON" "$SKILL_DIR/scripts/absent_symbol_triage.py" --repo "$REPO" \
    --report "$ARTIFACTS/interface-delta.md" --target "$TARGET_SHA" \
    --source "$SOURCE_SHA" "${final_args[@]}" \
    "${symbol_waiver_args[@]}" --output "$ARTIFACTS/absent-symbol-triage.md"
else
  record absent-symbol-triage skipped "$ARTIFACTS/absent-symbol-triage.md"
fi

run_gate orphan-scan "$ARTIFACTS/orphan-scan.md" \
  "$PYTHON" "$SKILL_DIR/scripts/orphan_scan.py" --repo "$REPO" \
  --target "$TARGET_SHA" --source "$SOURCE_SHA" "${final_args[@]}" \
  "${deploy_args[@]}" --output "$ARTIFACTS/orphan-scan.md"

if [[ -n "$TEST_COMMAND" ]]; then
  collect_args=()
  [[ -n "$COLLECT_COMMAND" ]] && collect_args=(--collect-command "$COLLECT_COMMAND")
  run_gate parent-test-delta "$ARTIFACTS/parent-test-delta.md" \
    "$PYTHON" "$SKILL_DIR/scripts/parent_test_delta.py" --repo "$REPO" \
    --final "${FINAL_REV:-HEAD}" --target "$TARGET_SHA" --source "$SOURCE_SHA" \
    --test-command "$TEST_COMMAND" "${collect_args[@]}" \
    --log-dir "$ARTIFACTS/logs/parent-test-delta" \
    --output "$ARTIFACTS/parent-test-delta.md"
else
  record parent-test-delta deferred "$ARTIFACTS/parent-test-delta.md"
fi

if [[ -n "$CARD_PATTERN" ]]; then
  run_gate review-preflight "$ARTIFACTS/review-preflight.json" \
    "$PYTHON" "$SKILL_DIR/scripts/review_preflight.py" --repo "$REPO" \
    --target-sha "$REVIEW_BASE_SHA" --head "${FINAL_REV:-HEAD}" --mode "$MODE" \
    --card-pattern "$CARD_PATTERN" --output "$ARTIFACTS/review-preflight.json"
else
  record review-preflight skipped "$ARTIFACTS/review-preflight.json"
fi

echo
echo "## Gate summary"
echo
printf "%-24s %-8s %s\n" gate result artifact
failed=0
for index in "${!NAMES[@]}"; do
  code="${CODES[$index]}"
  case "$code" in
    0) result=pass ;;
    skipped|deferred) result="$code" ;;
    *) result="FAIL($code)"; failed=1 ;;
  esac
  printf "%-24s %-8s %s\n" "${NAMES[$index]}" "$result" "${FILES[$index]}"
done
echo
echo "interface-delta is advisory: read absent-symbol-triage REAL-LOSS rows."
echo "deferred means no evidence was collected, not that the check passed."
exit "$failed"
