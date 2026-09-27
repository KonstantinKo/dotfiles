# Prompting Kling 3 on fal: research (2026-09-24)

Legend: **[schema]** read from the fal OpenAPI schema today (`https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=<id>`); **[verified]** read in an official Kling or fal doc; **[reported]** third-party blog or test; **[uncertain]** weak, single or inferred source.

## 1. Endpoints and inputs (fal)

The fal model list for "kling v3" returns 12 video endpoints: v3 `standard|pro|4k` x `text-to-video|image-to-video`, `turbo/standard|pro` x `t2v|i2v`, and `standard|pro/motion-control`. There is no `v3/*/reference-to-video`. The multi-image reference endpoint is **O3** (`fal-ai/kling-video/o3/{standard,pro}/reference-to-video`). [schema] https://fal.ai/api/models?keywords=kling%20v3

**`v3/{standard,pro,4k}/image-to-video`** takes the same fields on all three tiers. [schema]
- `start_image_url` is required. `end_image_url` (the tail frame) is optional.
- Image limits: ≥300px per side, aspect ratio 0.4 to 2.5, ≤50MB.
- `prompt` (≤2500 chars) or `multi_prompt`, but not both.
  - `multi_prompt` is a list of `{prompt, duration 1-15}` items.
  - `shot_type` is `customize` or `intelligent`.
- `duration`: "3" to "15" (string), default "5".
- `negative_prompt`: default `"blur, distort, and low quality"`, ≤2500 chars.
- `cfg_scale`: default 0.5.
- `generate_audio`: **default true**. Voice output is Chinese or English; other languages are auto-translated to English. Write English speech in lowercase and acronyms or proper nouns in uppercase.
- `elements[]`: see §4.
- There is no `aspect_ratio` field. The output follows the start image. [inferred, uncertain]

**`v3/{standard,pro,4k}/text-to-video`** takes the same fields minus the images, plus `aspect_ratio` (16:9, 9:16 or 1:1). [schema]

**`v3/turbo/{standard,pro}/image-to-video`** is stripped down. [schema]
- It takes only `image_url`, `prompt`, `multi_prompt` (1-6 shots, ≤15s in total) and `duration` (3-15).
- It has **no end frame, no elements, no negative prompt, no cfg and no audio toggle**.
- Turbo Pro is 1080p at $0.14/s. Turbo Standard is 720p at $0.112/s. [reported] https://fal.ai/learn/tools/fastest-ai-video-generation-models

**`v3/{standard,pro}/motion-control`** [schema]
- Required: `image_url`, `video_url` and `character_orientation` (`image` or `video`).
- Optional: `prompt` (≤2500), `keep_original_sound` (default true), and `elements` (at most 1 face element, only when orientation is `video`).
- Orientation sets the length limit: **`video` allows up to 30s and suits complex motion. `image` allows up to 10s and suits following camera movements.**
- The reference video "should contain a **realistic style character** with entire body or upper body visible, including head".
- The character in the image should "occupy more than 5% of the image area".

**`o3/pro/reference-to-video`** [schema]
- Inputs: `start_image_url`, `end_image_url`, `elements` (`@Element1`), `image_urls` (style or appearance refs, `@Image1`), `aspect_ratio`, 3-15s, `multi_prompt`.
- `generate_audio` defaults to **false** here.
- "Maximum 4 total (elements + reference images) when using video."
- `o3/pro/video-to-video/reference` takes an `@Video1` ref of 3-15s, elements and image_urls.

**Pricing for v3 Pro** [verified] https://fal.ai/learn/tools/how-to-use-kling-3-0-pro

| Mode | Price |
|---|---|
| Plain, audio off | $0.112/s |
| Plain, audio on | $0.168/s |
| With elements, audio off | $0.224/s |
| With elements, audio on | $0.336/s |
| Motion control | $0.168/s flat |

**Set `generate_audio:false` unless you want the model's audio.** Leaving it on silently costs 1.5x.

## 2. Prompt structure and length

- **Write it like direction for a scene, not a list of objects.** Order: environment first, then subject, action, camera, and sound. [verified] https://blog.fal.ai/kling-3-0-prompting-guide/
  - Kling's own formula is Subject / Action / Scene / Camera / Lighting+Mood, in "plain, readable language". [verified] https://kling.ai/blog/kling-ai-prompt-guide
- **For i2v, "treat the input image as an anchor"**: describe how the scene *evolves*, not what is already visible. [verified] https://blog.fal.ai/kling-3-0-prompting-guide/
- **Use explicit motion verbs and name real light sources.** Comma-separated keyword lists fail because they carry no spatial or temporal order. [verified] https://fal.ai/learn/tools/how-to-use-kling-3-0-pro
  - Name sources such as "golden hour", "fluorescent tubes" or "candlelight", not "dramatic lighting". [reported] https://www.atlabs.ai/blog/kling-3-0-prompting-guide-master-ai-video-generation
