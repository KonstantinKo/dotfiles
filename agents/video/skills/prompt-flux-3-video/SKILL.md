---
name: prompt-flux-3-video
description: Use when writing a prompt for a video via FLUX 3 (fal blackforestlabs/flux-3 text-, image-, first-last-frame-, keyframes-to-video, extend, edit, draft/draft-enhance).
---

# Prompting FLUX 3 video

Sources and details: `references/research.md` (researched 2026-09-24).

## Workflow
- Draft first (`.../draft`, ~$0.06/s, 720p), judge motion, timing and blocking there. Enhance the approved draft to 1080p by sending only its `draft_cache_url` to `draft-enhance` (~$0.29/s). Enhance adds detail, never fixes motion.
- No seed input: store `draft_cache.url` in the take metadata.
- 24 fps, 5–20 s whole seconds; set `aspect_ratio: 16:9`; `generate_audio` defaults to true (set false for music-only films).

## Keyframes from a previz
- `keyframes[]` = `{image_url, frame_index}`, 1–10, zero-based at 24 fps, unique, explicit duration (no `auto`).
- Pin where motion changes (start, turn apex, doorway, arrival); 3–6 pins; leave ≥12 frames after the last pin. For an exact last frame use `first-last-frame-to-video`.
- Derive all keyframe stills by editing one hero still; independent generations drift.
- The prompt describes the motion between pins; the images carry the look.

## Prompt template
```
Use the pinned images as keyframes of one continuous shot.
0.0-4.0s — <framing + one camera move> as <subject action>.
4.0-7.5s — ...
7.5-<n>s — ... settles.
<Subject block, verbatim from the Cast note>. Same house, materials and light as the keyframes throughout.
<Sound, or none>. No on-screen text or subtitles.
```

## Rules
- Plain directive prose; order: camera/shot, subject, action, setting, light/look, audio. 5–10 beats max.
- One framing term + one movement + one action per beat. Avoid roll, portal, morph effects.
- No negative prompts; prose guardrails work ("locked-off", "no camera shake", "no on-screen text").
- Multi-shot in one clip: `SHOT ONE: ... HARD CUT. SHOT TWO: ...` with contrasting shots.
- Extends drift after about 3 hops; restart from the last clean clip.
- Real people: benign, consented portrayals are allowed; don't present the fantasy as real footage.
