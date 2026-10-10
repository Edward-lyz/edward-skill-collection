#!/usr/bin/env bash
# Push the replay stack to iCode review (refs/for) and print the tip SHA and Change-Ids.
#
#   submit_cr.sh <target-branch> [--base NEW_BASE_SHA] [--remote origin] [--dry-run]
#
# Never pushes to a protected branch: only refs/for/<target>. Every commit above the
# base must carry a Change-Id, otherwise review would open a new change per patchset.
set -euo pipefail

target=${1:?usage: submit_cr.sh <target-branch> [--base SHA] [--remote origin] [--dry-run]}
shift
base=""
remote=origin
dry=0
while [ $# -gt 0 ]; do
  case $1 in
    --base) base=$2; shift 2 ;;
    --remote) remote=$2; shift 2 ;;
    --dry-run) dry=1; shift ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

case $target in master|main) echo "refuse: $target is protected" >&2; exit 1 ;; esac
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "dirty worktree" >&2; exit 1; }

range=${base:+$base..}HEAD
missing=$(git log --format='%h' --no-merges "$range" | while read -r h; do
  git show -s --format=%B "$h" | grep -q '^Change-Id: ' || git log -1 --format='%h %s' "$h"
done)
if [ -n "$missing" ]; then
  echo "commits without Change-Id (commit-msg hook not installed?):" >&2
  echo "$missing" >&2
  exit 1
fi

echo "tip=$(git rev-parse HEAD)"
git log --format='change %h %s' --no-merges "$range"
if [ "$dry" = 1 ]; then
  echo "dry-run: skip push"
  exit 0
fi

git push "$remote" "HEAD:refs/for/$target" 2>&1
