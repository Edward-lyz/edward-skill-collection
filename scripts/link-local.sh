#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
skills_dir="$repo_root/skills"
claude_project_skills="$HOME/baidu/.claude/skills"
pi_global_skills="$HOME/.agents/skills"
codex_skills="$HOME/.codex/skills"

if [ ! -d "$skills_dir" ]; then
  echo "missing skills directory: $skills_dir" >&2
  exit 1
fi

mkdir -p "$(dirname "$claude_project_skills")" "$HOME/.agents" "$codex_skills"

if [ -e "$claude_project_skills" ] && [ ! -L "$claude_project_skills" ]; then
  echo "refuse to overwrite real directory: $claude_project_skills" >&2
  exit 1
fi
ln -sfn "$skills_dir" "$claude_project_skills"

if [ -e "$pi_global_skills" ] && [ ! -L "$pi_global_skills" ]; then
  echo "refuse to overwrite real directory: $pi_global_skills" >&2
  exit 1
fi
ln -sfn "$skills_dir" "$pi_global_skills"

for skill_path in "$skills_dir"/*; do
  [ -d "$skill_path" ] || continue
  skill_name=$(basename "$skill_path")
  codex_link="$codex_skills/$skill_name"
  if [ -e "$codex_link" ] && [ ! -L "$codex_link" ]; then
    echo "refuse to overwrite Codex skill directory: $codex_link" >&2
    exit 1
  fi
  ln -sfn "$skill_path" "$codex_link"
done

find -L "$skills_dir" -maxdepth 2 -name SKILL.md | sort
