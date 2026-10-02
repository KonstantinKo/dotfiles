# Seedance 2.5 "likenesses of real people" filter: research and tests (updated 2026-09-28)

Legend: **[verified]** read in primary/official doc; **[reported]** third-party blog/test; **[uncertain]** weak or single source.

## 1. How the filter works

- **fal's rejection appears to come from upstream moderation.** In our fal tests it surfaced as `content_policy_violation` / `partner_validation_failed` ("partner" = upstream provider). [reported] https://masonry.so/blog/introducing-minimax-h3-max
  - fal's AUP says providers "may apply their own safeguards"; fal has no documented face filter of its own. [verified] https://fal.ai/legal/acceptable-use-policy
- **The official BytePlus rule:** "Seedance 2.5 and Seedance 2.0 series models do not support directly uploading reference images/videos that contain real human faces." [verified] https://docs.byteplus.com/en/docs/ModelArk/2608626
  - Other providers may apply the model policy differently; the BytePlus rule and fal errors do not establish how Higgsfield handles inputs.
- **fal test results:** fal Seedance 2.5 rejected photoreal human faces, including AI-generated images; this does not establish identical filtering on other providers.
  - Tests on fal Seedance 2.5 on 2026-09-14 rejected an AI-generated photoreal face sheet, a frame from Seedance's own output and Seedance's own mp4.
  - The same tests accepted a headless wardrobe crop and a stylised 3D/cartoon face. [reported] https://github.com/recoupable/skills/pull/145
  - A separate test found that a purely *generated* portrait was also refused on fal Seedance 2.5. [reported] https://masonry.so/blog/introducing-minimax-h3-max
  - In our fal tests, a wide shot with tiny faces passed while close face sheets failed. This suggests a detection threshold, but its behavior and threshold are undocumented. [uncertain]
- **Minors:** no source documents a *separate* minor-specific gate for Seedance reference images. One secondary source says child-looking uploads get "stricter review". [uncertain] https://www.seedance.tv/blog/seedance-safety-filters-real-faces-image-prompts-2026
  - The generic real-face block is enough to explain our fal failure.
- **Documented BytePlus ModelArk exception:** ModelArk "trusts" certain face-containing outputs as inputs:
  - Seedance 2.x videos and their last frames
  - **Seedream 5.0 lite text-to-image** images
  - Conditions: generated **on the same ModelArk account within 30 days**, unedited and not re-compressed. Cross-platform and cross-account use is not trusted. [verified] https://docs.byteplus.com/en/docs/ModelArk/2608626
  - Those ModelArk conditions are provider-specific and do not explain Higgsfield's behavior.

## Higgsfield S012 test and current project workflow

- On 2026-09-28, Higgsfield Seedance 2.5 job `6d039779-7745-4eed-a686-d017ad150b6e` accepted local uploads of fal-generated photoreal Tamino and Stoyan reference sheets/composites, approved fal-generated start/end images, and a local Blender previz video. The input media were supplied as local files, not as Higgsfield job IDs. A job ID was not necessary for this observed case.
- The reason for acceptance is unknown. The result does not establish that raw photographs or other photoreal face references will pass, or identify whether provider moderation, file handling, or another factor explains it.
- For this Backlot project, use Higgsfield Seedance 2.5 for upcoming shots and submit the reference sheets, approved start/end images, and Blender previz as local files. Treat S012 as evidence for this specific input route, and record outcomes for materially different inputs. Follow the paid-call approval steps in the Higgsfield generation skill.

## 2. Consent path: "authorized real-person assets" (BytePlus ModelArk)

- **Official path:** "Add real-human assets to asset library", for Seedance 2.0 and 2.5. [verified] https://docs.byteplus.com/en/docs/ModelArk/2315856 Flow:
  1. The asset user creates an asset group in the ModelArk Playground and generates a QR invite. The account must have completed *real-name or enterprise authentication*.
  2. The **depicted person** scans the QR code and logs into **their own BytePlus account**.
  3. They agree to the facial-data rules and complete a **liveness check**.
  4. They upload their own photos or videos. A face-consistency check follows.
  5. The asset user accepts, then uses `asset://<asset_id>` as a `reference_image` in the Ark API.
- **Cost:** the "Basic Creation Rights (Free tier)" allows real-person verification and upload via the console, with 50 assets and 50 groups. [verified] https://docs.byteplus.com/en/docs/modelark/2377608
  - The paid tiers ($1.4k+/month) are for API upload and scale.
  - That page says Advanced Creation Rights are for *enterprise* users with organisation verification. It is unclear whether the free console tier needs enterprise verification. [uncertain]
- **Blocker for the 5-year-old:** the verification requires the person themself to log into a BytePlus account and do liveness.
  - BytePlus services are "not aimed at or suitable for use by anyone below the age of 18" and under-18s "must not use" them. [reported via search snippet] https://docs.byteplus.com/en/docs/legal/docs-privacy-policy-20221020
  - So the path **looks feasible for the grandfather and not for the child**. [uncertain: no doc addresses parental consent for minors]
