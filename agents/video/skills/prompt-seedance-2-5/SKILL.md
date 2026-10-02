---
name: prompt-seedance-2-5
description: Use when writing a prompt for a video via Seedance 2.5 (Higgsfield seedance_2_5 or fal bytedance/seedance-2.5 reference-to-video or image-to-video).
---

# Prompting Seedance 2.5

Sources and details: `references/research.md` (researched 2026-09-24), `references/likeness-filter.md` (updated 2026-09-28).

For cinematic shot design or repairs, use [higgsfield-seedance-prompt-builder](../higgsfield-seedance-prompt-builder/SKILL.md) alongside this skill. Its [shot direction](../higgsfield-seedance-prompt-builder/references/shot-direction.md) covers blocking, acting and camera intent; retain this skill's platform rules and reference syntax.

## Hard limits
- **Faces depend on the platform.**
  - **Higgsfield (`seedance_2_5`):** the S012 job on 2026-09-28 (`6d039779-7745-4eed-a686-d017ad150b6e`) accepted local uploads of fal-generated photoreal Tamino and Stoyan reference sheets/composites, approved fal-generated start/end images, and a local Blender previz. A job ID was not needed for this input set. Why Higgsfield accepted it is unknown; this does not establish that raw photographs or every face reference will pass. For this project, use Higgsfield Seedance 2.5 with the local files for upcoming shots, and record results in `references/likeness-filter.md`.
  - **fal:** our fal Seedance tests rejected realistic faces in reference images (`content_policy_violation` on `image_urls`), real or AI-generated. Tiny faces in wide shots passed. Use fal Seedance for wide or faceless shots; close shots go to another model.
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
- Define the intended opening, camera side, body orientation and gaze when blocking is complex. Scope location references to layout/materials unless they also control framing; use reactions readable at the chosen shot size.
- Previz clips: flat grey, no UI or gizmos, placeholder colours get copied.
- Longer durations don't add events; spare seconds become slow motion or repeats.
- No negative field: specific exclusions go in CONSTRAINTS.
- Avoid redesign words ("transforms", "more cinematic"); describe visible behaviour.
- On a miss, change one thing and keep the working wording.
