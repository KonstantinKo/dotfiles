---
name: review
description: Review a Backlot draft for continuity and Brief compliance: extract frames, compare against Context with vision, list drift, produce a flag list. Use for "review the draft", "continuity check", "does this match the brief", "what's off in the cut", or when Status.md shows stage review.
---

# Review

## Purpose
Find every place the draft contradicts the Context or the Brief, and hand the user a flag list with evidence. Fixing is a separate decision.

## Inputs
- `renders/draft-NN.mp4` (latest accepted), `edit/timeline.yaml`
- `Projects/<slug>/Brief.md` (goal, message, mandatories, length, deliverables)
- `Context/Cast/*.md`, `Locations/*.md`, `Props/*.md`, `Visual Language.md`, `Rules.md`
- `Shots/S###.md`, `_thumbs/` for the approved board per shot
- `Studio/Playbooks/Default.md` (whether auto-regeneration is allowed; default no)

## Steps
1. Frames: `ffmpeg -i renders/draft-NN.mp4 -vf "fps=1" /tmp/backlot-review/<slug>/f%04d.jpg` plus one frame at each cut point from the timeline. Keep frames in a temp dir, never in the vault or project dir.
2. Spawn `continuity` with the frame dir, the timeline, the Context notes and the boards. It returns a table: timecode, shot, category (identity, wardrobe, location, prop, palette, lighting, camera, text, audio sync), what the Context says, what the frame shows, severity (block, fix, note), take ID involved.
3. Brief compliance, done by the lead: length within tolerance, message legible, mandatories present (logo, claim, legal), format and captions as specified, tone matches three words. Add rows to the same table.
4. Merge into `Projects/<slug>/Review.md`: header with render name and date, the table, then a summary line per severity. Newest review on top.
5. Present the block and fix rows by shot and take ID, one line each, plus the regeneration cost if they were all fixed (`backlot gen --dry-run` per affected shot). Do not regenerate. Only when `Playbooks/Default.md` or `Rules.md` states `auto_regenerate: true` for a category may the lead proceed without asking, and then still through the normal estimate flow.
6. On the user's decisions: fixes go through `revise` (Context changes) or `generate` (new variation of one take). Accepted notes stay as notes. `backlot status`; set `status: deliver` when no block rows remain.

## Outputs
- `Projects/<slug>/Review.md` (flag table, newest on top)
- Regeneration cost estimate in chat

## Gate
No `block` flags open, or the user has waived them in chat and the waiver is written into `Review.md`.

## Example phrases
- "review the draft against the brief"
- "continuity check on draft-03"
- "what's off in this cut"
