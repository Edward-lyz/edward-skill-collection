---
name: teach
description: Teach the user a new skill or concept, within this workspace.
disable-model-invocation: true
argument-hint: "What would you like to learn about?"
---

The user has asked you to teach them something. This is a stateful request across sessions, but the **only required deliverable is a core Markdown lesson**. Do not invent a course bureaucracy.

## Default workspace

Prefer an existing teaching workspace under `/Users/liyanzhen/baidu/PRIVATE/teach/<topic-slug>/`.

If the topic is new:

1. Create only `/Users/liyanzhen/baidu/PRIVATE/teach/<topic-slug>/lessons/`.
2. Put the lesson at `lessons/0001-<dash-case-name>.md`.
3. Update `/Users/liyanzhen/baidu/PRIVATE/teach/README.md` with one row for the new topic.

Do **not** create any of these by default:

- `MISSION.md`
- `NOTES.md`
- `RESOURCES.md`
- `learning-records/`
- `reference/`
- `assets/` beyond the current lesson banner SVG
- `build_standalone.py`
- `dist/`
- HTML lessons
- quiz widgets / shared CSS / standalone builders

If the user already has an old HTML-heavy workspace, keep reading it for context, but write **new** lessons as Markdown unless they explicitly ask for HTML.

## What the user cares about

1. The **core lesson** in Markdown.
2. A **banner diagram at the top** in the SGLang / LMSYS algorithm-figure style.
3. Enough depth to understand and reuse the idea. No ceremony files.

Everything else is optional scaffolding. Create it only when it unblocks teaching.

## Lesson unit

A lesson is one Markdown file:

```text
lessons/000N-<dash-case-name>.md
```

Numbering: scan existing `lessons/*.md` and `lessons/*.html`, take the highest number, increment by one. Prefer `.md` for new work.

### Required structure

```md
# {Title}

![Alt text: the mechanism thesis in one line.](./assets/{slug}-banner.svg)

*{Italic caption: what to notice in the figure.}*

{One sentence: what the learner can do after this lesson.}

## 背景
...

## 核心原理
...

## 公式推导   # only if a real derivation exists
...

## 小结
...
```

Rules:

- Start with `# Title`, then the banner figure, then an italic caption, then one outcome sentence.
- The banner is mandatory. No placeholder, no decorative art, no AI bitmap.
- Teach only what is needed for the outcome.
- Prefer tables, short code blocks, numbered derivations, and extra body diagrams only when they earn space.
- Cite high-trust sources inline when making non-obvious technical claims.
- Keep the lesson short enough to finish in one sitting, but do not split artificially if the user asked for one dense note.
- End with a short retrieval check: 2–4 questions, or one concrete task. Answers can sit under a section titled `参考答案`.

Optional sections only when they earn their place:

- 术语表
- 一图流 / 数据流
- 工程依据
- 与相邻方案对比
- 练习

### Forbidden by default

- `imagegen` / AI raster banners / stock photos
- Generic Mermaid flowchart as the opening banner for a multi-role algorithm
- HTML lesson chrome, quiz.js, lesson-nav, followup blocks
- Cards, badges, gradient callouts, fake stats
- Multi-file "course systems" for a single note
- Rebuilding `build_standalone.py` / `dist/`

## Banner figure — SGLang pattern

Every lesson opens with a wide algorithm figure in the style of the SGLang / LMSYS Kimi K3 day-0 post figures. The local reference translation is:

`/Users/liyanzhen/baidu/PRIVATE/teach/kimi-k3-day0-translation/translation-and-commentary.md`

Full visual language: [references/sglang-figure-pattern.md](./references/sglang-figure-pattern.md)

Starter shell: [assets/banner-template.svg](./assets/banner-template.svg)

### Non-negotiables

1. **Hand-authored SVG** under `lessons/assets/<lesson-slug>-banner.svg`
2. **Mechanism first** — the figure proves one idea: who owns what, what moves, what stays, what is index-only
3. **Multi-lane / overlay / rank-dataflow composition**, not a blob of rounded rectangles
4. **Semantic colors** for mechanisms, stable inside the figure
5. **Solid vs dashed arrows** mean different things and are defined in a legend
6. **Numbered phases** `① ② ③` when there are multiple moves
7. **Bottom italic invariant** stating the sentence the reader should keep
8. **Markdown alt + italic caption** under the image
9. **No text occlusion** — labels never cross strokes, arrows, borders, braces, or other labels
10. **Precise frames** — dashed groups / braces / keep-groups tightly bound only the claimed nodes

### Default composition choices

| Topic shape | Banner pattern |
| --- | --- |
| State moves over time | Multi-lane space-time |
| Sparse markers on a tree / pool / pipeline | Structure overlay |
| TP / PP / DCP / draft-verify | Rank or stage dataflow |
| Layout or policy change | Before → after panels |
| Optimization stack | Ladder / waterfall, usually as a body figure |

### Visual system, short form

- Paper `#ffffff`, ink `#22211e`, caption `#8f8b83`
- State/slot sand, copy/COW blue, snapshot teal, donate/index purple, stream sage
- Font: Inter / system UI sans
- Frame about `1000×560`
- Pure vectors only; no embedded PNG
- 3–9 primary nodes, 2–4 mechanisms, one legend, one invariant