- **Length:** the hard cap is 2500 chars. No official optimum is published.
  - fal's own examples run 2-5 sentences (about 40-80 words). [verified] https://fal.ai/learn/tools/how-to-use-kling-3-0-pro
  - Recommendation: keep one shot to about 1 beat and about 60-100 words. [uncertain: inferred from the examples]
  - "Biggest mistake: cramming an entire film into one prompt." [reported] https://morphic.com/resources/how-to/kling-3.0-guide
- **Duration:** 3-6s clips show tighter consistency. Single shots longer than about 6s risk coherence drift. [verified] https://fal.ai/learn/tools/how-to-use-kling-3-0-pro
- **Multi-shot:** use up to 6 shots and label each one ("Shot 1, profile shot of …, cinematic handheld. Shot 2, …"). On fal, use `multi_prompt` with a duration per shot. [verified] https://kling.ai/quickstart/klingai-video-3-model-user-guide, https://blog.fal.ai/kling-3-0-prompting-guide/

## 3. First and last frame

- **The end frame must be similar to the start frame.** Kling says: "Choose two similar images with the same theme for smoother transitions." "Large differences may trigger a lens switch", meaning the model inserts a cut instead of a move. [verified] https://kling.ai/quickstart/ai-video-start-end-frames
  - Kling's examples are small state changes in a fixed framing: a glass filling, a candle lighting, an expression change. The same page notes that start/end generations are about 5s. That may be outdated for v3; the fal schema allows 3-15 with an end frame. [verified + uncertain]
- **Use the end frame for** controlled transitions, loops and product reveals. [verified] https://fal.ai/learn/tools/how-to-use-kling-3-0-pro
- **In Video 3.0 you can bind up to 3 elements on top of the start and end frames**, and "the elements must appear in the reference frames". [reported, citing the Kling guide] https://kling.ai/quickstart/klingai-video-3-omni-model-user-guide (via search summary)
- **For our use:** if we have board A and board B, use the end frame only when the camera and layout are close. Otherwise make two clips and cut between them.

## 4. Elements for character consistency

- **Shape on fal:** `elements: [{frontal_image_url, reference_image_urls: [1-3], video_url?, voice_id?}]`. Refer to them in the prompt as `@Element1`, `@Element2`. Only one element per request may use a video. Element videos are 3-10s, 720-2160px, 24-60fps. [schema]
- **Kling's guidance:** 1 frontal image plus 1-3 extra angles, all showing the same subject. A front-facing main image gives "higher consistency". [verified] https://kling.ai/quickstart/klingai-element-library-3-user-guide
  - For faces, use a front view plus left and right profiles, and a neutral expression plus the target expressions. [verified] https://kling.ai/quickstart/motion-control-user-guide
  - A video element (3-8s, single speaker) captures appearance *and* voice. [verified] https://kling.ai/quickstart/klingai-element-library-3-user-guide
- **Keep the prompt description in step with the refs:** clothing, hair, props and role. [reported] https://www.atlabs.ai/blog/kling-3-0-prompting-guide-master-ai-video-generation
- **Reference sets:** keep "identical lighting and style across ref angles". [reported] https://www.atlascloud.ai/blog/tips/solving-character-inconsistency-a-guide-to-kling-3.0-image-to-video-mode
- **Voice:** once an element has a voice bound, don't restate its tone in the prompt. [verified] https://kling.ai/quickstart/klingai-video-3-model-user-guide
- **Several characters:** Kling claims three or more characters stay distinct ("multi-character coreference"). [verified, vendor claim] https://fal.ai/learn/tools/how-to-use-kling-3-0-pro
- **Cost:** elements double the price per second (see §1).

## 5. Motion control with a previz video

- **The split:** the reference video drives body motion. The prompt drives background, lighting and (in `image` mode) camera. **Don't describe the action in the prompt.** fal's own example prompt is just "A man dancing". [verified] https://kling.ai/quickstart/motion-control-user-guide, https://fal.ai/learn/tools/how-to-use-kling-3-0-pro
- **Choose the camera source through orientation.** [verified] https://kling.ai/quickstart/motion-control-user-guide
  - `video`: movements, expressions, **camera work** and orientation all follow the reference.
  - `image`: motion follows the reference, orientation follows the image, and the camera comes from the prompt (zoom in/out, pan, fixed).
  - To use previz **as the camera source**, pick `video`. To keep the board's framing and add a simple move, pick `image`.
