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
- The chosen native timeline or external/custom assembly recipe
- `<slug>.md` frontmatter (format, fps, resolution), `Brief.md` (length, mandatories)
- The exact accepted picture and any requested finishing cues, graphics or deliverable variants
- Timeline schema in `~/dotfiles/agents/video/backlot/ARCHITECTURE.md`

## Steps
1. Spawn `editor` with the shot list, approved take IDs and Brief. It returns a `video:` list: one row per shot in order, `src` = `video_take`, `in`/`out` trimmed to `duration_s`, transitions where the script implies them (default hard cut; `xfade` only on beat changes). Stills use `duration` and optional `motion: kenburns`.
2. Write `edit/timeline.yaml` when the project uses the Backlot renderer:
   ```yaml
   format: 16:9
   fps: 24
   resolution: 1920x1080
   video: [...]
   audio: [...]        # only requested audio: VO, music, sfx, or native sound
   captions: ...       # only when requested
   titles: ...         # only when required by the Brief or user
   ```
   Only approved take IDs. `backlot render` refuses rejected or stale sources (it lists the offending take IDs); fix the timeline rather than the take status. `--allow-stale` exists for a quick look, never for a delivered render.
   Keep project-local/custom renderers supported; do not require another renderer to translate into this timeline format. For every cut, cue map and exact graphic, bind timing to the chosen picture version, its hash, exact frame rate and stated time origin.
3. If the native renderer is selected, run `backlot render --preset draft -o renders/draft-01.mp4`. Otherwise keep the external/custom recipe. Check the actual frame count, dimensions, frame rate, audio streams and color metadata. Review the picture at cuts and any exact lettering at output size. When audio is requested, listen at cue boundaries and critical sync points. Report technical checks, listening/visual review and user review separately.
4. Cut notes go into `edit/CUTS.md` in the project dir: render name, timeline file, what changed, what to watch for. Keep it a table. `Decisions.md` stays CLI-owned.
5. Alternative cuts ("three shorter cuts"): one file each, `edit/timeline-30s.yaml`, `edit/timeline-15s.yaml`, `edit/timeline-6s.yaml`; render each to `renders/<name>-01.mp4`. The main timeline stays `edit/timeline.yaml`.
6. Present renders by path with length and one line per cut. Take change requests as timeline edits; rerender with an incremented number. Never overwrite a render the user has seen.
7. Register the selected output as an M2 assembly artifact, then `backlot assembly <spec.json>` with the route, recipe hash and ordered source/output frame ranges. Run read-only `backlot stage --json` to see unresolved work.

## Outputs
- `edit/timeline*.yaml`, `edit/CUTS.md`
- `renders/draft-NN.mp4` and variant renders

## Gate
The chosen assembly route has a reproducible recipe, verified output bytes and a source map. `edit/timeline.yaml` is required only for the native renderer.

## Example phrases
- "cut it together and render a draft"
- "give me three shorter cuts: 30, 15 and 6"
- "tighten the middle, the second beat drags"
