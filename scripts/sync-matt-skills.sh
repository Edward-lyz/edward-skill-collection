#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
skills_dir="$repo_root/skills"
matt_productivity_dir="$repo_root/third_party/mattpocock-skills/skills/productivity"

if [ ! -d "$matt_productivity_dir" ]; then
  echo "Matt skills submodule is not initialized; run git submodule update --init --recursive" >&2
  exit 1
fi
if [ -L "$skills_dir/teach" ] || [ ! -f "$skills_dir/teach/SKILL.md" ]; then
  echo "skills/teach must remain a local skill directory" >&2
  exit 1
fi

mapping_file=$(mktemp)
skill_files_file=$(mktemp)
trap 'rm -f "$mapping_file" "$skill_files_file"' EXIT

find "$matt_productivity_dir" -type f -name SKILL.md -print | LC_ALL=C sort >"$skill_files_file"

skill_count=0
while IFS= read -r skill_file; do
  skill_dir=${skill_file%/SKILL.md}
  skill_name=${skill_dir##*/}
  [ "$skill_name" = "teach" ] && continue
  relative_target="../${skill_dir#"$repo_root/"}"
  printf '%s\t%s\n' "$skill_name" "$relative_target" >>"$mapping_file"
  skill_count=$((skill_count + 1))
done <"$skill_files_file"

if [ "$skill_count" -eq 0 ]; then
  echo "no Matt productivity skills found in $matt_productivity_dir" >&2
  exit 1
fi

LC_ALL=C sort -o "$mapping_file" "$mapping_file"
duplicate_names=$(cut -f1 "$mapping_file" | uniq -d)
if [ -n "$duplicate_names" ]; then
  echo "Matt skill names must be unique across categories:" >&2
  printf '%s\n' "$duplicate_names" >&2
  exit 1
fi

while IFS=$'\t' read -r skill_name relative_target; do
  skill_path="$skills_dir/$skill_name"
  if [ -L "$skill_path" ]; then
    current_target=$(readlink "$skill_path")
    case "$current_target" in
      ../third_party/mattpocock-skills/skills/*) ;;
      *)
        echo "refuse to replace non-Matt skill link: $skill_path -> $current_target" >&2
        exit 1
        ;;
    esac
  elif [ -e "$skill_path" ]; then
    echo "refuse to replace local skill: $skill_path" >&2
    exit 1
  fi
done <"$mapping_file"

for skill_path in "$skills_dir"/*; do
  [ -L "$skill_path" ] || continue
  current_target=$(readlink "$skill_path")
  case "$current_target" in
    ../third_party/mattpocock-skills/skills/*)
      skill_name=${skill_path##*/}
      if ! awk -F '\t' -v name="$skill_name" '$1 == name { found = 1 } END { exit !found }' "$mapping_file"; then
        rm "$skill_path"
      fi
      ;;
  esac
done

while IFS=$'\t' read -r skill_name relative_target; do
  ln -sfn "$relative_target" "$skills_dir/$skill_name"
done <"$mapping_file"

echo "linked $skill_count Matt productivity skills; kept local teach"
