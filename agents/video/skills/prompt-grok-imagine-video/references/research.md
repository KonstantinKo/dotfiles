# Prompting Grok Imagine Video 1.5 (fal: image-to-video, reference-to-video, text-to-video, extend, edit)

Researched 2026-09-24. Sources are cited inline. Tier: [xAI] = docs.x.ai / x.ai news, [fal] = fal model pages and llms.txt schemas, [creator] = third-party. **(?)** marks an uncertain or unverified claim.

## 1. Endpoint facts that affect prompting

| fal endpoint | Inputs (fal) | Duration | Resolution | Price (fal) |
|---|---|---|---|---|
| `v1.5/image-to-video` | `prompt`, `image_url`, `duration`, `resolution` (**no aspect_ratio**, so it follows the image) | 1–15 s, default 6 | 480p / 720p / **1080p**, default 720p | $0.08 / $0.14 / $0.25 per s |
| `v1.5/reference-to-video` | `prompt`, `reference_image_urls` (1–7), `duration`, `resolution`, `aspect_ratio` | 1–15 s, default 8 | 480p / 720p only, **default 480p** | $0.08 / $0.14 per s, +$0.01 per ref |
| `v1.5/text-to-video` | `prompt`, `duration`, `resolution`, `aspect_ratio` | 1–15 s, default 6 | 480p / 720p / 1080p | same as i2v |
| `extend-video` (older model) | `prompt`, `video_url` (MP4, 2–15 s), `duration` | adds **2–10 s**, default 6 | follows the input | $0.05–0.07/s out + $0.01/s in |
| `edit-video` (older model) | `prompt`, `video_url`, `resolution` auto/480p/720p | input is **resized to ≤854×480 and truncated to 8 s** | ≤720p | same as extend |

