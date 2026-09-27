# Prompting FLUX 3 video (fal.ai) — research notes

Researched 2026-09-24. Sources inline. "BFL" = official docs.bfl.ml; "fal schema" = fal OpenAPI for the named endpoint; "Runware" = Runware's model docs (third-party host, but detailed and consistent with BFL).

## 1. Endpoint facts (from fal schemas)

| Endpoint | Key inputs | Notes |
| --- | --- | --- |
| `text-to-video` | prompt, duration, resolution, aspect_ratio, generate_audio | |
| `image-to-video` | `image_url` = first frame | duration may be `auto` |
| `first-last-frame-to-video` | `start_image_url`, `end_image_url` | explicit duration **required** ([fal schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=blackforestlabs/flux-3/first-last-frame-to-video)) |
| `keyframes-to-video` | `keyframes[]` of `{image_url, frame_index}`, 1–10 items | integer duration 5–20 (default 5), no `auto` ([fal schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=blackforestlabs/flux-3/keyframes-to-video)) |
| `extend-video` | `video_url` (MP4 <50 MB, <15 s), prompt | continues from the source's last frames ([fal schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=blackforestlabs/flux-3/extend-video)) |
| `edit-video` | `video_url` (MP4 <50 MB, <15 s), prompt ≤4096 chars | no duration/res params ([fal schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=blackforestlabs/flux-3/edit-video)) |
| `*/draft` | same as parent minus `resolution` | returns `video` + `draft_cache` ([fal schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=blackforestlabs/flux-3/keyframes-to-video/draft)) |
| `draft-enhance` | `draft_cache_url` only | 1080p final ([fal schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=blackforestlabs/flux-3/draft-enhance)) |