### How to produce the banner

Universal pipeline (details in [references/sglang-figure-pattern.md](./references/sglang-figure-pattern.md)):

1. **Refuse the wrong medium** — no imagegen, no Mermaid banner, no embedded bitmaps.
2. **Write the visual thesis card first** — thesis, roles, 2–4 moves, invariant, pattern.
3. **Choose one composition pattern** from the table above. Prefer multi-lane space-time when the idea is *when* state moves.
4. **Copy** `assets/banner-template.svg` → `lessons/assets/<slug>-banner.svg`.
5. **Lay out skeleton before labels** — bands, left roles, x-axis time/stages, 3–9 nodes, arrows, phases, legend, invariant, aria-label.
6. **Apply LMSYS density rules** — left-to-right serial rhythm, sparse phase groups, solid/dashed arrow grammar, mechanism colors only, intentional whitespace, one bottom invariant.
7. **Enforce hard geometry** — no text occlusion; group boxes / braces / keep-groups tightly frame exactly the claimed nodes (≈8–12 px pad); arrow docks land on node edges.
8. **Self-check against** `/tmp/sglang-figs/fig1-state-flow.svg` or `fig2-radix-branching.svg` when available, including occlusion and frame-precision checks.
9. **Embed under H1** with alt + italic caption, then write/finalize prose so labels stay synchronized.

Mermaid may appear later in the body for a tiny checklist flow. It is not the banner standard.

Do **not** use AI image generation for banners.

## Teaching loop

Do the smallest useful loop:

1. **Clarify the target.** If the user already named the topic, do not interview them for a mission document. Infer the practical outcome and start teaching.
2. **Ground the content.** Prefer primary sources, papers, source code, and the user's own repos over parametric memory. When a claim is load-bearing, open the source.
3. **Design the banner figure first** in the SGLang pattern.
4. **Write one Markdown lesson** around that figure.
5. **Open or point to the file.** Give the path. Do not publish, build, or create a site page unless asked.
6. **Stop.** Wait for questions, corrections, or "next lesson".

If the user wants a multi-lesson path, keep a short ordered list in chat or in a single `lessons/README.md`. Do not create a parallel tracking system.

## Optional scaffolding

Create these only when a concrete need appears:

| File | Create when |
| --- | --- |
| `NOTES.md` | User states durable teaching preferences worth reusing next session |
| `RESOURCES.md` | There are multiple high-trust sources that will be reused across lessons |
| `MISSION.md` | The goal is ambiguous and wrong scope would waste work |
| `learning-records/*.md` | User demonstrates a non-obvious understanding or prior knowledge that should change future lessons |
| `reference/*.md` | A cheatsheet will be revisited more than the lesson itself |
| HTML / interactive assets | User explicitly wants an interactive page or site publish |

Formats for the rare optional files live in:

- [MISSION-FORMAT.md](./MISSION-FORMAT.md)
- [RESOURCES-FORMAT.md](./RESOURCES-FORMAT.md)
- [LEARNING-RECORD-FORMAT.md](./LEARNING-RECORD-FORMAT.md)

## Pedagogy, without ceremony

Still optimize for long-term retention, not a tour of files:

- One tangible win per lesson
- Stay in the zone of proximal development
- Prefer retrieval practice over passive summary
- Use desirable difficulty for skills; remove unnecessary difficulty from pure knowledge acquisition
- Distinguish facts, derivations, and your engineering inferences

### Fluency vs storage strength

- Fluency: short-term retrieval while the note is open
- Storage strength: still usable next week

Design the ending check for storage strength.

## Knowledge and citations

Never trust parametric memory for niche systems, paper results, or repo-specific behavior. Open the code or paper first.

When the workspace has a `RESOURCES.md`, prefer those sources. When it does not, gather only the sources needed for this lesson and cite them inline. Do not create `RESOURCES.md` just to host three links.

## Skills practice

If the topic is skill-heavy, the Markdown lesson should still end with practice:

- a derivation to redo from memory
- a command sequence to run
- a small code-reading task in the user's repo
- 2–4 multiple-choice questions with equally long options

Interactive HTML quizzes are optional, not the default.

## Wisdom

If the user needs practitioner judgment rather than a settled fact, answer carefully, mark uncertainty, and point to a high-signal community only when useful. Respect opt-outs.

## Session notes

If the user says how they want to learn, record it in `NOTES.md` only after the preference is clearly durable. Examples worth recording:

- step-by-step formula derivations, no skipped algebra
- terminology table before the first dense section
- Chinese prose, English terms
- SGLang-style SVG banners; no AI bitmaps

## Completion criteria

A teaching turn is done when:

1. There is a new or updated `lessons/000N-*.md`
2. The file starts with a hand-authored SGLang-style SVG banner of the core mechanism
3. The figure has alt text, italic caption, legend semantics, and an invariant
4. The lesson is grounded enough to trust
5. The user can open one Markdown file and study without touching scaffolding

If you produced extra files the user did not need, delete them before finishing.
