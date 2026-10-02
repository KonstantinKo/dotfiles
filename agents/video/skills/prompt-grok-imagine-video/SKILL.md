---
name: prompt-grok-imagine-video
description: Use when writing a prompt for a video via Grok Imagine Video (fal xai/grok-imagine-video v1.5 image-, reference- or text-to-video, and the older extend/edit).
---

# Prompting Grok Imagine Video

Sources and details: `references/research.md` (researched 2026-09-24).

## Endpoints (fal)
- **v1.5 image-to-video:** image = first frame; aspect follows the image; up to 1080p.
- **v1.5 reference-to-video:** ≤7 images tagged `<IMAGE_0>`…; ≤720p (default 480p). Tag numbering is inconsistent in the docs: probe with two refs first.
- 1–15 s. No video or motion reference, no first/last-frame pinning on fal. Audio is always on: strip it in post.
- Older (non-1.5) extend (+2–10 s) and edit (cuts to 8 s, 480p) only.

## Prompt template (30–60 words)
```
<Subject from <IMAGE_0>> <one action> in <setting>. <One camera move, or static>. <Light/look>. Sound: <named sources, or quiet room tone>.
```

## Rules
- Write events in the order they happen; late actions often get dropped.
- One action and one camera move per clip; static is the default.
- Image-to-video: describe only what changes, not what's already in the image.
- If the camera moves, describe its visible landing target within the short prompt budget; a requested ending is direction, not a pinned last frame.
- Always include a `Sound:` line.
- Faces: realistic and consented real-person references are not forbidden, but the filter is strict since January 2026 and reportedly blocks anything resembling a minor. Blocked requests are still billed: run one cheap 480p probe per sensitive reference.
- For complex blocking, acting, stylized shots, or repairs, read the [shared shot-direction reference](../higgsfield-seedance-prompt-builder/references/shot-direction.md).