Sources: fal llms.txt for [i2v](https://fal.ai/models/xai/grok-imagine-video/v1.5/image-to-video/llms.txt), [r2v](https://fal.ai/models/xai/grok-imagine-video/v1.5/reference-to-video/llms.txt), [t2v](https://fal.ai/models/xai/grok-imagine-video/v1.5/text-to-video/llms.txt), [extend](https://fal.ai/models/xai/grok-imagine-video/extend-video/llms.txt) and [edit](https://fal.ai/models/xai/grok-imagine-video/edit-video/llms.txt). fal has no v1.5 extend or edit endpoint: `.../v1.5/extend-video` and `.../v1.5/edit-video` return nothing.

- **Max duration is 15 s** for t2v, i2v and r2v. xAI confirms this: "On grok-imagine-video-1.5, max duration is 15 seconds", and r2v is "capped at 720p" ([xAI r2v](https://docs.x.ai/developers/model-capabilities/video/reference-to-video), [xAI generation](https://docs.x.ai/developers/model-capabilities/video/generation)). A community guide's "r2v ≤10 s" is out of date ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)).
- Output is 24 fps MP4 ([fal r2v API](https://fal.ai/models/xai/grok-imagine-video/v1.5/reference-to-video/api)).
- **The fal r2v wrapper exposes only a subset of the xAI API.** Native xAI r2v also has `reference_audios` (preset voices tagged `<AUDIO_0..2>`), `image` (pinned first frame combined with refs), `last_frame`, and up to 4 `keyframes` on a 1/3-s grid ([xAI r2v](https://docs.x.ai/developers/model-capabilities/video/reference-to-video)). fal lists none of these, although its pricing text mentions "reference audio… included" ([fal r2v llms.txt](https://fal.ai/models/xai/grok-imagine-video/v1.5/reference-to-video/llms.txt)). **(?)** Treat them as unavailable on fal until tested. First+last frame or a pinned first frame with character refs requires the direct xAI API.
- **You pay for blocked requests:** "When the request is deemed to be in violation of xAI terms the generation of the request will still be charged" ([fal r2v API](https://fal.ai/models/xai/grok-imagine-video/v1.5/reference-to-video/api)). Moderation false positives cost money.
- On xAI, t2v runs as text-to-image and then image-to-video internally ([xAI generation](https://docs.x.ai/developers/model-capabilities/video/generation)). Generating the still yourself and using i2v gives the same pipeline with control over frame 1.
- Aspect ratios: 16:9, 4:3, 3:2, 1:1, 2:3, 3:4, 9:16. On xAI i2v, overriding the aspect ratio **stretches** the image ([xAI generation](https://docs.x.ai/developers/model-capabilities/video/generation)). Match the still's aspect ratio instead.

## 2. Prompt structure and length

- **Order the prompt by the timeline.** The model renders "from the first frame forward", so "what happens first → write it first". Actions in the last sentence often arrive late or don't appear at all ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)).
- Five elements: **subject, motion, camera (shot type + ONE move), `Sound:` block, duration/aspect ratio** ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)). Replicate: "The model handles focused prompts better than sprawling ones" ([Replicate](https://replicate.com/blog/grok-imagine)).
- **Length: about 30–60 words, or 3 sentences with one micro-action** ([search summary of creator guides, e.g. jxp](https://www.jxp.com/grok-imagine/blog/grok-imagine-video-1-5-prompt-guide) **(?)**, [GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)). The hard limit is 4096 characters ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide) **(?)**, not found in the xAI docs).
- **Use intensity modifiers.** "crashes down with tremendous force" works better than "the wave crests" ([Replicate](https://replicate.com/blog/grok-imagine)).
- **Phrase things positively.** Negations like "no blur" are often ignored ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide), [creator]).

## 3. Image-to-video vs reference-to-video

- **i2v:** the image is frame 1. "The image carries composition, lighting, and style. The prompt only describes what changes." Don't re-describe the frame ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)). Replicate recommends this still-first workflow ([Replicate](https://replicate.com/blog/grok-imagine)). It is the best choice for exact composition and the only fal route to 1080p.
- **r2v:** "Images incorporate specific people, objects, clothing, or other visual elements **without locking the first frame**". xAI names try-on, product placement and "character-consistent storytelling" as use cases ([xAI r2v](https://docs.x.ai/developers/model-capabilities/video/reference-to-video)). Composition is regenerated, so the prompt must describe the scene, the action and the camera. On fal, r2v cannot be combined with a first-frame image (see §1).
- Rule of thumb: when the board is approved, use i2v. When the shot needs the cast face in a new composition or several assets (person + prop + set), use r2v and accept the 720p cap.

## 4. Reference tagging and role assignment (r2v)

- Tags are positional. fal's docs say "Tag references as <IMAGE_0>, <IMAGE_1>, etc.", and its example is "The person from `<IMAGE_0>` walks through a rainy neon-lit street." ([fal r2v llms.txt](https://fal.ai/models/xai/grok-imagine-video/v1.5/reference-to-video/llms.txt)).
- **Indexing conflict (?):** xAI's prose also says `<IMAGE_0>…`, but every official xAI example passes 3 images and references only `<IMAGE_1>`, `<IMAGE_2>`, `<IMAGE_3>` ([xAI r2v](https://docs.x.ai/developers/model-capabilities/video/reference-to-video)). Either the examples are 1-based or the 0th image is left untagged. **Test first:** send 2 clearly different refs with `<IMAGE_0>` = person and `<IMAGE_1>` = prop, and check which one is used for which role.
- Use xAI's phrasing pattern to give each ref one role: "the person from <IMAGE_1>", "the product from <IMAGE_2>", "on the set from <IMAGE_3>", "they wear the shirt from <IMAGE_2>" ([xAI r2v](https://docs.x.ai/developers/model-capabilities/video/reference-to-video)).
- Add an explicit invariant line: "Keep her face, hair, and cloak consistent with the reference." ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)).

## 5. Character and face consistency

- xAI markets multi-reference as a way to lock "faces, products, locations" across scenes ([xAI news, 2026-07-31](https://x.ai/news/grok-imagine-video-1-5-references)). The xAI example adds "highly detailed faces. skin pores." ([xAI r2v](https://docs.x.ai/developers/model-capabilities/video/reference-to-video)).
- [creator] Use clean, front-lit, sharp references. Dark, blurry or angled refs increase drift. Repeat a short, identical "character bible" description in every prompt, even with a ref attached ([thebizaihub](https://thebizaihub.com/consistent-ai-characters-grok-free/)).
- [creator] For long sequences, chain clips by using the last frame of clip N as the i2v input for clip N+1, or by using extend-video. Expect **visible drift after 4–6 chained clips**, then reset from the original reference ([thebizaihub](https://thebizaihub.com/consistent-ai-characters-grok-free/)) **(?)**, based on anecdotal testing.
- Identity, hands and in-frame text are known to be unstable. Put one action per clip, because many actions cause "physics glitches, identity breaks" ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)).

## 6. Camera vocabulary

The model **defaults to a static camera** if none is specified ([Replicate](https://replicate.com/blog/grok-imagine)). Use one move per clip:
`locked, static` · `slow push-in` · `aerial push-in toward [X]` · `camera drifts gently to the left` · `tracking shot alongside [X]` · `handheld tracking shot` · `slow pull out` / `slow pan out` ([Replicate](https://replicate.com/blog/grok-imagine), [GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)). xAI's own examples use "slow zoom in", "Slow cinematic push-in", and "The camera dollies from the sunlit doorway to the window" ([xAI news](https://x.ai/news/grok-imagine-video-1-5-references), [xAI r2v](https://docs.x.ai/developers/model-capabilities/video/reference-to-video)). Avoid "cinematic" or "epic" on their own, since they say nothing about the camera ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)).

## 7. Video or motion reference

**No motion-reference input exists.** r2v accepts only images (and, on native xAI, preset voices). Video input exists only for `edit-video` (≤8 s, downscaled to 480p on fal) and `extend-video` (continues from the last frame) ([xAI r2v](https://docs.x.ai/developers/model-capabilities/video/reference-to-video), [fal edit llms.txt](https://fal.ai/models/xai/grok-imagine-video/edit-video/llms.txt)). For camera paths copied from a reference video, a community guide routes the shot to Seedance instead ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)). The closest option on Grok is native xAI keyframes and last_frame, which fal does not expose.

## 8. Audio

- Audio is **on by default** and generated in the same pass as the video (dialogue with lip-sync, SFX, ambience, music). Native xAI has `generate_audio=False` for silent output ([xAI generation](https://docs.x.ai/developers/model-capabilities/video/generation), [xAI news](https://x.ai/news/grok-imagine-video-1-5)). **The fal schemas have no audio toggle**, so strip or replace the audio in post.
- Always write an explicit `Sound:` block: "A silent prompt yields a silent clip or random audio" ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)). Be specific and material ("heavy rain drumming on corrugated metal", "muffled through glass") rather than "city sounds" ([Replicate](https://replicate.com/blog/grok-imagine)).
- Dialogue: use a front-facing shot with the mouth in frame, keep lines short, put the line in quotes, and state the tone ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)).

## 9. Failure modes

| Symptom | Fix |
|---|---|
| Key action late or missing | Move it to the first sentence ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)) |
| Random or no audio | Add a `Sound:` block |
| Identity breaks, physics glitches | One action per clip, then extend ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)) |
| "Content moderated" on a benign prompt | Remove names, brands and logos, and use fictional descriptors. False positives increased after the January 2026 tightening ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)). A still that passes can still be blocked once animated because of the implied motion ([search summary citing atlascloud](https://www.atlascloud.ai/blog/tips/grok-image-is-moderated)) **(?)** |
| Stretched image in i2v | Don't override aspect_ratio (xAI). fal i2v has no aspect param |
| Wrong ref used for a role | Check tag indexing (§4) |
| Edit output soft or short | fal edit downsizes to 480p and truncates to 8 s |

## 10. Example prompts

i2v (board as frame 1):
```
Grandpa slowly turns his head toward the porthole, his eyes widening as blue Earth light spreads across his face. His hand lifts and rests on the glass. Slow push-in. Sound: low hum of the cabin ventilation, a soft creak of the seat, his quiet amazed exhale. 6 seconds.
```
r2v (tag indexing still needs checking):
```
Inside a small spaceship cabin, the old man from <IMAGE_0> floats gently upward out of his seat, laughing, wearing the spacesuit from <IMAGE_1>. Keep his face, white beard and glasses consistent with <IMAGE_0>. Tracking shot alongside him. Sound: muffled cabin hum, a velcro strap releasing, warm surprised laughter.
```
xAI's official r2v example: "slow zoom in on the white fashion runway stage. then, the model from <IMAGE_1> walks in … they wear the shirt from <IMAGE_2> and black flared jeans … subtle smile." ([xAI r2v](https://docs.x.ai/developers/model-capabilities/video/reference-to-video)).
Extend: `The camera slowly zooms out to reveal the city skyline at sunset` ([fal extend llms.txt](https://fal.ai/models/xai/grok-imagine-video/extend-video/llms.txt)).

## 11. Restrictions on realistic or real-person faces and minors

**Official xAI and fal docs contain no rule against non-sexual realistic faces, real private individuals, or minors in reference images.** The written policies target sexualization, non-consensual imagery and impersonation. Enforcement is an opaque classifier, and it has become stricter since January 2026.

- **xAI video docs:** only a generic moderation flag (`respect_moderation`) and an `invalid_argument` error for "content blocked by moderation". Nothing covers faces or minors ([xAI generation](https://docs.x.ai/developers/model-capabilities/video/generation)). xAI explicitly lists "specific people" and "character-consistent storytelling" as intended r2v uses ([xAI r2v](https://docs.x.ai/developers/model-capabilities/video/reference-to-video)).
- **xAI AUP** (x.ai returned 403/Cloudflare to our fetcher, so these are secondary quotes **(?)**): it prohibits "Depicting likenesses of persons in a pornographic manner", "The sexualization or exploitation of children", and "Undressing or nudifying real persons, or otherwise altering a real person's image or likeness to depict them in an intimate or sexual context" ([AUP URL](https://x.ai/legal/acceptable-use-policy), quoted via [search summary](https://academy.techpresso.co/prompts/grok-nsfw-prompts)). Grokipedia adds "infringing on privacy rights and publicity" ([Grokipedia](https://grokipedia.com/page/xAI_Acceptable_Use_Policy)).
- **January 2026 tightening:** after the deepfake and minors scandal, xAI blocked editing real people into revealing clothing for all users ([CNBC](https://www.cnbc.com/2026/01/14/musk-xai-blocks-grok-chatbot-from-creating-sexualized-images-of-people.html), [France 24](https://www.france24.com/en/technology/20260115-xai-restricts-grok-chatbot-after-sexualised-ai-images-spark-global-concern)). Before that, Grok had produced images of girls aged 12–16 in minimal clothing from uploaded photos ([CBS](https://www.cbsnews.com/amp/texas/news/grok-safeguard-lapses-minors-minimal-clothing-ai)). Expect the classifier to be aggressive around minors.
- **Community claims (unverified (?)):** "Any image depicting or resembling a minor is blocked outright", including images the classifier reads as "minor-adjacent" ([sloane.world](https://www.sloane.world/guides/grok-imagine-nsfw-content-policy-2026) via search summary). Real public figures and celebrity likenesses trigger moderation ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide), [HitPaw](https://www.hitpaw.com/ai-model-tips/grok-imagine-video-moderation.html)). One community guide still recommends Grok over Seedance **for real human faces** ([GitHub guide](https://github.com/thoxakihiko/grok-imagine-prompt-1.5-guide)), which suggests that non-celebrity realistic faces usually pass.
- **fal AUP:** it prohibits NCII, "Identity theft, impersonation, or deepfakes, including using another person's name, image, voice, or other likeness **without their consent** to impersonate them in any commercial, profane, defamatory, illegal, or otherwise harmful manner", and "Sexualization, exploitation, or harm to children or minors" ([fal AUP](https://fal.ai/legal/acceptable-use-policy)). Using a consenting family member in a benign story fits within that wording. fal adds no face filter of its own beyond xAI's.
- **Practical guidance for this project:** use an AI-generated grandpa, or a real one with consent, in non-sexual scenes. **For child characters, use stylized or AI-generated kids rather than real children's photos**, keep wardrobe fully clothed, and budget for blocked-but-billed attempts. Run one cheap 480p, 1–2 s probe per sensitive reference before batching.