- **Conflict:** the same Kling page says the action video should be a "single continuous shot … avoid cuts, scene changes, or camera movements". So camera moves in the reference are officially discouraged even though `video` mode transfers camera work. [verified; the conflict is in the source] **Test a slow previz move before relying on it.**
- **Stylised previz is a gamble.**
  - fal's schema asks for a "realistic style character" in the reference.
  - Kling says "real human actions recommended; certain stylized humanoid … proportions can be recognized". [schema] + [verified] https://kling.ai/quickstart/motion-control-user-guide
  - A grey-mannequin or low-poly previz may extract poorly. [uncertain] Filming a real person acting the blocking is the safer input.
- **Rules for the reference clip:** [verified] https://kling.ai/quickstart/motion-control-user-guide, https://kling.ai/blog/fix-ai-video-drift-consistency-guide
  - One person. If several people are visible, the one with the largest on-screen presence is picked.
  - Whole body and head visible, with no occlusion.
  - Steady, moderate motion. Fast spins make limb glitches.
  - A clean background.
  - Framing matched to the image: portrait ref for a portrait image, full body for full body.
  - Match the body orientation between the image and the ref.
- **Failures:** extraction needs at least 3s of usable motion, and credits are not refunded if it fails. Complex motion can produce output shorter than the input. A face element that differs a lot from the first-frame face can degrade the face. [verified] https://kling.ai/quickstart/motion-control-user-guide
- **Audio:** `keep_original_sound` defaults to true. Set it to false for previz with scratch audio. [schema]

## 6. Camera vocabulary

- **Kling's list:** close-up, wide shot, low angle, slow push-in, pan, tilt, tracking shot, extreme close-up, medium close-up, full body shot, establishing wide shot. [verified] https://kling.ai/blog/kling-ai-prompt-guide
- **Also recognised:** profile shot, macro close-up, POV, shot-reverse-shot. [verified] https://blog.fal.ai/kling-3-0-prompting-guide/
  - Plus dolly push, whip-pan, shoulder-cam drift, crash zoom and snap focus, instead of "moves" or "goes". [reported] https://www.atlabs.ai/blog/kling-3-0-prompting-guide-master-ai-video-generation
- **Define the camera's relation to the subject over time**, for example "camera follows from behind, then …, holds medium shot". [verified] https://blog.fal.ai/kling-3-0-prompting-guide/
  - If you don't specify the camera, you get a static or subtly drifting shot. [verified] https://fal.ai/learn/tools/how-to-use-kling-3-0-pro
- **For stability:** "fixed lens", "tripod", "35mm" [verified] https://kling.ai/blog/fix-ai-video-drift-consistency-guide
  - A tracking camera moving at the subject's speed, and "heel-to-toe" to avoid gliding walks. [reported] https://www.atlascloud.ai/blog/guides/mastering-kling-3.0-10-advanced-ai-video-prompts-for-realistic-human-motion

## 7. negative_prompt and cfg_scale

- **cfg:** 0.5 by default. Use 0.3 for more freedom and 0.7 for tight spatial requirements. Raise it only when needed. [verified] https://fal.ai/learn/tools/how-to-use-kling-3-0-pro
- **negative_prompt:** keep the default. Add terms only for artifacts you actually see, such as warped faces or jittery camera. [verified] https://fal.ai/learn/tools/how-to-use-kling-3-0-pro
  - Kling suggests excluding "blur, distort, extra limbs, shaky camera". [verified] https://kling.ai/blog/fix-ai-video-drift-consistency-guide
  - Creators add "morphing, inconsistent face, changing clothes". [reported] https://www.atlascloud.ai/blog/tips/solving-character-inconsistency-a-guide-to-kling-3.0-image-to-video-mode
  - Neither field exists on turbo, motion-control or O3. [schema]

## 8. Audio and dialogue

- **Dialogue format:** `[Character A: Grandpa, warm raspy voice]: "…"`. Link lines with "Immediately," or "Pause,". Use unique labels, not pronouns. Describe the action before assigning the line. [verified] https://blog.fal.ai/kling-3-0-prompting-guide/
- **Languages:** Kling's app lists Chinese, English, Japanese, Korean and Spanish, plus accent tags. [verified] https://kling.ai/quickstart/klingai-video-3-model-user-guide
  - On fal, the schema says Chinese and English only, with other languages auto-translated to English. **German dialogue is therefore not viable through the fal v3 endpoints.** [schema]
- **Recommendation:** since we record VO separately, generate with `generate_audio:false`. That is cheaper and avoids unwanted lip movement. Ambient sfx may still be worth a test. [recommendation]

## 9. Failure modes (quick list)

