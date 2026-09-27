# Prompting Seedance 2.5 (fal: reference-to-video, image-to-video)

Researched 2026-09-24. Sources are cited inline. Tier: [fal] = fal docs/guides, [BD] = the ByteDance-style guide mirrored on docs.seedance.tv (the BytePlus page at docs.byteplus.com/en/docs/ModelArk/2607689 would not render for fetching), [creator] = third-party.

## 1. Endpoint facts that affect prompting

- **Reference limits: the fal API schema is stricter than the marketing copy.** The API lists **≤30 images** (30 MB each), ≤10 videos (200 MB each), ≤10 audio files, 50 files total ([fal API](https://fal.ai/models/bytedance/seedance-2.5/reference-to-video/api)). "Up to 50 image refs" is wrong. The 50 is the combined cap across all types.
- Each video/audio ref must be 1.8–30.2 s, with **≤30.2 s combined per modality**. Video refs: 24–60 fps, 300–6000 px per side, aspect 0.4–2.5. An audio ref needs at least one image or video ref alongside it ([fal guide](https://fal.ai/learn/devs/seedance-2-5-prompting-guide), [fal workflows](https://fal.ai/learn/tools/seedance-2-5-workflows)).
- Params: `resolution` 480p/720p/1080p (default 720p), `duration` auto or 4–30, `aspect_ratio` auto/21:9/16:9/4:3/1:1/3:4/9:16, `generate_audio` (default **true**, so set it false for silent shots), `seed` (reproducible, but results can still vary slightly), `task` reference/editing/extension.
- Image-to-video: `image_url` becomes frame 1. Optional `end_image_url`. Aspect is fixed to auto (follows the image). There is no `camera_fixed` and no seed input ([fal i2v API](https://fal.ai/models/bytedance/seedance-2.5/image-to-video/api)).
- **Tags are positional.** `@Image1` is the first URL in `image_urls`, and so on. Check upload order before sending: "the right description attached to the wrong reference number is still wrong" ([fal guide](https://fal.ai/learn/devs/seedance-2-5-prompting-guide)). fal's model page examples also use `[Image1]`. We use `@Image1`.
- **Cost (720p, fal):** ~$0.47/s without video refs, ~$0.28/s with video refs. **Input video seconds are billed too** (×0.6 per fal), so trim previz clips to exactly the shot length. 480p costs ~$0.22/s. Test at 480p, then re-run the winner at 720p ([fal model page](https://fal.ai/models/bytedance/seedance-2.5/reference-to-video), [fal workflows](https://fal.ai/learn/tools/seedance-2-5-workflows)).
- **1080p:** it is in the fal enum, but published price tables only list 480p/720p, and one reviewer says to use 2.0 for anything above 720p ([fal 2.5 vs 2.0](https://fal.ai/learn/devs/seedance-2-5-vs-seedance-2-0), [CellCog](https://cellcog.ai/blog/seedance-2-5-pricing/)). Check the price and quality on one shot before committing to it.

## 2. Prompt structure and length

- Official formula: **Subject + Action/Event + Scene (opt) + Visual style (opt) + Camera/Cut (opt) + Audio (opt)** ([fal how-to](https://fal.ai/learn/devs/how-to-use-seedance-2-5)).
- [BD] four parts: **asset mapping, then a one-sentence brief, then a timeline or shot order, then global constraints** ([docs.seedance.tv](https://docs.seedance.tv/en/seedance-2-5-prompting-guide)). "A basic prompt does not need a pile of adjectives."
- The full template from the fal guide, scaled to the complexity of the shot:
  ```
  FORMAT: 8s, 16:9, single take, real-time speed
  REFERENCE ROLES: @Image1 = ... only; @Video1 = ... only; do not copy ...
  STARTING STATE: positions/objects at frame 1
  TIMELINE: 0-3s ..., 3-6s ..., 6-8s ...
  CAMERA: path, framing (subject in left third), what triggers each move
  CONTINUITY: invariants (face, suit, helmet, prop, screen direction)
  AUDIO: dialogue / room tone / no music
  ENDING STATE: final frame positions
  CONSTRAINTS: no cuts, no text, no duplicated props ...
  ```
  A 2-second action doesn't need the full template. Length itself matters less than precision: Higgsfield's tested prompts run from 300 to 2000+ words ([Higgsfield](https://higgsfield.ai/blog/seedance-2-5-prompting-guide)). For our shots, aim for roughly 80–250 words.
- **Timeline ranges must be continuous** (0–3, 3–7, 7–15). An under-filled range invites improvisation. An over-filled one drops actions or makes the edit frantic ([BD]). Timestamps allocate time to events. They are **not frame-accurate** ([fal how-to](https://fal.ai/learn/devs/how-to-use-seedance-2-5)).
- **Longer durations do not add events.** Unplanned extra seconds turn into waiting, repetition or slow motion. Fill long takes with explicit beats ([fal guide](https://fal.ai/learn/devs/seedance-2-5-prompting-guide)).

## 3. References and role assignment (@ tags)

- **Give every reference exactly one job, and say what NOT to take from it.** The model does not guess that image 3 is the location ([fal guide](https://fal.ai/learn/devs/seedance-2-5-prompting-guide), [OpenArt](https://openart.ai/blog/seedance-2-5-prompt-guide/)):
  - `@Image1 controls only [identity/wardrobe/prop design]. Do not copy [pose, background, lighting, camera angle, text] from @Image1.`
  - `@Video1 controls only [camera path, framing, timing]. Do not copy [subject, wardrobe, objects, setting] from @Video1.`
  - "Do not make an image and a video reference do the same job."
- [BD] mapping style: `Images 1–2: Grandpa's appearance. Image 3: capsule interior. Video 1: reference only camera movement and timing.`
- **Use fewer references.** Start with 2–3 essential refs. Stability drops as refs increase. Official recommendation: 1–8 distinct image subjects, and for video, 1–5 subjects at 5–10 s each. Clean, well-lit, single-subject images give the best identity transfer ([fal model page](https://fal.ai/models/bytedance/seedance-2.5/reference-to-video), [fal how-to](https://fal.ai/learn/devs/how-to-use-seedance-2-5)).
- fal example: *"The woman from [Image1], wearing the jacket from [Image2], performs the dance from [Video1] on the rooftop from [Image3], hitting the beats of [Audio1]. Keep her face and the jacket exact."*

## 4. Previz / blocking video as camera reference

- This is an officially supported workflow ("blockout"). [BD] examples:
  - Coarse blockout: *"Use Video 1 only for the complete shot order, camera positions, framing changes, subject paths, and timing. Do not copy the blockout materials or character appearance."* Use this with keyframe images and add "keep character appearance consistent with each corresponding keyframe."
  - Fine blockout: *"Fully re-render Video 1 while preserving its action paths, camera movement, timing, and framing exactly. Replace the environment with ..."*
  - Global constraints they add: *"No black-and-white, illustration, storyboard line art, toy-like rendering"*, *"Do not generate motion paths, axes, or camera guides."*
- How to prepare the clip ([cozyclay](https://cozyclay.org/seedance-camera-control/), [BD]):
  - Use flat grey/clay shading with a plain sky. **Placeholder colours get copied**, so keep it monochrome.
  - Remove all UI: gizmos, grid, outlines, selection highlight, frame counter. These can show up as objects in the render.
  - Match the delivery aspect ratio. Keep geometry simple and at real scale, with a stand-in figure.
  - Match the clip length to the shot length (3–5 s is typical, minimum 1.8 s). Longer clips cost more and drift toward the end.
- Let the clip carry the camera. **Don't restate the move in text** beyond "follow @Video1's camera movement exactly". Spend the words on materials, light, wardrobe and mood ([cozyclay](https://cozyclay.org/seedance-camera-control/)).
- If the framing is off, fix it in the blockout and re-export (free) rather than re-rolling a paid generation.

## 5. Character consistency

- Use **one canonical identity**. Near-duplicate refs that disagree (nose, hair part) are the #1 cause of drift. Recommended pack: 3–5 images, each with a job: neutral portrait, full-body/turnaround, the shot's opening frame, a prop sheet ([Elser](https://www.elser.ai/news/why-seedance-2-5-character-keeps-changing)).
- Supply side and back views if the camera will orbit. Otherwise the model invents unseen geometry, and that bleeds into the face. Use a full head-and-body image, because cropped refs destabilise the face in motion ([domoai](https://domoai.app/blog/seedance-2-5-character-consistency)).
- **Avoid redesign words** like "becomes heroic", "transforms" or "more cinematic". Write visible behaviour instead ("lifts his chin, steps toward the window").
- Name the invariants concretely: "Keep the same face, white hair, orange suit with blue shoulder patch, helmet under left arm from first frame to last." Repeat them after any occlusion ([fal guide](https://fal.ai/learn/devs/seedance-2-5-prompting-guide)).
- For costumes: a clear silhouette, 2–3 colours, and one signature detail. Tiny emblems migrate.
- **Chaining shots:** use the last frame of clip N as `@Image1` with "Use @Image1 as the exact first frame and continue forward from that moment. Do not replay [previous action]." Always compare that frame against the canonical portrait first, because drift compounds across chained clips ([fal guide](https://fal.ai/learn/devs/seedance-2-5-prompting-guide), [Elser](https://www.elser.ai/news/why-seedance-2-5-character-keeps-changing)).
- Build the next shot's start frame by **editing the approved image**, not by writing a fresh text-to-image prompt ([fal workflows](https://fal.ai/learn/tools/seedance-2-5-workflows)).

## 6. Camera language

- Supported terms ([BD]): extreme wide, medium, close-up, push-in, pull-out, pan, tilt, low angle, overhead, one-take, aerial, FPV, dolly zoom. For anything else, describe the visible result, e.g. "from second 4, rack focus: foreground glass softens while the woman sharpens".
- "Dynamic" is close to useless. Give **screen position** ("keeps him in the left third"), **triggers** ("the camera does not pan until the capsule hatch is fully open") and **axis rules** ("never cross the axis"; "he always travels left-to-right") ([fal guide](https://fal.ai/learn/devs/seedance-2-5-prompting-guide), [Higgsfield](https://higgsfield.ai/blog/seedance-2-5-prompting-guide)).
- Lock a lens per segment ("Segment 2: short telephoto, shallow focus") to stop focal-length drift ([Higgsfield](https://higgsfield.ai/blog/seedance-2-5-prompting-guide)).

## 7. Multi-shot / cuts

- There is no special token. Use timed segments: `0.0s–3.0s, SEGMENT 1, wide from behind, dolly-in. 3.0s–6.0s, SEGMENT 2, close-up ...`. Land cuts on motion or dialogue, not on static poses ([Higgsfield](https://higgsfield.ai/blog/seedance-2-5-prompting-guide)).
- fal example: *"Cut on the rhythm of @Audio1, one cut per bar, four camera positions in this order: wide from across the water, low on the float, macro on the crank turning, high three-quarter as he straightens up."* ([fal workflows](https://fal.ai/learn/tools/seedance-2-5-workflows))
- Staged beats: "Stage 1 / Stage 2 / Stage 3, one primary change each, ending frame named." If the ending state is left out, transitions come early. Unordered parts get ordered by the model ([fal workflows](https://fal.ai/learn/tools/seedance-2-5-workflows)).
- A storyboard grid image (fewer than 15 panels) can define shot count, framing and order ([BD]).
- One creator's caveat: in-generation cuts aren't fully reliable. **For controlled films, generate one shot per call** and cut in the edit ([cozyclay](https://cozyclay.org/seedance-camera-control/)).

## 8. Negative instructions

- There is no negative-prompt field, so put a CONSTRAINTS line in the prompt. For references, ByteDance prefers saying **which part to use** over listing what to leave out ([OpenArt](https://openart.ai/blog/seedance-2-5-prompt-guide/)).
- Be specific and categorical, e.g. "No cuts, no slow motion, no repeated entrance, no duplicated helmet, no object teleportation." or "Only these two people exist in the entire video; no other figures." Weak version: "no people" ([fal guide](https://fal.ai/learn/devs/seedance-2-5-prompting-guide), [Higgsfield](https://higgsfield.ai/blog/seedance-2-5-prompting-guide)).
- Add "No music, no subtitles, no on-screen text" when needed, and/or set `generate_audio: false`.

## 9. Image-to-video specifics

- The still is frame 1. Split the prompt into **motion** (what changes) and **protection** (what the still got right and must stay). With `end_image_url`, don't describe the end state's visuals. Describe only sequence and timing ([fal workflows](https://fal.ai/learn/tools/seedance-2-5-workflows)).
- Mismatched first/last-frame aspect ratios can stretch the last frame ([fal how-to](https://fal.ai/learn/devs/how-to-use-seedance-2-5)).
- Identity drifts toward a generic face mid-clip when only a first frame anchors it, and re-seeding won't fix it. Add a second anchor (an end frame, or an identity ref via reference-to-video) ([search summary citing domoai](https://domoai.app/blog/seedance-2-5-character-consistency)).

## 10. Known failure modes and fixes

| Symptom | Fix |
|---|---|
| Ref bleed (background/pose of the character sheet copied) | "controls only X; do not copy Y from @ImageN" |
| Blockout look leaks (grey, toy-like, guide lines) | Monochrome clean render + "do not copy blockout materials; no toy-like rendering; no camera guides" |
| Face drift after turns or occlusion | Side/back refs, limit head rotation, re-state invariants after occlusion, cut during occlusion |
| Long take padded with slow-mo/repeats | Timeline beats that fill the duration, or shorten the duration |
| Reactions without cause, physics oddities | Write cause before reaction (contact, force, then result), and name the settling state |
| Wrong ref used | Check the URL order against the @ numbers |
| Miss on regenerate | Change **one** thing (the failed beat), keep the working wording |
| Real-person likeness | Seedance applies face-detection filtering to real people and celebrities ([MindStudio, on 2.0](https://www.mindstudio.ai/blog/seedance-2-0-content-restrictions-workarounds)). Use generated/stylised characters. |

## 11. Example prompt (our style, reference-to-video with previz)

```
Refs: @Image1 = Grandpa identity sheet (face, white hair, beard, orange flight suit) only;
do not copy its white background or pose. @Image2 = capsule interior (layout, panel colours,
porthole) only. @Video1 = camera path, framing and timing only; do not copy its grey
geometry, mannequin or flat lighting.
Brief: Grandpa floats up from his seat in zero-g and looks out of the porthole at Earth.
0-3s: seated, belts unclip, he drifts upward, hands open.
3-6s: he turns toward the porthole, face lit blue by Earth.
6-8s: he smiles and taps the glass twice.
Camera: follow @Video1's movement exactly; Grandpa stays in the right third.
Continuity: same face, hair, suit and patch from first frame to last.
Audio: capsule hum, soft belt click at 1s, two glass taps; no music, no dialogue.
Constraints: photoreal, no text, no extra people, no duplicated props, no camera guides,
no toy-like rendering.
```
Settings: 480p for iteration, then 720p for the approved take. Match `duration` to the @Video1 length. `generate_audio` as needed. Fix the `seed` while iterating on wording.
