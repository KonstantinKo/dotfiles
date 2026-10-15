---
name: models
description: Work with the Backlot model catalog: read Studio/Models notes, choose a model by kind and tier, add a model note, add a provider adapter. Use for "which models do we have", "add a model", "add fal endpoint X", "add a provider", "why was this model picked", "is comfyui reachable".
---

# Models

## Purpose
Keep the catalog the CLI reads accurate, and choose models with the same rules every skill uses.

## Inputs
- `Studio/Models/<id>.md` (frontmatter is machine-read), `Studio/Models/Models.base`
- `Studio/Providers/<name>.md`
- `backlot models [--kind K] [--provider P]`, `backlot doctor`
- `~/dotfiles/agents/video/backlot/README.md` for adapter and workflow template details
- `generate/references/model-routing.md`

## Reading the catalog
`backlot models --kind video` lists active and untested models with tier, provider and cost (untested are marked; `--all` adds disabled ones). Open the note for strengths, limits and prompt tips before choosing. `status: untested` means nobody has run it here; the first run is a test at lite settings. A paid test needs its own exact quote and authorization under [Decision and spend](../studio/references/decision-and-spend.md); free or local tests need no spend authorization.

Treat readiness as route-specific. A stub or unconfigured provider is unavailable even if its name appears in the catalog. A configured route is not locally verified until a real request succeeds. Before quoting, check the exact provider, model/version and operation against current primary provider guidance and a dated local observation where available. Confirm that the prompt and requested controls reach the effective request with its attachments; check minimum duration, retained controls, price-changing options and any applicable promotion. A paid route with unknown price is ineligible for a quote; zero is reserved for a route whose cost is verified to be zero.

Record local observations separately from provider claims. Include the date, exact provider/model/version/operation, task and inputs, effective defaults plus overrides, result or failure, confidence and limits of the observation. One successful call supports only the route and conditions actually tried; it does not establish broad model suitability. Keep a failed observation too. Do not infer a price, promotion or route capability from a neighboring model or a different operation.

## Choosing
Filter by kind, inputs, duration, resolution; tier by lock state; rank by strengths. Full rules in `generate/references/model-routing.md`. State the chosen model and the reason in one line when presenting an estimate. Models whose note lists `image` more than once in `inputs` (multi-reference) take a repeated `--image`; check `optional_inputs` before promising image-to-video. For a set of takes, write a batch plan and quote `backlot batch --dry-run`; compare options with `backlot sheet`. Use `backlot recover <take>` only when an accepted provider job/result is available to fetch. A new submission is a new take; for a variation, record its parent and quote the call again. Paid calls follow [Decision and spend](../studio/references/decision-and-spend.md).

## Adding a model note
1. Copy `_templates/Model.md` to `Studio/Models/<id>.md`. The `id` is the file name and what `--model` takes.
2. Frontmatter, every key present:
   `id, provider (fal|comfyui-local|comfyui-cloud|higgsfield|local), kind (image|video|tts|music|sfx|upscale|stt|lipsync), endpoint, tier (lite|pro|ultra), cost_unit (per_image|per_second|per_1k_chars|per_run), cost_eur, status (untested), inputs [], optional_inputs [], max_duration_s, min_duration_s, resolutions [], defaults {}, arg_map {}, param_types {}`. The template body documents each key.
   For fal, `endpoint` is the fal model path and `inputs` name the request fields the adapter maps (`prompt`, `text`, `voice`, `image`, `audio`, `video`). Compare the endpoint's argument names with the defaults (`prompt`, `text`, `voice`, `image_url`, `audio_url`, `video_url`) and set `arg_map` for any that differ (`image: image_urls`, `image: start_image_url`, `voice: voice_setting.voice_id`). Set `param_types: {duration: str}` when the endpoint wants string enums such as `"5"` or `"8s"`, and `min_duration_s` when the page states a minimum billed length. For comfyui-local, `endpoint` is the workflow template name under `backlot/workflows/<id>.json` and `defaults` list its placeholders.
3. Body: strengths, limits, prompt tips, dated local observations, and sourced provider guidance. Add a paid model note only after its current price source and date are recorded. Keep a local result distinct from a provider-published claim.
4. `backlot doctor` (parses all model notes). Fix any parse error before use.
5. Test once at lite settings with a real request; paid tests follow [Decision and spend](../studio/references/decision-and-spend.md), while free or local tests need no spend authorization. Set `status: active` only after a successful run and record the observed cost in the body.

## Adding a provider adapter
Pointer: `~/dotfiles/agents/video/backlot/README.md`. An adapter is one file `backlot/providers/<name>.py` implementing `estimate(model, req)` and `run(model, req) -> files`, plus `Studio/Providers/<name>.md` (reach, auth, quirks, status) and at least one model note. Keys come from env or macOS Keychain; never write them to disk or into notes. `backlot doctor` must pass before the provider is used by a skill.

## Outputs
- `Studio/Models/<id>.md`, `Studio/Providers/<name>.md`
- Adapter file when a provider is added (CLI scope; coordinate rather than improvise)

For reference provenance and the ordered reference set attached to a shot, see [Reference records](../studio/references/reference-records.md). Keep this evidence in structured fields, outside creative prompt prose.

## Gate
`backlot doctor` clean and one successful test run recorded in the note.

## Example phrases
- "which video models can do image-to-video over 8 seconds"
- "add the new fal kling endpoint as a pro model"
- "add higgsfield as a provider"