- **Keyword lists or vague verbs** give static or random motion. [verified] https://fal.ai/learn/tools/how-to-use-kling-3-0-pro
- **Single shots over about 6s drift.** [verified] same source
- **A start and end frame that are too different** trigger a cut ("lens switch"). [verified] https://kling.ai/quickstart/ai-video-start-end-frames
- **Human motion artifacts:** sliding feet, floating arms, morphing hands. [reported] https://www.atlascloud.ai/blog/guides/mastering-kling-3.0-10-advanced-ai-video-prompts-for-realistic-human-motion
- **Moderation:** Kling checks the prompt, the input image and the output frames. A flagged output is a generic "Generation Failed", not a specific code. [reported] https://www.atlascloud.ai/blog/guides/kling-ai-nsfw-policy (now returns 410), https://magiclight.ai/academy/kling-ai-censorship/
  - A "2026 sensitivity update" is said to block swimwear, dance-fitness and fashion refs. [reported, uncertain] https://anycap.ai/page/en-US/news/kling-ai-nsfw-policy-developers

## 10. Realistic or real-person faces and minors

**No documented face gate like Seedance's.** Kling's model, element and motion-control guides contain **no** prohibition on uploading realistic human faces. The motion-control guide *asks* for "clear facial close-ups". [verified] https://kling.ai/quickstart/klingai-element-library-3-user-guide, https://kling.ai/quickstart/motion-control-user-guide

**What Kling's terms and policies do say:**
- **Terms of use:** you must hold the rights or "legal authorization" to the input, and it must not infringe "personality rights". This is a legal duty, not a technical filter. [verified] https://kling.ai/docs/user-policy
- **Community policy:** respect others' "likeness". No sexualised or "inappropriate staged" content using "images or likenesses of minors or virtual minors". CSAM is banned. [verified] https://kling.ai/docs/community-policy
  - **There is no ban on non-sexual depictions of children.** [verified by absence; uncertain whether an undocumented classifier stricter on minors exists]

**What happens in practice:**
- Photoreal faces pass on fal Kling O3 Pro. A person-shot bake-off passed 3/3 on Kling O3 Pro where Seedance blocked the same faces. [reported] https://github.com/warsha-marketing/agent-media-app/issues/25
- Creator comparisons recommend Kling specifically for photoreal humans. [reported] https://www.mindstudio.ai/blog/seedance-2-0-content-restrictions-workarounds
- Blog posts claim Kling blocks public figures and celebrities, and private individuals "without explicit legal authorization", with a 400 error or security rejection. **No primary source is cited, and "authorization" cannot be checked technically.** Treat the celebrity or politician block as likely. [reported, uncertain] https://www.glbgpt.com/resources/ai-video-human-face-seedance-veo-kling/

**fal's side:**
- The acceptable-use policy bans non-consensual deepfakes or impersonation, NCII and any sexualisation of minors. [verified] https://fal.ai/legal/acceptable-use-policy
  - It says third-party providers "may apply their own safeguards". fal documents no face filter of its own.
  - fal accounts are 18+.
- fal's model page lists no face or real-person limitations. [verified] https://fal.ai/models/fal-ai/kling-video/v3/pro/motion-control

**Implications for this project:**
- An AI-generated photoreal grandpa, or a consented family photo, is expected to work on Kling v3/O3.
- Non-sexual child characters are within policy.
- Keep a consent note for any real family member's likeness (Kling ToS §4.3).
- Before committing a shot list, **smoke-test one face sheet as an element** (3s, audio off, about $0.67 on pro with elements). This is the only way to confirm there is no hidden classifier. [recommendation]

## 11. Example prompts (adapted to our use)

- **i2v (fal's example):** "The figure walks slowly along the stone path toward the cliff edge. His cloak billows in the wind. Camera follows from behind, then he stops at the edge and slowly turns to face the valley below. Golden hour light catches dust in the air." [verified] https://fal.ai/learn/tools/how-to-use-kling-3-0-pro

- **i2v with element (ours, untested):**
  > Inside the cramped capsule, @Element1 floats up from his seat, eyes widening; a pen drifts past his face. Slow push-in from medium to close-up, fixed lens, soft blue instrument-panel glow from below, warm sunlight through the round porthole. He reaches out and gently catches the pen, then smiles.
  - Settings: `duration:"5"`, `generate_audio:false`, `cfg_scale:0.5`, default negative + "morphing, inconsistent face".

- **multi_prompt:**
  - `[{prompt:"Wide establishing shot, the rocket on the pad at dawn, steam venting, static tripod.", duration:"3"}, {prompt:"Close-up of @Element1 in the helmet, visor reflecting the countdown lights, slow push-in.", duration:"3"}]` [pattern verified: https://kling.ai/quickstart/klingai-video-3-model-user-guide]

- **motion-control** (orientation `image`, camera from prompt):
  > Grandpa in a white spacesuit on a grey lunar plain, black sky, Earth low on the horizon, hard sunlight, slow dolly-in.
  - Leave the action out; it comes from the ref video. [pattern verified: https://kling.ai/quickstart/motion-control-user-guide]
