# Prompting MiniMax H3 Max (fal) — research notes

Researched 2026-09-24. Primary sources: the official MiniMax H3 prompt guides on Hugging Face ([base](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md), [ref](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md)), [MiniMax API docs](https://platform.minimax.io/docs/guides/video-generation), the fal docs ([R2V API](https://fal.ai/models/minimax/h3-max/reference-to-video/api), [I2V API](https://fal.ai/models/minimax/h3-max/image-to-video/api), [how-to](https://fal.ai/learn/tools/how-to-use-minimax-h3-max), [prompting guide](https://fal.ai/learn/devs/minimax-h3-prompting-guide)). The rest are secondary sources.

## TL;DR

1. **Choose the endpoint by what the image is for.** If the image must be the exact opening frame (or opening and closing frame), use `image-to-video` (`image_url` plus optional `end_image_url`). If images are references for identity, wardrobe, location or style, and you may also have a motion video, use `reference-to-video`. Don't mix the two. On the native API, a first frame sent alongside refs is silently dropped and you are still charged in full ([AtlasCloud](https://www.atlascloud.ai/blog/tips/minimax-h3-reference-to-video)).
2. **Give every reference one explicit job:** "Image 1 is grandpa: preserve his face, white beard, glasses. Image 2 is the wardrobe. Video 1 provides only the camera move." fal's docs call this out as the biggest lever ([fal guide](https://fal.ai/learn/devs/minimax-h3-prompting-guide)).
3. **Write the prompt as a timeline in plain English, not as tags.** Pick 1 subject, 1 action and 1 main camera move per shot. Describe the sound too, because every clip gets native audio.
4. **Prompt expansion:** keep `balanced` (the default) for short or plain prompts. Use `disabled` once you have a long, structured prompt that already works, because expansion "can overwrite a long one" ([fal how-to](https://fal.ai/learn/tools/how-to-use-minimax-h3-max)). Skip `quality`: it adds about 30 s.
5. **Camera:** use the official natural-language form "motion type + amplitude + speed + target". Bracket tags are optional at best (details below).

## Endpoint facts (fal)

- **R2V:** `reference_image_urls` (≤9), `reference_video_urls` (≤3, 2–15 s each, ≤15 s total), `reference_audio_urls` (≤3, same limits), ≤12 files in total. Audio needs at least one image or video alongside it.
  - Other params: `aspect_ratio` (default `adaptive`, or 21:9/16:9/4:3/1:1/3:4/9:16), `resolution` 480P/768P/1080P (default 768P), `duration` (default 5, max 15), `seed`, `enable_safety_checker` (default true).
  - Refer to files by modality and upload order: `Image 1`, `Video 1`, `Audio 1`. Numbering runs separately for each modality ([fal R2V API](https://fal.ai/models/minimax/h3-max/reference-to-video/api)).
- **I2V:** `image_url` (first frame), `end_image_url` (turns the call into first-to-last keyframe interpolation), optional `target_audio_url`. Aspect ratio follows the image ([fal I2V API](https://fal.ai/models/minimax/h3-max/image-to-video/api)).
- **Prompt length:** up to ~7,000 characters on fal ([fal guide](https://fal.ai/learn/devs/minimax-h3-prompting-guide)). Timestamped beats must add up to exactly `duration`. If they don't, the last beat has nowhere to go ([fal how-to](https://fal.ai/learn/tools/how-to-use-minimax-h3-max)).
- **Price:** $0.05/s at 480P, $0.08/s at 768P. Reference files are nearly free: the first 4,096 tokens cost nothing, then $0.02 per 1k tokens. Adding more reference images does not change the per-second price ([fal how-to](https://fal.ai/learn/tools/how-to-use-minimax-h3-max), [AtlasCloud](https://www.atlascloud.ai/blog/tips/minimax-h3-reference-to-video)).
- **Validation is late:** the native API returns HTTP 200 for bad requests and only fails 2–3 minutes later ([AtlasCloud](https://www.atlascloud.ai/blog/tips/minimax-h3-reference-to-video)). Check outputs; don't trust the submit response.

## How the model actually reads prompts (important)

The released checkpoint is driven by a structured "Context IR" rather than a raw sentence ([HF README](https://huggingface.co/MiniMaxAI/MiniMax-H3) via [mold#1434](https://github.com/utensils/mold/issues/1434)). fal's `balanced`/`quality` expansion rewrites your plain prompt into that form. That is why one-line prompts work with expansion on and do poorly with it off.

- **Base / I2V / first-last frame format:** an instruction line followed by three fields ([base guide](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md)):
  - Instruction line, e.g. "Picture 1 aligns with 0.00 s; Picture 2 aligns with the 8.00 s mark".
  - `integrated_multimodal_description:` holds the visuals, action and dialogue in `[Shot 1]` blocks.
  - `overall_soundscape:` has 1–4 sentences of ambience and foley.
  - `non_diegetic_music:` has 1–3 sentences, or `N/A`.
- **Reference format:** `subject_definitions`, `summary` (with a task tag such as `[reference generation]`), `retention_analysis`, `detailed_description` (350–500 words for generation), `overall_soundscape`, `non_diegetic_music` ([ref guide](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md)).
  - Labels in this format are `<Subject N>`, `<Picture N>`, `<Video N>`, `<Audio N>`.
  - Each label gets a retention marker: `fully_preserved`, `partially_preserved`, `attribute_transfer` or `weak_reference`.
- **Practical rule:** with expansion `disabled`, write in this structured format or something close to it. With `balanced`, plain English with "Image 1 / Video 1" roles is enough. Untested: whether fal maps "Image N" to `<Picture N>` when you paste the structured format with expansion disabled. Run an A/B test before relying on it.

## Referencing images and videos; assigning roles

- **One line per asset, one role each:**
  - identity: face and hair
  - wardrobe
  - location
  - style or grade
  - storyboard/keyframe
  - motion
  - voice

  Example: "Image 1 is the female protagonist. Image 2 is her small dog." ([fal R2V API](https://fal.ai/models/minimax/h3-max/reference-to-video/api)). Official form: "<Subject 1> is the woman whose appearance comes from <Picture 1> and whose walking motion comes from <Video 1>" ([ref guide](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md)).
- **State what to preserve and what to change:** "keep the face from Image 1 and the camera move from Video 1" ([Picsart](https://picsart.com/blog/minimax-prompting-guide/)).
- **Storyboard-style sequences:** "Use Images 1–4 as sequential keyframes…" ([fal guide](https://fal.ai/learn/devs/minimax-h3-prompting-guide)).

## Reference video for camera motion only

- Classify it as `reference generation`, not editing or continuation, and describe the move in plain words inside the shot ([ref guide](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md)).
- **Say explicitly what transfers and what doesn't:** "Video 1 provides only the camera path (slow half-orbit, then push in). Do not copy its subject, set, lighting or audio."
- **Gotcha:** a reference video's colour grade leaks into the output even when the prompt asks for different lighting ([AtlasCloud](https://www.atlascloud.ai/blog/tips/minimax-h3-reference-to-video)). Use a neutral or grey-box clip for camera reference, or say "ignore the colour and lighting of Video 1".
- **Its audio also transfers** unless you say otherwise. Mark it as `weak_reference`, or write "no audio from Video 1".
- **Motion-transfer example (fal):** "Match the action in Video 1 from a locked-off wide camera. Replace the three suited men with three highly photoreal capybaras. Preserve the original movement path exactly."

## Character consistency

- **Across shots, use R2V with the same reference images and the same identity paragraph, word for word, every time.** Changing adjectives between calls produces a different person ([fal how-to](https://fal.ai/learn/tools/how-to-use-minimax-h3-max)).
- **List concrete anchors:** "Preserve his oval face, white short beard, round tortoiseshell glasses, grey cardigan…" ([fal guide](https://fal.ai/learn/devs/minimax-h3-prompting-guide), [RunDiffusion](https://www.rundiffusion.com/minimax-h3-prompt-guide)).
- **Use 2–3 compatible identity images:** a face close-up, full body, and an optional detail shot. Conflicting references cause drift ([RunDiffusion](https://www.rundiffusion.com/minimax-h3-prompt-guide)).
- **Face drift usually means the role was never declared.** Say "preserved exactly" (`fully_preserved` in the IR) ([aireiter summary of official guide](https://aireiter.com/blog/minimax-h3-prompt-guide)).
- **Fix a seed** while you iterate on the prompt.

## Camera vocabulary

- **Official moves** ([base guide](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md)):
  - Zoom In/Out
  - Push In/Pull Out
  - Pan Left/Right
  - Truck Left/Right
  - Tilt Up/Down
  - Pedestal Up/Down
  - Arc Shot
  - Tracking Shot
  - Static Shot
  - Shake Slightly/Strongly
  - POV
  - Roll Clockwise/Counterclockwise
- **Official form:** "The camera pushes in with small amplitude at slow speed toward the folded letter in her hands." That is type + amplitude ("small/large amplitude") + speed ("slow/fast speed") + target.
  - Medium amplitude and normal speed are the defaults and can be left out.
  - Always end the move on a target: what it reveals, or where it settles ([aireiter](https://aireiter.com/blog/minimax-h3-prompt-guide)).
- **Brackets:** Hailuo-02/Director used `[Pan left]`-style commands. For H3:
  - The HF prompt guide uses natural language only.
  - Square brackets in H3's format mean shot markers (`[Shot 1]`) and task tags.
  - MiniMax's API page still says tags like `[pan]`, `[zoom]`, `[static]` can follow key descriptions ([platform docs](https://platform.minimax.io/docs/guides/video-generation)).
  - **Recommendation:** natural language. Brackets are tolerated but add nothing, and they can be confused with shot markers.
- **Other camera rules:**
  - One main move per shot. Don't combine "locked camera" with "orbit" ([camera guide](https://minimaxh3videogenerator.com/guides/minimax-h3-camera-prompts)).
  - If the subject rotates when you wanted the camera to move, write "the subject stays fixed; only the camera arcs".
  - Dolly and tilt are reliable; pans have a limited range (secondary sources).
  - Lens and film language is understood, e.g. "wide angle lens with strong perspective distortion" or "fine grain, soft highlight halation" ([fal guide](https://fal.ai/learn/devs/minimax-h3-prompting-guide)).
- **Portraits:** add a subtle camera move. Otherwise the result looks like "a photograph with motion painted on" ([fal how-to](https://fal.ai/learn/tools/how-to-use-minimax-h3-max)).

## Audio and dialogue (native audio is always generated)

- **Name real sound sources:** footsteps, the room tone, the moment a cue lands. Vague mood words leave the audio empty ([fal how-to](https://fal.ai/learn/tools/how-to-use-minimax-h3-max)).
- **If you don't want a score, say so:** "No music" or `non_diegetic_music: N/A`. Otherwise you get unwanted music ([aireiter](https://aireiter.com/blog/minimax-h3-prompt-guide)).
- **Dialogue format** in the official format: `(S1) says <d>[English] line</d>` ([base guide](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md)).
  - In the official format, quotation marks mean visible on-screen text, so quoted dialogue can end up as burned-in subtitles.
  - fal's plain-English advice is the opposite ("dialogue inside double quotes"), which works with expansion on.
  - For voiceover, write "off-screen voiceover, lips remain closed".
  - If we add the VO in post, say "no dialogue, no speech".

## Failure modes → fixes

| Symptom | Fix |
|---|---|
| Output ignores or merges references | Give each asset one explicit role; remove conflicting images |
| Face or identity drift between shots | Use the identical identity paragraph and the same refs every call; say "preserve exactly" |
| First frame not respected | You used R2V; use I2V `image_url` for an exact first frame |
| Grade or audio from motion video leaks in | Use a neutral camera-ref clip; say "camera path only" |
| Slideshow or pacing drift | Timestamped beats (`[0–2 s] … [2–5 s] …`) that add up to the duration |
| Camera barely moves or wanders | One move, with amplitude, speed and a target |
| Unwanted text, subtitles or garbled glyphs | "No on-screen text, no subtitles"; avoid quotes in the disabled/IR mode |
| Morphs or dissolves in stylised prompts | "No soft dissolves or fluid morphs, no hard cuts" ([fal guide](https://fal.ai/learn/devs/minimax-h3-prompting-guide)) |
| Long careful prompt gets rewritten | `prompt_expansion_mode: "disabled"` |

## Real-person reference images

- **The official guides don't restrict real faces;** they only ask for permission and consent ([RunDiffusion](https://www.rundiffusion.com/minimax-h3-prompt-guide)).
- **Moderation:** it is automated and covers inputs and expanded prompts. It blocks impersonation, sexual content involving real people, and infringing content.
- **Reported behaviour:** real people reportedly get stricter handling than invented characters, and false positives happen ([AtlasCloud](https://www.atlascloud.ai/blog/tips/minimax-h3-reference-to-video)).
- **For grandpa photos:** family photos with consent should pass. If a ref is blocked, try a cleaner and less ambiguous crop before rewording. `enable_safety_checker` defaults to true on fal.

## Example prompts

**I2V, first + end frame (plain English, balanced):**
> Start frame: the uploaded photo. Hold the framing, clothing and light exactly, then let the scene run forward. Grandpa leans toward the capsule window as the camera pushes in with small amplitude at slow speed, settling on his reflected face in the glass as the Earth drifts into view behind it, ending on the composition of the end frame. Sound: soft cabin hum, a faint creak of the seat, his quiet exhale. No music, no dialogue, no on-screen text.

**R2V, identity refs + camera-only video (plain English, balanced):**
> Image 1 is Grandpa: preserve his face, white short beard and round glasses exactly. Image 2 is his wardrobe: the orange flight suit with a NASA-style patch. Image 3 is the spacecraft interior (location and lighting). Video 1 provides only the camera path: a slow half-orbit around a seated person ending in a push-in. Do not copy its subject, colours or audio. Grandpa sits in the pilot seat of Image 3 and turns to look out of the window, smiling. The camera arcs around him at slow speed, then pushes in with small amplitude to a close-up of his eyes. Soft ventilation hum, switch clicks. No music. No on-screen text.

**R2V, official IR form (use with `prompt_expansion_mode: "disabled"`):**
```
subject_definitions:
<Subject 1> is the elderly man in <Picture 1>, with a white short beard, round tortoiseshell glasses and a grey cardigan.
<Subject 2> is the spacecraft cockpit in <Picture 2>.
summary:
[reference generation] <Subject 1> sits in <Subject 2> and looks out at Earth; the camera path follows <Video 1>.
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - face, beard, glasses, cardigan.
<Subject 2> (appears in [Shot 1]): fully_preserved - panel layout, window shape, warm cabin light.
<Video 1>: weak_reference - camera path only; subject, grade and audio are not used.
detailed_description:
Live-action, cinematic, soft warm cabin light. [Shot 1] <Subject 1> sits in <Subject 2> ... The camera performs an arc shot at slow speed, then pushes in with small amplitude toward his eyes as Earth's blue limb fills the window.
overall_soundscape:
Low ventilation hum, soft switch clicks, fabric rustle as he turns.
non_diegetic_music:
N/A
```
