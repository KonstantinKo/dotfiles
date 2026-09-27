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
`backlot models --kind video` lists active and untested models with tier, provider and cost (untested are marked; `--all` adds disabled ones). Open the note for strengths, limits and prompt tips before choosing. `status: untested` means nobody has run it here; the first run is a test at lite settings with the user's yes.

## Choosing
Filter by kind, inputs, duration, resolution; tier by lock state; rank by strengths. Full rules in `generate/references/model-routing.md`. State the chosen model and the reason in one line when presenting an estimate. Models whose note lists `image` more than once in `inputs` (multi-reference) take a repeated `--image`; check `optional_inputs` before promising image-to-video. For a set of takes, write a batch plan and quote `backlot batch --dry-run`; compare options with `backlot sheet`; a failed take is retried with `backlot recover <take>`, never re-generated under a new ID.

## Adding a model note
1. Copy `_templates/Model.md` to `Studio/Models/<id>.md`. The `id` is the file name and what `--model` takes.
2. Frontmatter, every key present:
   `id, provider (fal|comfyui-local|comfyui-cloud|higgsfield|local), kind (image|video|tts|music|sfx|upscale|stt|lipsync), endpoint, tier (lite|pro|ultra), cost_unit (per_image|per_second|per_1k_chars|per_run), cost_eur, status (untested), inputs [], optional_inputs [], max_duration_s, min_duration_s, resolutions [], defaults {}, arg_map {}, param_types {}`. The template body documents each key.
   For fal, `endpoint` is the fal model path and `inputs` name the request fields the adapter maps (`prompt`, `text`, `voice`, `image`, `audio`, `video`). Compare the endpoint's argument names with the defaults (`prompt`, `text`, `voice`, `image_url`, `audio_url`, `video_url`) and set `arg_map` for any that differ (`image: image_urls`, `image: start_image_url`, `voice: voice_setting.voice_id`). Set `param_types: {duration: str}` when the endpoint wants string enums such as `"5"` or `"8s"`, and `min_duration_s` when the page states a minimum billed length. For comfyui-local, `endpoint` is the workflow template name under `backlot/workflows/<id>.json` and `defaults` list its placeholders.
3. Body: strengths, limits, prompt tips, a link to the provider's model page, price source and date.
4. `backlot doctor` (parses all model notes). Fix any parse error before use.
5. Test once at lite settings with a real request; set `status: active` and record the observed cost in the body.

## Adding a provider adapter
Pointer: `~/dotfiles/agents/video/backlot/README.md`. An adapter is one file `backlot/providers/<name>.py` implementing `estimate(model, req)` and `run(model, req) -> files`, plus `Studio/Providers/<name>.md` (reach, auth, quirks, status) and at least one model note. Keys come from env or macOS Keychain; never write them to disk or into notes. `backlot doctor` must pass before the provider is used by a skill.

## Outputs
- `Studio/Models/<id>.md`, `Studio/Providers/<name>.md`
- Adapter file when a provider is added (CLI scope; coordinate rather than improvise)

## Gate
`backlot doctor` clean and one successful test run recorded in the note.

## Example phrases
- "which video models can do image-to-video over 8 seconds"
- "add the new fal kling endpoint as a pro model"
- "add higgsfield as a provider"
