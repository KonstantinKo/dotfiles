---
name: prompt-minimax-h3
description: Use when writing a prompt for a video via MiniMax H3 Max (fal minimax/h3-max reference-to-video or image-to-video).
---

# Prompting MiniMax H3 Max

Sources and details: `references/research.md` (researched 2026-09-24).

## Pick the endpoint
- **image-to-video:** the image must be the exact first frame (optional `end_image_url` for first→last).
- **reference-to-video:** images carry identity, wardrobe, location or style; optional motion video. ≤9 images, ≤3 videos (2–15 s each, ≤15 s total), duration ≤15 s.
- Never send a first frame alongside references: it is dropped silently and still billed.

## Prompt template (plain English, `prompt_expansion_mode: balanced`)
```
Image 1 is <name>: preserve <face, hair, clothes> exactly. Image 2 is <location/wardrobe>.
Video 1 provides only the camera path; do not copy its subject, colours, lighting or audio.
[0-3 s] <beat>. [3-6 s] <beat>. [6-<n> s] <beat>.   (beats sum to the duration)
The camera <push in / pull out / pan / tilt / arc / pedestal / tracking> with <small/large> amplitude at <slow/fast> speed toward <target>.
Sound: <named sources>. No music, no dialogue, no on-screen text, no subtitles.
```

## Rules
- Same reference images and the same identity paragraph, word for word, in every call.
- One subject, one action, one main camera move per shot; end every move on a target.
- Reference video colours and audio leak: use a neutral grey previz and say "camera path only".
- Audio is always generated: name real sounds or say "no music, no dialogue".
- `disabled` expansion only for long prompts already in MiniMax's structured format (see references); skip `quality`.
- Real faces: allowed with consent; moderation is stricter and false positives happen. If blocked, try a cleaner crop before rewording.
- Portraits need a subtle camera move, otherwise they look like a still with motion painted on.
- Validation is late: check the output, not the submit response.
