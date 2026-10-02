# Additional model evidence

Researched 2026-10-01. These notes supplement the image, video, and specialist research. **P** means a provider or serving platform; **I** means independent reporting or user evidence. Confidence refers to the recommendation, not whether a catalog entry exists. Source dates marked approximate come from the publisher/search metadata; access date is always 2026-10-01.

## Qwen Image 3

**Observed availability:** fal `alibaba/qwen-image-3/text-to-image` and `/edit`; absent from the current Higgsfield CLI list. Do not equate this hosted release with older open-weight Qwen Image/Edit checkpoints or assume it is the Pro variant.

- **P, live endpoint:** [fal Qwen Image 3](https://fal.ai/models/alibaba/qwen-image-3/text-to-image). Advertises text rendering and instruction following, prompt rewriting, and output up to 2048 square. Billing text establishes a low-to-mid image price that increases at 2K. The pricing API's generic `units` obscures the formula; use endpoint billing text.
- **I, publication date not established (displayed as two months ago), anecdotal comment in a promotional thread:** [Qwen Image 2 & 3 versus 2512](https://www.reddit.com/r/StableDiffusion/comments/1va0vfu/qwen_image_2_3_are_closedweights_so_we_optimized/). A commenter who tested Qwen 3 praises complex layout text but prefers an older fine-tune for other qualities. The thread promotes work on an older model; this is a narrow counterexample, not a benchmark.
- **I, approximately September 2026, adjacent-version report:** [Qwen Image 2.1 initial tests](https://www.reddit.com/r/StableDiffusion/comments/1wlhh8v/after_initial_tests_qwen_image_21_quality_is/). A commenter explicitly compares artifacts with Qwen 3.0 API photorealism. Treat this as a reported risk, not a universal defect or a full Qwen 3 test.

**Decision:** compare for dense text/layout at lower cost; photoreal portraits need a sample rather than assuming superiority. Independent confidence is low.

## Krea 2 Large and Turbo

**Observed availability:** fal `krea/v2/large/text-to-image`, `fal-ai/krea-2/turbo`, and Turbo style/LoRA routes; absent from the Higgsfield CLI list. The Krea website's moodboard interface is not automatically an API feature.

- **P, 2026-05-12:** [Krea 2](https://www.krea.ai/krea-2). Positions the model for varied aesthetics and style-driven exploration. These are design goals, not proof of an advantage on exact layout or identity.
- **P, 2026-06-23:** [Krea 2 technical report](https://www.krea.ai/blog/krea-2-technical-report). Describes exploratory prompt expansion and style conditioning. That emphasis suggests a weaker match for rigidly specified output, rather than proving inability to follow instructions.
- **P, live endpoints:** [Large](https://fal.ai/models/krea/v2/large/text-to-image), [Turbo](https://fal.ai/models/fal-ai/krea-2/turbo). Large costs more than Turbo at ordinary sizes; style-reference billing differs. Turbo uses megapixel billing. Exact edits need a different model or a specifically available editing workflow.
- **I, approximately June/July 2026, one author's gallery:** [Krea 2 Turbo: 100+ styles](https://www.reddit.com/r/StableDiffusion/comments/1uf1qcc/krea_2_turbo_100_styles_on_the_same_scene/). A user posts a children's-book experiment across many style prompts. Supports aesthetic exploration, but prompts were rewritten per style; it does not isolate model quality from prompting or measure identity continuity.
- **I, approximately September 2026, operation mismatch:** [Krea 2 Edit discussion](https://www.reddit.com/r/StableDiffusion/comments/1wck3xj/any_news_on_a_krea_2_edit_model/). Users seek a dedicated edit model. Do not infer that a website editor is native Krea 2 editing or expose it through a text-to-image endpoint.

**Decision:** Large for style exploration with references; Turbo for cheap visual auditions and compatible LoRAs. Avoid choosing these routes for precise surgical edits. Confidence medium for style exploration, low for general superiority.

## Meta Muse Image

**Observed availability:** fal `meta/muse-image/text-to-image` and `/edit`; absent from Higgsfield CLI list.

- **P, July 2026:** [Meta's Muse introduction](https://ai.meta.com/blog/introducing-muse-image-muse-video-msl/). Claims detailed generation, instruction-guided editing, and reference composition. Its launch-time ranking is dated and should not be repeated as current leadership.
- **P, live endpoint:** [fal Muse Image](https://fal.ai/models/meta/muse-image/text-to-image). The read-only pricing query returned a low per-image price. This supports a budget audition, not an assumption that accuracy matches premium models.
- **I, 2026-07-09, hands-on consumer app test:** [Digital Camera World on Muse](https://www.digitalcameraworld.com/tech/social-media/instagrams-controversial-ai-wont-just-copy-your-face-meta-muse-image-imitates-photography-styles-too). Tested Instagram-linked identity/style behavior. App integrations differ from fal; do not assume API access to Instagram profiles or transfer all app behavior to the API. This source provides little evidence about exact API typography or edit quality.

**Decision:** low-cost general generation/editing audition. Exact text, identity, and surgical edit advantages remain insufficiently established for this route. Confidence low; no dedicated independent API comparison found.

## LTX-2.5 Fast and Pro

**Observed availability:** fal `lightricks/ltx-2.5/{image-to-video,text-to-video,audio-to-video}/{fast,pro}`; absent from Higgsfield CLI list.

- **P, August 2026/current page:** [Lightricks LTX-2.5](https://ltx.io/model/ltx-2-5). Advertises speed, native multi-shot, and better continuity. Its own speed chart mixes resolutions, hardware, queue time, and clip lengths; its artifact score is an internal automated test. These do not establish general superiority to other models.
- **P, live endpoint billing:** [Fast](https://fal.ai/models/lightricks/ltx-2.5/image-to-video/fast), [Pro](https://fal.ai/models/lightricks/ltx-2.5/image-to-video/pro). Fast is cheaper than Pro at matching resolution; native audio is included in Fast pricing. Fast's page exposes higher-resolution tiers. Hosted costs remain payable even though weights are downloadable.
- **I, 2026-08-12, small local test:** [Quick LTX 2.5 test](https://www.reddit.com/r/comfyui/comments/1vmld52/a_quick_test_to_ltx_25/). User reports camera motion and small-detail difficulties despite improved quality. Local LoRA settings differ from hosted Fast/Pro. Treat as a failure risk, not a measured fal endpoint failure rate.
- **I, publication date not established, corrective workflow investigation; publisher discloses affiliate links:** [Aillex on the hidden prompt enhancer](https://askaillex.com/guides/ltx-2-5-comfyui-hidden-prompt-enhancer/). A tester retracts part of an earlier negative assessment after identifying prompt rewriting in the template. This supports recording the actual rewritten prompt and workflow before attributing every defect to the base model.

**Decision:** Fast for economical audio-video drafts; Pro when its quality tier justifies added cost. Audition camera motion and continuity before complex final shots. Independent confidence medium for risks; direct Fast-versus-Pro hosted comparisons remain sparse.

## Vidu Q3 Pro / Turbo / Mix

**Observed availability:** fal `fal-ai/vidu/q3/image-to-video`, `/text-to-video`, corresponding `/turbo`, and `/reference-to-video/mix`; absent from Higgsfield CLI list.

- **P, current undated:** [Vidu Q3](https://s.vidu.com/vidu-q3). Advertises native audio, clips up to 16 seconds, comic/manga narratives, and dialogue in English, Japanese, and Chinese. Frame-accurate direction is an advertised claim; check controls on the actual fal route.
- **P, current:** [Vidu model map](https://platform.vidu.com/models). Distinguishes Pro, Turbo, Mix, and specialized native-platform variants. Only recommend those exposed on fal; a Vidu-native feature is not automatically available there.
- **P, endpoint contracts:** [fal Q3 text-to-video](https://fal.ai/models/fal-ai/vidu/q3/text-to-video), [Mix API](https://fal.ai/models/fal-ai/vidu/q3/reference-to-video/mix/api). Q3 Pro price rises at higher resolutions. Pricing-tool `videos` must not be interpreted as a flat price per finished clip; the endpoint charges by seconds. Turbo is cheaper than Pro at matching settings.
- **Commercial secondary, approximately May/June 2026:** [Pollo AI Q3 review](https://pollo.ai/hub/vidu-q3-review). Shows use cases but sells access to the same model; reports character drift and difficulty with complex prompt logic. It is useful as a commercial test report, not independent corroboration.
- **I, approximately April/May 2026, small demonstration:** [Reddit action test](https://www.reddit.com/r/AI_Forge/comments/1sxfcvw/action_test_with_different_tools/). Posted Q3 action results provide a task sample, not repeated controlled comparisons. Independent evidence for Q3 Mix specifically remains sparse.

**Decision:** a candidate for anime/comic narrative, native dialogue, and lower-cost previews; Mix when references are required. Strict continuity or complex action needs a representative test. Confidence low-to-medium.

## Scope and excluded catalog claims

The connected fal discovery tool returned at most 100 endpoints per query; targeted family searches were used for LTX and Vidu beyond the initial snapshot. This is a curated decision guide, not an exhaustive list of fal's hosted models.

Public pages advertise [Imagen 4](https://deepmind.google/models/imagen/) and [Reve 2.1 on fal](https://fal.ai/reve-2.1), but targeted discovery returned no matching image entries for `imagen4` or `reve` in this session. Their absence from search does not prove inaccessibility. They are excluded from active recommendations until a current route is confirmed. Neither appears in the current Higgsfield CLI list. Sora, Runway, and other ecosystems are likewise outside the confirmed selection set here.

**Segmentation utilities, P/local:** targeted fal discovery confirmed [SAM 3 video](https://fal.ai/models/fal-ai/sam-3/video) and its RLE route, alongside [BiRefNet v2](https://fal.ai/models/fal-ai/birefnet/v2). Read-only pricing metadata bills SAM video by groups of frames and BiRefNet by compute seconds. These are segmentation/cutout tasks, not general image generation; mask output and a finished transparent video are distinct deliverables. No comparative edge-quality or temporal-matte benchmark was performed here.

## Existing local observations that affect provider choice

[Seedance likeness-filter research](../../prompt-seedance-2-5/references/likeness-filter.md), updated 2026-09-28, records fal failures with photoreal face references and one successful Higgsfield Seedance 2.5 submission of local, fal-generated photoreal reference sheets plus Blender previz. This is a recorded local observation, not a new test conducted for this research or proof of universal face acceptance on Higgsfield. The [BytePlus input policy](https://docs.byteplus.com/en/docs/ModelArk/2608626) is an official rule for that provider; provider-specific exceptions must not be generalized.

## Reading overall leaderboards

[Artificial Analysis image generation](https://artificialanalysis.ai/image/leaderboard/text-to-image), [image editing](https://artificialanalysis.ai/image/leaderboard/editing), and [video generation](https://artificialanalysis.ai/video/leaderboard/text-to-video), accessed 2026-10-01, use blind pairwise human preference. GPT Image 2.5 variants lead the retrieved image boards; Wan 3.0, Seedance 2.5, and H3 are competitive on the video board. These support comparing current candidates, rather than inheriting old brand rankings. Boards differ by operation, settings, samples, and confidence intervals; their creator-API prices do not establish Higgsfield subscription costs or fal endpoint charges.

## Higgsfield price observations on this signed-in account

Read-only CLI cost estimates on 2026-10-01; no jobs created or reference files uploaded. These are local observations of credit estimates, rather than dollar prices or claims about output quality. Current [official CLI instructions](https://github.com/higgsfield-ai/skills/blob/main/higgsfield-generate/SKILL.md) describe model discovery and cost estimation. Re-run an exact quote when selecting settings or using references.

**Image prompt:** `A plain ceramic cup on a table`; no media, one output, default aspect and resolution, except the explicit quality variants below. Current schemas set GPT Image 2.5, Nano Banana 2, and Recraft defaults to 1K. Do not assume matching quality from matching resolution labels.

| Route/settings | Relative estimate on this account |
|---|---|
| Soul 2.0 default 2K; Z Image defaults | Lowest in the sampled group |
| GPT Image 2.5 default Flare/low/1K | Low; far cheaper than its own max tier |
| Recraft V4.1 standard/1K | Mid |
| Nano Banana 2 default/1K; GPT Image 2.5 Flare/high/1K | Same estimate; higher than Recraft in this sample |
| Nano Banana Pro default 2K; separate 1K re-quote gave the same estimate | Higher than Nano Banana 2 at the quoted settings |
| Seedream 5.0 Pro default 2K | Higher than Nano Banana Pro |
| GPT Image 2.5 Sunburst/max/1K | Highest; about twenty times the default Flare/low quote, conflating both variant and quality changes |

**Video prompt:** `A ceramic cup rests on a table while the camera slowly moves closer`; no media; requested eight seconds. Values compare the named settings, not equivalent quality. Reference video billing, generated audio, and hidden defaults can change the order.

| Route/settings | Relative estimate on this account |
|---|---|
| Veo 3.1 Lite, 8s, default audio off | Lowest in the sampled group |
| Wan 3.0, 8s, 720p, default audio on | Slightly above Lite |
| Kling 3.0, 8s, std; MiniMax H3, 8s, 2K (only exposed resolution) | Equal quotes; modestly above Wan in this sample |
| Gemini Omni Flash 1.1, 8s, text-to-video, 720p | Mid; above Kling/H3 |
| Veo 3.1, 8s, basic | Higher than Omni |
| Seedance 2.5, 8s, t2v, 720p, default audio on | High; over three times the quoted Kling std/H3 settings |
| Veo 3.1, 8s, ultra | Highest; above Seedance 2.5 |

Because several output settings differ, use these to decide which routes deserve an exact quote, rather than asserting that the lowest quote buys the same fidelity or sound. The decision table mainly uses fal endpoint billing for cross-model tiers and names Higgsfield differences explicitly.
