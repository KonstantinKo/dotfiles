---
name: deliver
description: Deliver a Backlot project: final renders per preset, 9:16 reframes, localisation hook, final status, commits. Use for "export the final", "deliver", "make the shorts version", "render for youtube", "localise to German", or when Status.md shows stage deliver.
---

# Deliver

## Purpose
Produce every deliverable named in the Brief, record the state, and commit both repos.

## Inputs
- `Projects/<slug>/Brief.md` (deliverables, languages), `<slug>.md` frontmatter (`deliverables[]`)
- `edit/timeline*.yaml`, `Review.md` (no open block flags)
- `Studio/Workflows/Reframing.md`, `Studio/Workflows/Localisation.md`
- `backlot models --kind upscale` when the Brief asks for above-native resolution

## Steps
1. Confirm the deliverables list from the Brief in one message: name, preset, aspect, captions, language. Ask only if the Brief is silent.
2. Upscale, if required, approved takes only: stills with `backlot gen up --model fal-topaz-upscale-image --image <take> --shot S###`, video takes with `backlot gen up --model fal-topaz-upscale-video --video <take> --shot S###`, one call per take, estimate first; swap the `src` in a copy of the timeline (`edit/timeline-final.yaml`).
3. Master: `backlot render edit/timeline-final.yaml --preset youtube -o renders/<slug>-master-16x9.mp4`. Watch the result end to end or check frames at every cut.
4. Vertical: follow `Workflows/Reframing.md`. `backlot reframe renders/<slug>-master-16x9.mp4 --to 9:16 --focus auto`, then check every shot with a face for framing; rerun single shots with `--focus left|right` and rebuild via a 9:16 timeline if the auto crop cuts a subject. Render with `--preset shorts`.
5. Localisation, when languages are listed: follow `Workflows/Localisation.md`: translate VO lines in a `Script.<lang>.md`, run the `voice` skill with the same Cast voice or the language variant from `Studio/Voices/`, captions per language, one timeline per language, render each.
6. Verify each file with `ffprobe` (duration, resolution, fps, audio present). List paths with sizes.
7. `backlot cost` then `backlot status`; set `status: delivered` and `deliverables[]` in `<slug>.md` to the rendered file names.
8. Commit: in `~/projects/video/<slug>/` `git add -A && git commit -m "deliver: <names>"` (media is ignored; timelines, meta and manifest are tracked). In the vault `git add Projects/<slug> Studio && git commit -m "<slug>: delivered"`.
9. Write a short retro into `Studio/Lessons/<date>-<slug>.md`: what cost more than expected, which model held identity best, what to promote into a Playbook.

## Outputs
- `renders/<slug>-*.mp4` per deliverable
- `Status.md` at delivered, `Costs.md` final, `Lessons` note
- Two commits

## Gate
Every Brief deliverable exists in `renders/`, verified, and both repos are committed.

## Example phrases
- "export the final and the shorts version"
- "deliver it"
- "we also need a German version"
