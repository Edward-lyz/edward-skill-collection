# SGLang / LMSYS Figure Pattern

Canonical visual language for teach banners. Distilled from the figures used in
[SGLang and Miles Add Day-0 Support for Kimi K3](https://www.lmsys.org/blog/2026-07-27-kimi-k3-day0-support/)
and mirrored in
`/Users/liyanzhen/baidu/PRIVATE/teach/kimi-k3-day0-translation/translation-and-commentary.md`.

Best reference SVGs (hand-authored, pure vectors):

- `fig1-state-flow.svg` — multi-lane space-time diagram of COW / snapshot / donate
- `fig2-radix-branching.svg` — tree overlay with sparse checkpoints and branch points

Local copies of the pure-vector refs (if present): `/tmp/sglang-figs/fig1-state-flow.svg`, `/tmp/sglang-figs/fig2-radix-branching.svg`.

Other post figures (PP chunking, DCP dataflow, unified memory, ladders) share the same
editorial rules even when exported from a drawing tool.

## What the figures are for

A figure is not decoration. It is a compressed proof of one mechanism.

Good figures answer, at a glance:

1. Which roles / ranks / buffers exist
2. What moves, and what stays put
3. What is solid copy vs index-only vs in-place mutation
4. What invariant the prose will later rely on

Bad figures: abstract wallpaper, logo soup, unlabeled arrows, generic boxes with no topology.

## Universal production pipeline

Use this pipeline for **every** future lesson banner. Do not invent a new process per topic.

### Step 0 — refuse the wrong medium

Stop if you are about to:

- call `imagegen` / any AI bitmap generator
- paste a Mermaid flowchart as the opening banner for a multi-role algorithm
- draw a blob of rounded rectangles with equal weight and no lanes
- embed PNG/JPEG inside the SVG

Banner medium is always hand-authored pure SVG.

### Step 1 — write the visual thesis first (2 minutes)

Before any SVG geometry, fill this card:

```text
Thesis:   one sentence the figure proves without prose
Roles:    2–4 actors that become lanes / panels
Moves:    2–4 mechanisms (copy, snapshot, index-only, verify, …)
Invariant: one italic sentence the reader should keep
Pattern:  multi-lane | structure-overlay | rank-dataflow | before-after | ladder(body only)
```

If you cannot write the thesis, you do not understand the lesson yet. Open the source, then return.

### Step 2 — choose one composition pattern

| Topic shape | Banner pattern | Cadence to copy |
| --- | --- | --- |
| State moves over time | Multi-lane space-time | `fig1-state-flow.svg` |
| Sparse markers on a tree / pool / pipeline | Structure overlay | `fig2-radix-branching.svg` |
| TP / PP / DCP / draft-verify | Rank or stage dataflow | DCP / PP figures |
| Layout or policy change | Before → after panels | lower half of `fig2` |
| Optimization stack | Ladder / waterfall | body figure, rarely the banner |

Rules:

- One primary pattern only. Do not mix five patterns into one frame.
- Ladder / waterfall is almost always a body figure, not the opening banner.
- Prefer multi-lane space-time when the algorithm is about *when* state moves relative to a serial stream.

### Step 3 — lay out the skeleton before labels

Copy [../assets/banner-template.svg](../assets/banner-template.svg) to:

```text
lessons/assets/<lesson-slug>-banner.svg
```

Then place, in this order:

1. Paper background + CSS variables (do not invent a new palette)
2. Faint lane bands (`ink` ≈ 3% opacity), left role labels, optional row subtitles
3. Time / stage axis on x when the pattern is space-time or dataflow
4. Primary nodes only (3–9)
5. Mechanism arrows (solid / dashed / tick), then phase numbers `①②③`
6. One-line legend
7. Bottom italic invariant
8. `role="img"` + `aria-label` equal to the thesis

Do not write long prose inside the figure. Secondary captions are short *when/why* notes under a node.

### Step 4 — apply the LMSYS density rules

These are the differences between "usable" and "official-looking":

1. **Left-to-right time wins.** In a serial lane, nodes share one baseline and advance on x. Do not stack a serial chain into a cramped 2-row snake unless the second row is a true parallel actor.
2. **Phase groups are sparse.** Use dashed group boxes or bottom brace labels for stage spans (`extend · …`, `decode · …`), not heavy cards.
3. **Arrow grammar is load-bearing.** Solid = bytes/state move. Dashed = index/ownership/selection only. Double-ended tick = in-place read/write. Every arrow type appears in the legend.
4. **Color encodes mechanism, not decoration.** One family per mechanism, stable inside the figure.
5. **Secondary captions explain condition, not the box title.** Example: `cache hit · tree → request`, not another copy of `copy-on-write`.
6. **Whitespace is intentional.** Official figures leave quiet paper between phase clusters. If the middle is cramped, delete a node or widen the frame before shrinking fonts.
7. **One invariant at the bottom.** Italic, centered, caption color. No second slogan.
8. **No text occlusion.** Labels never sit on a stroke, arrow shaft, node border, group outline, brace, or another label. Prefer quiet paper pockets above/below a gap; never "float" a caption across geometry and hope opacity hides the collision.
9. **Precise grouping marks.** Dashed group boxes, keep-groups, braces, and phase spans must tightly frame the exact nodes they claim (about 8–12 px pad). Do not draw a decorative box that includes unrelated nodes, cuts a node in half, or leaves a large empty half-lane.

### Step 4b — hard geometry rules (non-negotiable)

Treat the SVG as engineering geometry, not freehand illustration.

#### No occlusion

Forbidden:

- Text crossing a line, arrow, stream, brace, or group border
- Phase numbers sitting on a node face or arrow head
- Secondary captions stacked on top of primary node labels
- Row labels colliding with content that leaks into the left gutter
- Legend / invariant overlapping the bottom braces

Required layout habits:

1. Reserve a **left gutter** (~140–160 px) for role labels only. Content bands start after the gutter.
2. Reserve **quiet channels** between lanes for handoff arrows and short handoff labels.
3. Put `①②③` in a free pocket beside the mechanism arrow, not on the mechanism itself.
4. Keep secondary captions either centered under their node with ≥4 px clear air, or left-aligned in a free strip that no stroke enters.
5. If a label does not fit without collision, shorten the label or move a node. Do not shrink font below the system sizes.

#### Precise frames / braces / keep-groups

A group mark is a proof claim. Its bounds must equal the claim.

Rules:

1. **Containment.** Every node the group claims is fully inside; every node it does not claim is fully outside.
2. **Pad.** About 8–12 px from the outermost claimed node edges. Not 2 px (looks clipped) and not 40 px (looks fake).
3. **Brace x-range = content x-range.** Bottom braces start and end under the same nodes the phase actually covers.
4. **Keep / drop groups are exclusive.** A keep-group frames only retained tokens; trimmed tokens sit outside it.
5. **One purpose per box.** Do not reuse one dashed rectangle to mean both "serial chain" and "formula note".
6. **Arrow docks are exact.** Arrow endpoints stop at node borders (or a fixed 4–8 px gap before the marker), not mid-air and not buried inside a box.
7. **Self-check with numbers.** Before shipping, verify group bounds against node coords. Mental eyeballing is not enough when nodes are dense.

### Step 5 — self-check against official refs

Open the closest pure-vector reference and answer yes/no:

- [ ] Could a reader restate the thesis without the lesson body?
- [ ] Are roles lanes/panels rather than a spaghetti graph?
- [ ] Does every arrow type appear in the legend?
- [ ] Do colors map to mechanisms, not mood?
- [ ] Is the serial rhythm left-to-right with a visible time cadence?
- [ ] Is the handoff into the next phase obvious (keep/drop, donate, verify prefix)?
- [ ] Is the bottom italic sentence the actual invariant?
- [ ] Is the SVG pure vectors under `lessons/assets/`?
- [ ] Does any text cross a stroke, arrow, node border, group outline, or brace?
- [ ] Do group boxes / braces tightly frame exactly the claimed nodes (8–12 px pad, no half-cut nodes)?

If two or more answers are no, revise the SVG before writing more prose.

### Step 6 — embed in Markdown, then write the lesson

```md
# Title

![<mechanism thesis in one line>](./assets/<slug>-banner.svg)

*<what to notice in the figure>*

After this lesson you can ...
```

Only after the figure labels are stable, write or finalize the body so terminology stays synchronized.

### Step 7 — optional preview render

When the user wants a visual check, render a PNG preview with the local browser/QL toolchain and show the absolute path. Do not check the PNG into the lesson tree; the lesson source of truth is the SVG.

## Composition patterns

Pick one primary pattern for the banner. Do not mix five patterns into one frame.

### 1. Multi-lane space-time

Rows = roles. Columns / x-axis = time or step.

Example: radix tree / request private state / forward stream as three lanes; COW, snapshot,
donate drawn as colored arrows across lanes.

Use when the algorithm is about *when* state moves relative to a serial stream.

Cadence template from `fig1-state-flow.svg`:

- Lane bands full-width under a quiet paper background
- Left labels: role + 1–2 subtitles
- Bottom serial stream as a bead chain of short kernels
- Vertical / curved arrows for cross-lane state moves
- Bottom braces for stage groups
- Legend one line above the italic invariant

### 2. Structure overlay

A durable structure (tree, memory pool, pipeline) is drawn first. Sparse annotations
(checkpoints, free region, hand-off arrows) sit on top.

Use when the key idea is *where* something is placed on an existing structure.

### 3. Rank / stage dataflow

Two or more parallel actors. Local work, one collective, then local merge.

Use for TP / PP / DCP / EP / draft-verify paths.

### 4. Before → after comparison

Stacked or side-by-side panels that change only the disputed dimension.

Use for pool layouts, KV layout, policy A vs policy B.

### 5. Ladder / waterfall

Ordered optimization or cost stages with cumulative effect.

Use for throughput ladders and category breakdowns. Rarely the right banner for a pure
algorithm lesson; better as a body figure.

## Visual system

Copy this system. Do not invent a new palette per lesson.

### Surfaces and ink

| Token | Light | Role |
| --- | --- | --- |
| `--paper` | `#ffffff` | background |
| `--ink` | `#22211e` | primary labels |
| `--cap` | `#8f8b83` | secondary captions, legends, axis labels |

Support dark mode with the same token names when practical.

### Semantic mechanism colors

Assign one color family per mechanism, then keep it stable inside the figure:

| Mechanism class | Stroke / text | Fill |
| --- | --- | --- |
| Durable state / slot | `#bd9358` | `#f4ecdc` |
| Copy / COW / remote read / base tensor | `#4c5fa8` | `#e5e9f7` |
| Snapshot / checkpoint / bias repair | `#2e8c80` | `#dcefeb` |
| Ownership transfer / donate / index-only | `#a05a92` | soft purple if needed |
| Forward stream / compute lane | `#7f9c92` | paper or faint sage |

If the lesson has different mechanisms, remap the same four or five families rather than adding neon colors.

### Geometry

- Wide frame: roughly `1000×480` to `1000×720`, or `1080×620` when a fourth band is needed
- Rounded rects, `rx=4` to `rx=9`
- Stroke width `1.2` to `2.1`; never heavy poster outlines
- Solid arrow = bytes / state actually move
- Dashed arrow = index / ownership / metadata only
- Double-ended tick or short bar = in-place read/write on one slot
- Sparse dashed group boxes for ping-pong buffers, stages, or logical groups
- Faint lane bands (`ink` at ~3% opacity) instead of heavy grid paper

### Typography

Font stack:

```text
"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif
```

Sizes that match the LMSYS figures:

- Optional figure title: 14–15px, weight ~700 (keep short; body H1 already names the lesson)
- Row / panel title: 13px, weight ~650
- Node primary label: 11–12px, weight 650–700
- Secondary caption under a node: 10–10.5px, normal, `--cap`
- Legend / axis: 10.5–11px, `--cap`
- Bottom invariant sentence: 11.5–12px italic, `--cap`

Labels are short. Prefer:

- `working slot`
- `keep / next`
- `① copy-on-write`
- `index only · no bytes`

Avoid paragraph text inside the figure.

## Annotation grammar

Every banner should use this grammar when applicable:

1. **Lane labels on the left** — who owns the row
2. **Numbered phases** — `① ② ③` for the 2–4 moves that matter
3. **Primary / secondary text** — bold mechanism name, smaller condition under it
4. **Bottom legend** — decode solid/dashed/colors once
5. **One italic invariant** — the sentence the reader should remember

Example invariant:

> Every state copy is a kernel on the one serial stream. The only move that leaves the request moves no bytes.

## Markdown embedding

In the lesson:

```md
# Title

![Three KDA state moves — COW, snapshot, donate — against one serial forward stream.](./assets/0001-state-flow-banner.svg)

*Three state moves relative to the serial forward stream: copy-on-write on cache hit, snapshot at chunk boundaries, donate of an index with no byte copy.*

After this lesson you can ...
```

Rules:

- Alt text states the mechanism, not "architecture diagram"
- Italic caption immediately under the figure says what to notice
- The body prose may restate the invariant, but the figure must already carry it

## Implementation rules for teach

1. Default banner medium is **hand-authored SVG** in this pattern.
2. Keep the SVG pure vectors: `rect`, `text`, `line`, `path`, `circle`, CSS variables, markers.
3. Do not embed PNG/JPEG inside the SVG for algorithm banners.
4. Do not use Mermaid as the banner when the idea needs lanes, overlays, solid/dashed semantics, or numbered phases. Mermaid is fine later in the body for a simple checklist flow.
5. Do not use AI image generation.
6. Budget: about 3–9 primary nodes, 2–4 colored mechanisms, one legend, one invariant.
7. Reuse [../assets/banner-template.svg](../assets/banner-template.svg) as the starting shell.
8. Follow the **Universal production pipeline** above for every new lesson.

## Design checklist before shipping

- [ ] One visual thesis, readable without the prose
- [ ] Roles are lanes or panels, not a spaghetti graph
- [ ] Every arrow type is defined in the legend
- [ ] Colors encode mechanisms, not decoration
- [ ] Secondary captions explain *when/why*, not restate the box title
- [ ] Serial / time lanes read left-to-right with clear phase groups
- [ ] Handoff into the next phase is explicit (keep/drop, donate, verify prefix, …)
- [ ] Bottom italic sentence states the invariant
- [ ] No text occlusion: labels clear of strokes, arrows, borders, braces, other labels
- [ ] Group boxes / braces / keep-groups precisely frame only the claimed nodes
- [ ] Arrow endpoints dock cleanly on node edges
- [ ] File is self-contained SVG under `lessons/assets/`
