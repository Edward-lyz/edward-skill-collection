# Edward's Skill Collection

Private agent skill collection for Claude Code, Codex, and pi.

## Layout

```text
skills/
  code-philosophy-check/
  cuda/
  dev-machine-remote/
  grill-me/
  op-profiler/
  python-dev-standards/
scripts/
  link-local.sh
```

Each skill follows the Agent Skills directory format:

```text
skill-name/
  SKILL.md
  references/
  scripts/
  assets/
```

## Skills

| Skill | Purpose |
| --- | --- |
| `code-philosophy-check` | Check changed code against local code philosophy rules. |
| `cuda` | CUDA kernel development, profiling, debugging, and review. |
| `dev-machine-remote` | Remote development-machine command and file-sync workflow. |
| `grill-me` | Stress-test a plan through iterative questioning. |
| `op-profiler` | Remote operator profiling workflow. |
| `python-dev-standards` | Python development and review standards. |

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
pi install /Users/liyanzhen/baidu/PRIVATE/edward-skill-collection
```

## Maintenance

Add or update a skill:

```bash
cp -a /path/to/skill skills/<skill-name>
git add skills/<skill-name>
git commit -m 'Add <skill-name> skill'
```

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
