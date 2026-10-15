---
name: review
description: Review a Backlot draft for continuity and Brief compliance: extract frames, compare against Context with vision, list drift, produce a flag list. Use for "review the draft", "continuity check", "does this match the brief", "what's off in the cut", or when Status.md shows stage review.
---

# Review

## Purpose
Find every place the draft contradicts the Context or the Brief, and hand the user a flag list with evidence. Fixing is a separate decision.

## Inputs
- The exact candidate output and its assembly record
- `Projects/<slug>/Brief.md` (goal, message, mandatories, length, deliverables)
- `Context/Cast/*.md`, `Locations/*.md`, `Props/*.md`, `Visual Language.md`, `Rules.md`
- `Shots/S###.md`, plus each shot’s selected source footage, board, or guide when present
- `Studio/Playbooks/Default.md` (whether auto-regeneration is allowed; default no)
- `../studio/references/production-checks.md` for review dimensions and accepted limitations

## Steps
1. Resolve semantic scene/beat names to shot IDs and the current render/timeline versions. Read the active Brief, shot cards, ordered reference roles, relevant prior/next beats, and accepted limitations.
2. Frames: `ffmpeg -i renders/draft-NN.mp4 -vf "fps=1" /tmp/backlot-review/<slug>/f%04d.jpg` plus cut points and risk-directed middle frames from the timeline. Watch full playback when possible; one-second samples alone can miss an action or morph. Keep frames in a temp dir, never in the vault or project dir.
3. Spawn `continuity` with the frame dir, timeline, active Context, shot cards, and each shot’s selected footage, board, or guide when present, with its reference role. A board is optional when the shot uses another declared source. It returns a table: timecode, semantic scene and shot ID, category (identity, wardrobe, location, prop, palette, lighting, camera, text, audio sync), intended context, observed evidence, severity (block, fix, note), take ID involved. Report technical validity separately from semantic/story and continuity findings.
4. Brief compliance, done by the lead: length within tolerance, message legible, mandatories present (logo, claim, legal), format and captions as specified, tone matches three words. Add rows to the same table. Record subjective judgments and accepted imperfections separately from technical passes; accepted limitations remain notes unless the user reopens them.
5. Write the human-readable findings in `Projects/<slug>/Review.md` and, when a typed review criterion is declared, record the exact output version, coverage and criterion with `backlot review-record <spec.json>`.
6. Present the first review before proposing paid repairs. Show block/fix rows by semantic scene, shot, and take ID, one line each, plus exact route/settings and `backlot gen --dry-run` cost if estimating repairs. Do not regenerate. `auto_regenerate: true` in `Playbooks/Default.md` or `Rules.md` may permit local review or revision work within its stated category. Every paid repair still needs the exact quote and explicit per-call authorization in `../studio/references/decision-and-spend.md`.
7. On the user's decisions, fix the named blocker and compare before/after nearby context. `backlot repair-plan <spec.json>` records a bounded no-spend plan for an eligible typed review; `backlot repair-result <spec.json>` records its observed effect. A technically valid job with no visible target change is ineffective. Run read-only `backlot stage --json` for current blockers.

## Optional visual HTML review

Use [`templates/visual-review.html`](templates/visual-review.html) only when the user selects an HTML review surface. Copy it for the candidate and fill the semantic scene/shot, take and active versions, source artifact ID/hash, exact submitted inputs in request order, actual review coverage, payload size, and publication revision/state. Identify inputs by stable IDs and hashes; keep private URLs, credentials, and local paths out of the page. The blank template contains no candidate evidence and its pending checks must remain pending until performed.

Budget the completed page before publication; keep the whole artifact below 512 KB. Embed review media as data URLs when that fits. Show the complete candidate image with `object-fit: contain` and fluid width/height limits. An optional detail crop is a separate image with its source and crop window recorded; it never replaces the whole frame. If the selected review surface is used, check the actual desktop and target mobile layouts and record each result. Record a failed publication as failed with its observed error, and leave `Published revision` empty unless that revision was actually published. Do not infer full playback, listening, semantic review, or user approval from a frame page.

## Outputs
- `Projects/<slug>/Review.md` (flag table, newest on top)
- Regeneration cost estimate in chat

## Gate
Declared review criteria have version-bound evidence, and the matching user approval is recorded on the deliverable. A `Review.md` file alone is not an approval or gate pass.

## Example phrases
- "review the draft against the brief"
- "continuity check on draft-03"
- "what's off in this cut"
