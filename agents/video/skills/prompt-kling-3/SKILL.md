---
name: prompt-kling-3
description: Use when writing a prompt for a video via Kling 3 (fal fal-ai/kling-video/v3 image-to-video, text-to-video, motion-control, or Kling O3 reference-to-video).
---

# Prompting Kling 3

Sources and details: `references/research.md` (researched 2026-09-24).

## Pick the endpoint
- **v3 pro/standard image-to-video:** `start_image_url` (required), optional `end_image_url`, `elements` (`@Element1`, character consistency), `negative_prompt`, `cfg_scale`, `generate_audio`, `multi_prompt`. 3–15 s.
- **v3 turbo:** image, prompt and duration only (no end frame, elements, negative or audio toggle).
- **v3 motion-control:** image + `video_url` + `character_orientation`. `video` (≤30 s): camera and motion follow the video. `image` (≤10 s): motion from the video, camera from the prompt. Wants a realistic human in the reference video; a grey-mannequin previz may not track.
- **O3 reference-to-video:** start/end frames plus elements and `image_urls` (`@Image1`); max 4 elements + images when a video is used.

## Prompt template (60–100 words per shot)
```
<Setting>. @Element1 <action>. <Camera: framing + one move, e.g. slow push-in from medium to close-up, fixed lens>. <Light>. <Sound or none>.
```
Settings: `generate_audio: false` (music-only films; also 1.5x cheaper), `cfg_scale: 0.5`, default `negative_prompt` + only the artifacts you actually see.

## Rules
- Order: setting, subject, action, camera, sound.
- Keep single shots at 3–6 s; beyond ~6 s coherence drifts. Multi-shot via `multi_prompt` (≤6 shots, each with its own duration).
- Start and end frames must be similar, or Kling inserts a cut.
- Elements: `frontal_image_url` + 1–3 `reference_image_urls`; they must appear in the reference frames; elements double the per-second price.
- Motion-control: don't describe the action in the prompt; the video drives it.
- When text controls motion, describe visible action and the camera's relation to the subject, including its landing frame. For motion-control, keep video-driven action out of the prompt and follow the selected orientation mode.
- Faces: no documented block on realistic faces; you need rights to the likeness. Smoke-test one face element (3 s, audio off) before relying on it.
- Generated speech is English or Chinese only on fal.
- For complex blocking, acting, stylized shots, or repairs, read the [shared shot-direction reference](../higgsfield-seedance-prompt-builder/references/shot-direction.md).
