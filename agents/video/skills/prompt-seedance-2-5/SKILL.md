---
name: prompt-seedance-2-5
description: Use when writing a prompt for a video via Seedance 2.5 (fal bytedance/seedance-2.5 reference-to-video or image-to-video).
---

# Prompting Seedance 2.5

Sources and details: `references/research.md`, `references/likeness-filter.md` (researched 2026-09-24).

## Hard limits
- **No realistic human faces in reference images.** ByteDance rejects them (`content_policy_violation` on `image_urls`), real or AI-generated. Tiny faces in wide shots pass. Use Seedance for wide or faceless shots; close shots go to another model.
- fal: ≤30 images, ≤10 videos (≤30.2 s combined), ≤10 audio. Input video seconds are billed: trim previz to the shot length.
- `generate_audio` defaults to true: set false for music-only films. Iterate at 480p, final at 720p.

## Prompt template
```
FORMAT: <n>s, 16:9, single take, real-time speed
REFERENCE ROLES: @Image1 = <one job> only; do not copy <pose/background/light> from @Image1. @Video1 = camera path, framing and timing only; do not copy its grey geometry, mannequins or flat lighting.
BRIEF: <one sentence>
TIMELINE: 0-3s ..., 3-6s ..., 6-<n>s ...   (continuous, no gaps, fills the duration)
CAMERA: follow @Video1 exactly (don't restate the move)
CONTINUITY: <invariants: faces, clothes, props, screen direction>
AUDIO: none
CONSTRAINTS: photoreal, no cuts, no text, no extra people, no toy-like rendering, no camera guides
```

## Rules
- Tags are positional (@Image1 = first URL). Check order before sending.
- 2–5 references that agree beat many. One job per reference, plus what not to take from it.
- Previz clips: flat grey, no UI or gizmos, placeholder colours get copied.
- Longer durations don't add events; spare seconds become slow motion or repeats.
- No negative field: specific exclusions go in CONSTRAINTS.
- Avoid redesign words ("transforms", "more cinematic"); describe visible behaviour.
- On a miss, change one thing and keep the working wording.
