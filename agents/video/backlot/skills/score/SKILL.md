---
name: score
description: Music and sound effects for a Backlot project: mus and sfx takes, placement into timeline audio tracks, ducking under VO. Use for "add music", "score this", "sound design", "sfx for the door", "duck the music", or when Status.md shows stage score.
---

# Score

## Purpose
Give the film a music bed and the sfx the shots call for, placed in `edit/timeline.yaml` with sensible levels.

## Inputs
- `Projects/<slug>/Brief.md` (tone), `Script.md` (beats, VO placement), `Shots/S###.md` (durations, action)
- `Context/Rules.md`, `Studio/Playbooks/Default.md`
- `backlot models --kind music`, `--kind sfx`
- `edit/timeline.yaml` if `assemble` already started

## Steps
1. Spawn `sound-designer` with Brief, Script and shot list. It returns: a music brief (genre, tempo, instrumentation, arc across the beats, where it should lift or drop), an sfx list (shot, event, description, at seconds), and a ducking plan.
2. Music: `backlot gen mus --model <id> --prompt "<music brief>" --param duration=<film length + 2> --n 2 --depends-on Brief`. Exit 3: estimate, ask, `--yes`. Present both by ID with the arc described in one line each. Approve one with a reason.
3. Sfx: one `backlot gen sfx --model <id> --prompt "<event>" --shot S### --depends-on "<shot's notes>"` per event. Batch the estimate. Skip events the music already covers.
4. Placement: add rows to `audio:` in `edit/timeline.yaml`:
   `{track: music, src: mus-001, at: 0.0, gain_db: -14, duck_under: vo, duck_db: -10}`
   `{track: sfx, src: sfx-003, at: 12.4, gain_db: -6}`
   VO rows stay at `gain_db: 0`. Music ends with a fade in the last second: `out: <film length>` trims the track and `fade_out_s: 1.0` fades its tail.
5. `backlot render --preset draft -o renders/score-check.mp4`. Listen for masking of VO, sfx timing against picture. Adjust `at` and gain values in the YAML; rerender.
6. `backlot status`. Set `status: assemble`.

## Outputs
- mus and sfx takes, approved with reasons
- `edit/timeline.yaml` audio rows
- `renders/score-check.mp4`

## Gate
Music approved and placed; sfx placed; VO audible over music in the draft render.

## Example phrases
- "score it, something warm and slow"
- "add a door slam at S050"
- "the music drowns the VO, duck it more"
