# Edward's Skill Collection

Private agent skill collection for Claude Code, Codex, and pi.

## Layout

```text
skills/
  code-philosophy-check/
  codebase-design/
  cuda/
  dev-machine-remote/
  diagnosing-bugs/
  domain-modeling/
  gorden-ppt-skill/
  grill-me/
  handoff/
  lsp-callgraph/
  op-profiler/
  python-dev-standards/
  tdd/
  teach/
  writing-great-skills/
third_party/
  mattpocock-skills/
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
| `codebase-design` | Shared vocabulary for deep modules, seams, interfaces, leverage, and locality. |
| `cuda` | CUDA kernel development, profiling, debugging, and review. |
| `dev-machine-remote` | Remote development-machine command and file-sync workflow. |
| `diagnosing-bugs` | Disciplined diagnosis loop for hard bugs and performance regressions. |
| `domain-modeling` | Build project glossary and ADRs when domain terminology needs sharpening. |
| `grill-me` | Stress-test a plan through iterative questioning. |
| `handoff` | Write a redacted handoff document for another agent session. |
| `lsp-callgraph` | Generate bounded LSP call hierarchy graphs as interactive HTML. |
| `op-profiler` | Remote operator profiling workflow. |
| `python-dev-standards` | Python development and review standards. |
| `tdd` | Test-driven development through vertical red-green-refactor slices. |
| `teach` | Stateful workspace-based teaching sessions. |
| `writing-great-skills` | Reference for writing and editing predictable agent skills. |
| `gorden-ppt-skill` | AI-friendly Chinese PPT builder with 17 templates, text-only editing via python-pptx. |

## Upstream imports

Selected skills from `mattpocock/skills` are tracked in `skills-lock.json`.
The upstream MIT license is preserved at
`third_party/mattpocock-skills/LICENSE`.

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