- **Private *virtual* portrait library:** this is for your own AI characters. Assets "must not resemble the portrait or likeness of any natural person". [verified] https://docs.byteplus.com/en/docs/ModelArk/2333565
  - Our sheets are derived from real family members, so registering them here would breach those terms.
- **Preset digital characters** (the ByteDance stock-avatar library): compliant, but they are not our people. [verified] https://docs.byteplus.com/en/docs/ModelArk/2608626
- **Self-only digital avatar** (Jimeng/Doubao apps, China, liveness of your own face). [reported] https://ruoqijin.com/blog/seedance-access-and-face-policy
  - ComfyUI partner node "Seedance 2.0 Real Human" wraps the same ByteDance liveness verification. [verified] https://docs.comfy.org/tutorials/partner-nodes/bytedance/seedance-2-0-real-human, https://blog.comfy.org/p/unlock-seedance20-real-human-video-generation

## 3. Workarounds: legitimate vs not

- **Legitimate:**
  - Authorized real-person assets on ModelArk (grandfather, adult consent + liveness). [verified, see above]
  - **Stylised cast** (3D-animation/Pixar-like or illustrated versions of boy and grandpa). The stylised face passes and holds identity on fal Seedance 2.5. [reported] https://github.com/recoupable/skills/pull/145
  - Fits a playful "space trip" family film. Caveat: one source calls stylising a *real* face specifically to beat the filter a ToS risk. [reported] https://ruoqijin.com/blog/seedance-access-and-face-policy
  - Framing matters: stylisation as an artistic choice with consent is defensible. Stylisation tuned to "break the biometric signature" is evasion.
  - **Hybrid routing:** use a different model for photoreal close shots of the family, and Seedance only for wide shots, faceless shots and environments. [reported] https://github.com/recoupable/skills/pull/145
- **Grey area:** regenerating the family's likeness through Seedream 5.0 lite on ModelArk to get "trusted" outputs.
  - Trust only covers *text-to-image* outputs (not i2i from family photos).
  - Using it to launder a real person's likeness contradicts the stated real-face rule. **Not recommended.** https://docs.byteplus.com/en/docs/ModelArk/2608626
- **Not legitimate (skip):** grid overlays, angle tricks, noise or partial masking, and "bypass" YouTube methods. These are explicit filter evasion and "violate ByteDance's ToS". https://ruoqijin.com/blog/seedance-access-and-face-policy
- **Other front-ends:**
  - Higgsfield "Face Eligibility" reportedly allows faces after verification. [uncertain: marketing and YouTube only] https://www.youtube.com/watch?v=cNkw-LOTJvw
  - CapCut/Dreamina explicitly restrict real faces. https://techcrunch.com/2026/03/26/bytedances-new-ai-video-generation-model-dreamina-seedance-2-0-comes-to-capcut/
  - Freepik and Krea: no documented consent path found. [uncertain]

## 4. Other models on fal

- **MiniMax H3 Max reference-to-video:** accepted the same generated portrait that Seedance 2.5 refused. [reported] https://masonry.so/blog/introducing-minimax-h3-max
  - No documented face or minor gate. Consent remains the user's responsibility.
- **Veo 3.1:** Google blocks **minors in image-to-video** unless the project is allowlisted. The documented error is support code 17301594, "child category". [reported, forum 2026-07-13] https://discuss.ai.google.dev/t/request-allowlist-access-for-veo-3-1-person-generation-image-to-video-minors-project-little-learning-lab/174587
  - `personGeneration` defaults to adults only. https://cloud.google.com/vertex-ai/generative-ai/docs/video/use-reference-images-to-guide-video-generation
  - **Likely to fail on the 5-year-old via fal.** [uncertain for the fal passthrough]
- **Kling:** the policy forbids private individuals' likeness "without explicit legal authorization" (a consent rule, not a technical block). There are strict rules on harmful depictions of minors, and non-harmful ones are not banned.
  - [verified policy] https://kling.ai/docs/community-policy
  - [reported] https://www.glbgpt.com/resources/ai-video-human-face-seedance-veo-kling/
  - No documented automatic real-face block on reference images. [uncertain]
- **Grok Imagine Video 1.5 (reference-to-video, 1-7 refs):** no documented real-face gate on fal. https://fal.ai/models/xai/grok-imagine-video/v1.5/reference-to-video
  - xAI tightened moderation after the 2026 deepfake scandal. One source claims anything resembling a minor is blocked outright. [uncertain, NSFW-focused source] https://www.sloane.world/guides/grok-imagine-nsfw-content-policy-2026, https://en.wikipedia.org/wiki/Grok_sexual_deepfake_scandal
- **FLUX 3 video:** no public real-face or minor reference policy found. [uncertain] https://bfl.ai/blog/flux-3-video
- **Suggested fal fallback order if a photoreal family shot needs an alternate model:**
  1. MiniMax H3 Max
  2. Kling
  3. FLUX 3
  4. Grok 1.5
  5. Veo (expect the child to be blocked)
