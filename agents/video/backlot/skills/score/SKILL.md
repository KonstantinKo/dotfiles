---
name: score
description: Music and sound effects for a Backlot project: mus and sfx takes, placement into timeline audio tracks, ducking under VO. Use for "add music", "score this", "sound design", "sfx for the door", "duck the music", or when Status.md shows stage score.
---

# Score

## Purpose
Place requested music and sound effects in `edit/timeline.yaml` with sensible levels.

## Inputs
- `Projects/<slug>/Brief.md` (tone), `Script.md` (beats, VO placement), `Shots/S###.md` (durations, action)
- `Context/Rules.md`, `Studio/Playbooks/Default.md`
- `backlot models --kind music`, `--kind sfx`
- `edit/timeline.yaml` if `assemble` already started
- The exact accepted picture cut and any title boundary or cue map relevant to this request

## Steps
1. Spawn `sound-designer` with Brief, Script and shot list. It returns a music brief if music is requested (genre, tempo, instrumentation, arc across the beats, where it should lift or drop), requested sfx cues (shot, event, description, at seconds), and a ducking plan for any VO that is present. Music, SFX, VO and native clip sound are separate optional elements; add only what the project asks for.
2. Music, when requested: `backlot gen mus --model <id> --prompt "<music brief>" --param duration=<film length + 2> --n 2 --depends-on Brief`. For paid calls, follow [Decision and spend](../studio/references/decision-and-spend.md); an exit 3 requires a recorded exact-call authorization, and `--yes` alone is not approval. Free/local calls need no spend authorization. Present both by ID with the arc described in one line each. Record the user's selected take with its exact approval text, message reference, reason, and use scope through `backlot approve`. Skip this step when music was not requested.
3. Sfx, when requested: one `backlot gen sfx --model <id> --prompt "<event>" --shot S### --depends-on "<shot's notes>"` per event. For paid calls, use the same [Decision and spend](../studio/references/decision-and-spend.md) procedure as music; batch the quote and authorize each paid call separately. Skip events the music already covers.
4. Placement: identify the exact picture cut by its source path and SHA-256, and use its probed frame rate, frame count and duration. Treat cue times as relative to that cut's first frame; place music after the exact title boundary when the requested cue plan calls for it. Probe the generated audio file and use its actual decoded duration to trim or pad against the picture, not the requested generation duration. Then add rows for requested elements to `audio:` in `edit/timeline.yaml`:
   `{track: music, src: mus-001, at: <measured cue start>, gain_db: -14}`
   `{track: sfx, src: sfx-003, at: <measured cue start>, gain_db: -6}`
   When VO rows are present, keep them at `gain_db: 0`; add `duck_under: vo` only when VO is present and ducking is needed. When a final-second music fade is requested, `out: <picture end>` trims the track and `fade_out_s: 1.0` fades its tail.
5. `backlot render --preset draft -o renders/score-check.mp4`. For a score-only change, verify the accepted picture's full frame sequence and timing are preserved. Listen to the rendered mix at each cue start and end, picture cuts, any title/SFX boundary, and critical sync points; check masking only where VO is present. Adjust `at` and gain values in the YAML; rerender. If listening is unavailable, report it as unavailable; a successful decode is a technical check, not a listening review.
6. Run read-only `backlot stage --json` for the current scored deliverable and declared sound blockers.

## Outputs
- Requested mus and sfx takes, approved with reasons
- `edit/timeline.yaml` audio rows
- `renders/score-check.mp4`

## Gate
Every requested audio element is approved and placed. Record technical checks, actual listening coverage, and user review as separate outcomes; leave any unavailable or unperformed review explicit. VO clarity is checked only when VO is part of the cut.

## Example phrases
- "score it, something warm and slow"
- "add a door slam at S050"
- "the music drowns the VO, duck it more"
