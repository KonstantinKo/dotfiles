---
name: voice
description: Voice-over for a Backlot project: tts per VO line with the voice locked in each Cast note, captions, timing check against shot durations. Use for "record the VO", "generate the voice-over", "captions for the narration", "the VO is too long for S030", or when Status.md shows stage voice.
---

# Voice

## Purpose
Produce an approved `vo` take per VO line, with captions, and confirm each line fits its shot.

## Inputs
- `Projects/<slug>/Script.md` (VO column, durations per beat)
- `Context/Cast/<Name>.md` (`voice:` id, delivery notes), `Studio/Voices/<id>.md`
- `Shots/S###.md` (`duration_s`, which VO line belongs to which shot)
- `backlot models --kind tts`, `--kind stt`; `Context/Rules.md` for the default tts model

## Steps
1. Build the line list: scene, speaker or narrator, text, target seconds. Create a Cast voice lock only when the declared workflow needs a recurring generated voice identity. Supplied or imported narration can be registered directly with exact provenance.
2. Per line: `backlot tts --model <tts> --voice <voice id> --text "<line>" --shot S030 --depends-on Cast/<Name>`. For paid calls, follow [Decision and spend](../studio/references/decision-and-spend.md): quote first, record a per-call authorization after explicit approval, and execute with its ID. `--yes` alone is not approval. Local tts (`kokoro`, `edge-tts`) is free and needs no spend authorization; prefer it for drafts.
3. Timing check: `ffprobe -show_entries format=duration` on each `takes/<id>/out.*`. A line longer than its shot's `duration_s` minus 0.3 s is flagged. Fix order: shorten the line with `screenwriter` (edit `Script.md`, regenerate), then speed param if the model has one, then extend the shot (goes through `revise`).
4. Listen or, when audio cannot be played, check the transcript with `backlot captions <take> --model <stt>` and diff it against the script text. Mispronunciations get a variation with a phonetic spelling, `--parent <take>`.
5. Record the user's chosen take per line with its original approval text/reference and reason through `backlot approve`; see [Decision and spend](../studio/references/decision-and-spend.md). Run `backlot captions` on each approved take; `.srt` and word timestamps land next to the media. If captions uses a paid route, quote and authorize it through the same procedure.
6. `backlot status`. Set `status: score` when every VO line has an approved take.

## Outputs
- vo takes, one approved per line, `.srt` plus word JSON
- `Shots/S###.md` with `vo_take`
- `Script.md` edits if lines were shortened

## Gate
All VO lines approved and within their shot durations.

## Example phrases
- "generate the voice-over for all beats"
- "redo the narrator line in S030, it runs long"
- "captions for the VO"
