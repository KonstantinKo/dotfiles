---
name: davinci-resolve-captions
description: Build and revise speech-synced captions in DaVinci Resolve Studio, including editable Text+ designs, mixed typography, word timing, zooms, and cutaways. Use for caption work in Resolve; use davinci-resolve-localization for translated or reframed versions.
---

# Speech-synced captions in Resolve

Use [davinci-resolve](../davinci-resolve/SKILL.md) for project access, state preservation, app or script execution, preview, and delivery. Assume the installed Resolve Studio version; inspect its actual capabilities. Do not add setup steps as a prerequisite. If the user asks for a paste-ready script, follow the shared [Lua handoff and execution contract](../davinci-resolve/references/execution-and-contract.md); script authorship does not require a connected Studio session. For complex custom animation, read [davinci-resolve-motion](../davinci-resolve-motion/SKILL.md) and its relevant references.

Anchor cues to the audio the viewer hears. Keep source-media, timeline-record, and Fusion-comp frames distinct; read [timeline frame conventions](../davinci-resolve/references/timeline-media-render.md) and the focused [cue mapping guide](references/cue-mapping.md) before converting speech times. Resolve's scripting API reports timeline item positions in frames and can expose fractional positions when requested.

Choose the representation by the deliverable:

- Use a native subtitle track for conventional dialogue captions, review, and subtitle export. SRT cues are phrase ranges by default; importing one does not make it word-timed. Treat automatic transcription as a draft and check every cue against speech.
- For per-word emphasis or custom type, preserve editable wording in native Text+ / Fusion titles and retain cue-to-word timing. Do not estimate word boundaries by dividing a phrase evenly. Keep a reusable native title or Fusion template editable rather than baking text into a movie.
- Use Text+ when a line needs mixed styles, a curved path, custom reveals, or independent word motion. Character Level Styling supports per-character font and style changes; use separate text elements or a selected range when words need their own timing. Keep phrase reading order and legibility clear.

Keep dialogue timing stable across B-roll and zooms. Position titles in the final record frame, check that zooms do not unexpectedly scale or hide them, and respect the subject and required safe area. Preserve reference-supported cuts and holds; give each phrase enough time to read. Inspect cue entrances, exits, cut boundaries, and representative frames over moving footage. Do not apply one motion treatment to every word by default.
