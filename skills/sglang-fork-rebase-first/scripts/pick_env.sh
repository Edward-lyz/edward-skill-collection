#!/usr/bin/env bash
# Pick where a rebase step runs: local (uv venv) first, remote only when local cannot.
#
#   pick_env.sh <static|unit|gpu> [--repo DIR]
#
# static : inventory / pick / ruff / contract / residual / CR / image fetch. Stdlib + git.
# unit   : repo unit tests that import torch etc. Local only if the import works in the venv.
# gpu    : EPD runtime acceptance, kernel tests. Always remote (macOS has no CUDA).
#
# Remote is whatever the user configured in REBASE_REMOTE: a command prefix that runs a
# shell command on the remote machine (e.g. "ssh user@gpu-host"). No tool is assumed.
#
# stdout: "local <venv>" or "remote <host>". Exit 1 on a missing hard dependency.
set -euo pipefail

need=${1:?usage: pick_env.sh <static|unit|gpu> [--repo DIR]}
shift
repo=$PWD
while [ $# -gt 0 ]; do
  case $1 in
    --repo) repo=$2; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

venv=${REBASE_VENV:-$HOME/.cache/sglang-rebase/.venv}

command -v git >/dev/null || { echo "missing: git" >&2; exit 1; }

use_remote() {
  [ -n "${REBASE_REMOTE:-}" ] \
    || { echo "remote needed but REBASE_REMOTE is unset (e.g. 'ssh user@gpu-host')" >&2; exit 1; }
  $REBASE_REMOTE true >&2 || { echo "remote '$REBASE_REMOTE' unreachable" >&2; exit 1; }
  echo "remote $REBASE_REMOTE"
  exit 0
}

[ "$need" = gpu ] && use_remote

command -v uv >/dev/null || { echo "uv missing, falling back to remote" >&2; use_remote; }
if [ ! -x "$venv/bin/python" ]; then
  uv venv "$venv" >&2
  # ruff is the only external tool the skill scripts call; they are otherwise stdlib.
  uv pip install --python "$venv/bin/python" ruff >&2
fi

if [ "$need" = unit ]; then
  # Unit tests need the repo's runtime deps. Try once; macOS often lacks CUDA-only wheels.
  if ! "$venv/bin/python" -c "import torch" 2>/dev/null; then
    uv pip install --python "$venv/bin/python" torch pytest >&2 || use_remote
  fi
  if ! (cd "$repo" && "$venv/bin/python" -c "import sglang.srt" 2>/dev/null); then
    uv pip install --python "$venv/bin/python" -e "$repo/python" >&2 || use_remote
    (cd "$repo" && "$venv/bin/python" -c "import sglang.srt" 2>/dev/null) || use_remote
  fi
fi

echo "local $venv"