- All: 24 fps, 5–20 s whole seconds, 720p/1080p, aspect `auto|21:9|2:1|16:9|4:3|1:1|3:4|9:16`, `generate_audio` default **true**, `safety_tolerance` 0–4 (default 2). The generation endpoints take **no seed input**; the seed is only returned. Draft→enhance is how you lock a result.
- Set `aspect_ratio` explicitly (e.g. `16:9`). `auto` lets the model pick.
- Pricing per output second ([fal guide](https://fal.ai/learn/tools/how-to-use-flux-3)): standard $0.17 (720p) / $0.29 (1080p); extend $0.41 / $0.53; draft $0.06 (extend draft $0.12); draft-enhance $0.29. A 10 s shot costs $0.60 as a draft and $2.90 to enhance. Go straight to 1080p only when you're sure.

## 2. Prompt structure and length

- Write plain, directive prose, the way you'd brief a DP. Avoid keyword lists. "Direct the scene, don't inventory the objects in it." ([fal](https://fal.ai/learn/tools/how-to-use-flux-3), [Runware](https://runware.ai/docs/models/bfl-flux-3-video/guides/prompting))
- Default one-liner order: **[camera/shot] of [subject] [action] in [environment], then motion, light and look, then audio** ([fal](https://fal.ai/learn/tools/how-to-use-flux-3)).
- BFL's full-structure order is core summary → scene (setting, light, DoF) → subject identity → timecoded action/camera → audio → style/colour ([BFL t2v](https://docs.bfl.ml/guides/prompting_video_text_to_video)). Always include "continuity constraints", meaning what must stay stable ([BFL overview](https://docs.bfl.ml/guides/prompting_video_overview)).
- Length: a few hundred well-chosen words at most. After that, "later clauses start to fight earlier ones for focus". **5–10 named beats beat 40 adjectives.** ([Runware](https://runware.ai/docs/models/bfl-flux-3-video/guides/prompting))
- Budget time per beat: 2–3 phases in a 5 s clip ([BFL t2v](https://docs.bfl.ml/guides/prompting_video_text_to_video)), about 5–7 s per shot beat, 12–18 s for a 3-cut spot ([Runware](https://runware.ai/docs/models/bfl-flux-3-video/guides/prompting)). If you give it too little duration, content gets dropped rather than evenly compressed ([Runware multi-shot](https://runware.ai/docs/models/bfl-flux-3-video/guides/multi-shot-sequences)).
- **Timestep prompting** gives precise timing: `0.0–1.5s — …  1.5–3.0s — …  3.0–5.0s — …` ([BFL t2v](https://docs.bfl.ml/guides/prompting_video_text_to_video)).
- **Multi-shot in one generation:** `SHOT ONE: … HARD CUT. SHOT TWO: …`. Capitalised `SHOT`/`HARD CUT` lands better than "cut to". Adjacent shots need to contrast in scale, angle, location or light, otherwise they blend into one take. Name the music bed once, or it restarts at every cut. ([Runware multi-shot](https://runware.ai/docs/models/bfl-flux-3-video/guides/multi-shot-sequences))
- The model rewrites and fills in anything you leave out (light, skin tone, ambience). Every explicit choice is respected. When a default lands wrong, fix that one layer in the next iteration instead of rewriting everything ([Runware](https://runware.ai/docs/models/bfl-flux-3-video/guides/prompting)).
- **No negative prompts.** State what you want. Exceptions that work as prose guardrails: "no camera shake", "no on-screen text or subtitles", "no announcer delivery". ([Morphic](https://morphic.com/resources/how-to/flux-3-guide), [BFL audio](https://docs.bfl.ml/guides/prompting_video_audio))

## 3. Keyframes and frame indices

- `frame_index` is a zero-based integer at 24 fps. It must be unique and ≤ duration×24. Up to 10 keyframes. ([fal schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=blackforestlabs/flux-3/keyframes-to-video))
- **Don't pin the literal last frame.** fal's guide says a keyframe at 240 in a 10 s clip "leaves zero runway and breaks the call". Their example spaces 0 / 96 (4 s) / 216 (9 s) and keeps a buffer at the tail ([fal](https://fal.ai/learn/tools/how-to-use-flux-3)). A safe end pin is `duration*24 - 12` or so (about 0.5 s runway). For an exact end frame, use `first-last-frame-to-video`.
- Tell the prompt what the images are, e.g. "Use this image as the first frame", so they act as strong anchors rather than loose references ([Runware keyframes](https://runware.ai/docs/models/bfl-flux-3-video/guides/keyframes)).
- Keyframes should be **the same composition family**. Radical composition changes between neighbouring keyframes don't interpolate cleanly. Distant keyframes can cause drift, props that linger too long, or jumpy motion. Multi-image storyboards are described as experimental ([Runware keyframes](https://runware.ai/docs/models/bfl-flux-3-video/guides/keyframes)).
- The prompt should describe the **motion between the pins** (camera path, action, pacing). The images already carry the look, so don't re-describe every pixel.

### Planning keyframes from the Blender previz (PREVIZ 01 / 08)

1. Retime the previz to **24 fps** first. If it's 25/30 fps, convert via seconds: `frame_index = round(t_seconds * 24)`.
2. Split the flight into generations of at most 20 s (prefer 8–12 s). Cut at moments where the camera is momentarily at rest or moving slowly, because extend and chaining need a "camera at rest" seam ([Runware continuation](https://runware.ai/docs/models/bfl-flux-3-video/guides/video-continuation)).
3. Within each segment, pin frames where motion **changes**: start, apex of a turn, passing through a door or window, arrival. Uniform spacing is less useful. 3–6 pins is usually enough; 10 is the ceiling. Leave at least 12 frames after the last pin.
4. Render those previz frames, then turn each into a styled still. Best practice is to generate one hero still and derive the others by **editing that same file** (e.g. FLUX.2 [pro] edit), not by independent generations. This keeps the identity and set consistent ([fal](https://fal.ai/learn/tools/how-to-use-flux-3)).
5. Write the prompt as a timestep list that matches the pins. For example, if pins are at 0/96/216, use beats `0–4s`, `4–9s`, `9–10s`, with a camera move per beat.

## 4. Draft → enhance workflow

- Call `…/draft` (720p-ish, $0.06/s). You get a `video` plus a durable `draft_cache` URL. Send **only** `draft_cache_url` to `draft-enhance` for a 1080p final ($0.29/s). Enhance keeps the same subjects, composition and motion, and "adds detail rather than replanning the scene". ([BFL blog](https://bfl.ai/blog/flux-3-video), [Runware](https://runware.ai/docs/models/bfl-flux-3-video/guides/prompting), [fal](https://fal.ai/learn/tools/how-to-use-flux-3))
- "The draft is where every creative decision gets fixed. It isn't a preview of the render. It's the render, at lower quality." Judge motion, timing, blocking and audio on the draft. Enhance won't fix them. ([fal](https://fal.ai/learn/tools/how-to-use-flux-3))
- Cache bundles persist, so you can draft many takes, review them, and enhance days later. **Store `draft_cache.url` in take metadata.**
- There's a draft variant for extend-video, but I found none documented for edit-video.

## 5. Character consistency

- Within one generation, identity holds across HARD CUTs ([Runware multi-shot](https://runware.ai/docs/models/bfl-flux-3-video/guides/multi-shot-sequences)).
- Across generations: **repeat the subject description word for word** (clothes, hair, age, build) in every prompt. "The cheapest continuity trick" ([fal](https://fal.ai/learn/tools/how-to-use-flux-3), [Morphic](https://morphic.com/resources/how-to/flux-3-guide)). Take it verbatim from the locked Cast note.
- Keep every keyframe and first/last image derived from one source image via edits. Two independently generated stills cause identity mismatch ([fal](https://fal.ai/learn/tools/how-to-use-flux-3)).
- For voice: reuse the full voice direction (person, register, recording, delivery) every time a character speaks. Compare takes by ear, because voice is directed, not a fixed identity ([BFL audio](https://docs.bfl.ml/guides/prompting_video_audio)).
- Chained extends drift in colour, audio and appearance after about 3 hops. Restart from the last clean clip instead of patching with prompts ([Runware continuation](https://runware.ai/docs/models/bfl-flux-3-video/guides/video-continuation)).

## 6. Camera language ([BFL camera terms](https://docs.bfl.ml/guides/prompting_video_camera_terms), [Runware](https://runware.ai/docs/models/bfl-flux-3-video/guides/prompting))

- Reliable: close-up / medium / wide / ECU; low, high and eye-level; POV; over-the-shoulder; pan; tilt; dolly/push-in; pull-back reveal; tracking; orbit ("orbits clockwise around…"); handheld follow; locked-off; shallow DoF; rack focus; golden hour; rim light; volumetric light.
- Unreliable: snorricam, camera roll, screen-in-screen, portal transitions, datamosh, slit-scan, morphing.
- Rule: **one framing term + one movement term + one clear subject action** per beat. Don't stack moves like "low aerial handheld orbit push-in". Add lens character ("35mm, shallow depth of field"; "70mm long lens, background compressed"). Use "locked-off" or "no camera shake" when you need stability.
- Name motion style explicitly if you want it: slow motion, timelapse, hyperlapse.

## 7. Audio

- Audio is on by default, and silence isn't free. If you name nothing you get generic or dead audio. Set `generate_audio: false` for shots the edit will score and mix separately. ([Morphic](https://morphic.com/resources/how-to/flux-3-guide))
- Four layers ([BFL audio](https://docs.bfl.ml/guides/prompting_video_audio)):
  - **Speech:** name the speaker, give the exact words in double quotes, add delivery.
  - **Ambience:** name the specific sources.
  - **Effects:** tie each to a visible action.
  - **Music:** style plus mix position, e.g. "sparse piano, low in the mix".
- Templates:
  - On camera: `[Shot]. [Character]. Says, "[line]." [Delivery]. [Ambience]. No on-screen text or subtitles.`
  - Voiceover: `Off-screen voiceover says, "[line]." …`
- Timing: "The voiceover speaks once and aims to finish by 8 seconds. For the final two seconds, only [ambience]." Short lines in long clips are safest. If the last word gets cut, shorten the line or lengthen the clip.
- Physical sounds (footsteps, impacts, engines, weather) render strongly. Abstract sounds ("held breath", "subsonic note") are weak ([fal](https://fal.ai/learn/tools/how-to-use-flux-3)).
- Multilingual (including German): label each line's language and keep one voice across the switch. Give each speaker their own turn with no overlap.
- Troubleshooting: speech rendered as captions → name the speaker, keep the quotes, add "no on-screen text or subtitles". Salesy tone → "no announcer delivery". Garbled words → remove competing voices. Busy mix → keep 1–2 layers.

## 8. Extend and edit

- **Extend:** start with "Continue the reference video from its final frames…". The source's last frame should be resolved: pose settled, camera at rest, audio at a pause. Stutter at the seam means you should regenerate the source ending, not tweak the prompt. ([Runware continuation](https://runware.ai/docs/models/bfl-flux-3-video/guides/video-continuation))
- **Edit:** "An edit prompt describes a change, not a shot." Use the shortest prompt that names the change and add placement and appearance. Anything unmentioned stays as filmed. Chain edits one change at a time. New dialogue has to fit the original speech duration, and a silent source stays silent. For restyles, describe materials and textures, not just a style name. ([BFL editing](https://docs.bfl.ml/guides/prompting_video_editing))

## 9. Failure modes (summary)

| Symptom | Fix |
| --- | --- |
| Scenes blur together / incoherent multi-beat | Timestep beats + `HARD CUT`; contrast adjacent shots; add duration |
| Content dropped at end | Fewer beats or longer duration |
| Identity drift | Verbatim subject block; keyframes edited from one source; ≤3 extend hops |
| Unwanted camera drift on stills/products | "locked-off", restate framing and light from the input image |
| Keyframe transitions morph or jump | Pins too far apart or compositions too different; add an intermediate pin |
| Call rejected | frame_index > duration×24, duplicate indices, `auto` duration on keyframes/first-last |
| Captions burned in | "no on-screen text or subtitles" |
| Over-stuffed prompt ignored | Cut to about 5–10 beats, one camera move per beat |

## 10. Example prompts

Official ([BFL t2v](https://docs.bfl.ml/guides/prompting_video_text_to_video)):

> 0.0–1.5s — locked wide of a still harbor at dawn, boats motionless on glassy water. 1.5–3.0s — a slow push-in begins as gulls lift off the water. 3.0–5.0s — the sun breaks the horizon, warm light spreads and the camera settles.

> A low tracking shot of a fox sprinting through wet pine undergrowth at dawn. Mist drifts between the trees as the camera keeps pace beside it. Cool blue morning light, fast but controlled motion, cinematic naturalism.

fal three-beat spot ([fal](https://fal.ai/learn/tools/how-to-use-flux-3)):

> It opens on a diamond necklace laid out on black velvet in total darkness, then a hard beam sweeps across it and fires the stones into colour one at a time, then a hand in a black silk sleeve lifts it clear and fastens it at the nape of a neck… Macro for the sweep, a slow push-in for the fastening, a high-contrast grade with pure black around everything. The whisper of silk, a faint chain sound, one sustained cello note and nothing else.

Sketch for this project (keyframes from previz, 10 s, pins 0/96/180/228):

> Use the pinned images as keyframes of one continuous camera flight. 0–4s — a slow dolly forward up the garden path toward the front door of the house, eye level, late-afternoon golden light. 4–7.5s — the camera glides through the open front door into the entrance hall, passing the cubby rack, steady and unhurried. 7.5–10s — the camera eases to a stop facing the kitchen and settles, locked-off. Same house, same furniture and materials as the keyframes throughout. Birdsong and a distant lawnmower outside, the door creak as we pass, the room tone of a quiet house inside. No people, no on-screen text.

## 11. Reference images and real people

- BFL Usage Policy ([bfl.ai/legal/usage-policy](https://bfl.ai/legal/usage-policy)) prohibits realistic depiction of a real person in a "sexual, intimate, degrading, defamatory, fraudulent, misleading, or otherwise abusive manner without their verified, documented, and informed consent". It also bans unlawful impersonation (name, image, **voice** or likeness) and deceptive realistic content presented without disclosure. There's no blanket ban on real people in benign content. A secondary review reports "no celebrity likenesses" ([airmore](https://airmore.ai/ai-review/flux-3-review)); I couldn't confirm that in the policy text.
- For grandpa, a real family member: a benign, affectionate depiction is in scope. Get his (or the family's) consent anyway, don't clone his real voice without consent, and don't present the space trip as real footage.
- Input images: PNG, JPEG or WebP. Video inputs: MP4 <50 MB, <15 s. `safety_tolerance` 0–4 controls moderation strictness. Only raise it if benign shots get refused.
- fal: output can be used commercially ([fal](https://fal.ai/learn/tools/how-to-use-flux-3)).

## Open questions (untested)

- Exactly how close to `duration*24` the last pin can go (the fal schema says `≤`, the fal guide says a pin at 240 fails). Test cheaply with a 5 s draft.
- Whether keyframes-to-video drafts reproduce identically after enhance with multiple pins. Verify on the first real shot.
