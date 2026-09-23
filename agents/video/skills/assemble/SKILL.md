---
name: assemble
description: Assemble a Backlot project: author edit/timeline.yaml from approved takes, render a draft, write cut notes, produce alternative cuts as separate timeline files. Use for "cut it together", "assemble the edit", "render a draft", "three shorter cuts", "tighten the middle", or when Status.md shows stage assemble.
---

# Assemble

## Purpose
Produce a draft render from a deterministic timeline that names only approved takes.

## Inputs
- `Shots/S###.md` (`video_take`, `vo_take`, `duration_s`, order by shot number)
- `Takes/*.md` for statuses; `backlot takes --status approved`
- `edit/timeline.yaml` (audio rows from `score`)
- `<slug>.md` frontmatter (format, fps, resolution), `Brief.md` (length, mandatories)
- Timeline schema in `~/dotfiles/agents/video/ARCHITECTURE.md`

## Steps
1. Spawn `editor` with the shot list, approved take IDs and Brief. It returns a `video:` list: one row per shot in order, `src` = `video_take`, `in`/`out` trimmed to `duration_s`, transitions where the script implies them (default hard cut; `xfade` only on beat changes). Stills use `duration` and optional `motion: kenburns`.
2. Write `edit/timeline.yaml`:
   ```yaml
   format: 16:9
   fps: 24
   resolution: 1920x1080
   video: [...]
   audio: [...]        # vo rows at the shot start times, music and sfx from score
   captions: {src: vo-003, style: default, burn: false}
   titles: [...]       # mandatories from Brief: claim, logo card, legal
   ```
   Only approved take IDs. `backlot render` refuses rejected or stale sources (it lists the offending take IDs); fix the timeline rather than the take status. `--allow-stale` exists for a quick look, never for a delivered render.
3. `backlot render --preset draft -o renders/draft-01.mp4`. Watch it (or extract frames at each cut with ffmpeg). Check total length against Brief, VO sync, mandatories present.
4. Cut notes go into `edit/CUTS.md` in the project dir: render name, timeline file, what changed, what to watch for. Keep it a table. `Decisions.md` stays CLI-owned.
5. Alternative cuts ("three shorter cuts"): one file each, `edit/timeline-30s.yaml`, `edit/timeline-15s.yaml`, `edit/timeline-6s.yaml`; render each to `renders/<name>-01.mp4`. The main timeline stays `edit/timeline.yaml`.
6. Present renders by path with length and one line per cut. Take change requests as timeline edits; rerender with an incremented number. Never overwrite a render the user has seen.
7. `backlot status`. Set `status: review` when the user accepts a draft.

## Outputs
- `edit/timeline*.yaml`, `edit/CUTS.md`
- `renders/draft-NN.mp4` and variant renders

## Gate
`timeline.yaml` renders a draft the user has watched and accepted for review.

## Example phrases
- "cut it together and render a draft"
- "give me three shorter cuts: 30, 15 and 6"
- "tighten the middle, the second beat drags"
