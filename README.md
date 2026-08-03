# Edward's Skill Collection

Private agent skill collection for Claude Code, Codex, and pi.

## Layout

```text
skills/
  <local-skill>/
  <matt-skill> -> ../third_party/mattpocock-skills/skills/<category>/<skill>
third_party/
  GordenSuperPPTSkills/
  kill-ai-slop/       # Git submodule
  mattpocock-skills/  # Git submodule
scripts/
  link-local.sh
  sync-matt-skills.sh
```

Each skill follows the Agent Skills directory format:

```text
skill-name/
  SKILL.md
  references/
  scripts/
  assets/
```

## Local skills

| Skill | Purpose |
| --- | --- |
| `gorden-image2pptx` | Convert slide images/screenshots back into editable PPTX using background, frame, icons, and text layers. |
| `code-philosophy-check` | Check changed code against local code philosophy rules. |
| `branch-replay` | Per-commit branch replay onto a new base with a migration report. |
| `cuda` | CUDA kernel development, profiling, debugging, and review. |
| `dev-machine-remote` | Remote development-machine command and file-sync workflow. |
| `op-profiler` | Remote operator profiling workflow. |
| `nsight-systems` | Nsight Systems profiling, report analysis, and recipe workflows. |
| `python-dev-standards` | Python development and review standards. |
| `aiqa-test-report` | Query AIQA standard test records and return report/review links. |
| `teach` | Stateful workspace-based teaching sessions. |
| `gorden-ppt-skill` | AI-friendly Chinese PPT builder with 17 templates, text-only editing via python-pptx. |

## Upstream imports

`yetone/kill-ai-slop` is mounted as the `third_party/kill-ai-slop` Git
submodule. Its Agent Skill is exposed as `skills/kill-ai-slop` through a
relative symlink.

`mattpocock/skills` is mounted as the
`third_party/mattpocock-skills` Git submodule. Every upstream directory under
`skills/productivity` that contains a `SKILL.md` is exposed through a flat
relative symlink under the local `skills/` directory. The only exclusion is
`teach`, which remains the local implementation. The selected engineering
skills are `diagnosing-bugs` and `research`.

Initialize the submodule after cloning:

```bash
git submodule update --init --recursive
./scripts/sync-matt-skills.sh
```

`gorden-image2pptx` is imported from `GordenSun/GordenSuperPPTSkills` upstream path `GordenImage2PPTX`.
Its upstream README and attribution notice are preserved at
`third_party/GordenSuperPPTSkills/README.md`.

## Local linking

Run from repository root:

```bash
./scripts/link-local.sh
```

The script links:

```text
~/baidu/.claude/skills -> ./skills
~/.agents/skills       -> ./skills
~/.codex/skills/<name> -> ./skills/<name>
```

Codex keeps `~/.codex/skills` as a real directory so bundled `.system`
skills are not overwritten.

## pi usage

pi auto-discovers `~/.agents/skills`, so no settings change is required.

This repository also works as a pi package:

```bash
pi install /Users/liyanzhen/baidu/PUBLIC_REPO/edward-skill-collection
```

## Maintenance

Add or update a skill:

```bash
cp -a /path/to/skill skills/<skill-name>
git add skills/<skill-name>
git commit -m 'Add <skill-name> skill'
```

Update the Matt Pocock skills to the latest upstream `main` commit:

```bash
git submodule update --remote --checkout third_party/mattpocock-skills
./scripts/sync-matt-skills.sh
git add third_party/mattpocock-skills skills
git commit -m 'Update Matt Pocock skills'
```

The sync script adds newly published Matt productivity skills and the selected
engineering skills, removes links for deleted skills, and fails on missing
selected skills, duplicate names, or collisions with local skills.

The parent repository deliberately pins the reviewed submodule commit; an
ordinary `git pull` does not silently advance it.

Validate skill discovery:

```bash
find -L skills -maxdepth 2 -name SKILL.md | sort
find -L ~/baidu/.claude/skills -maxdepth 2 -name SKILL.md | sort
find -L ~/.agents/skills -maxdepth 2 -name SKILL.md | sort
```

## GitHub private publish

```bash
gh repo create edward-skill-collection --private --source . --remote origin --push
```
