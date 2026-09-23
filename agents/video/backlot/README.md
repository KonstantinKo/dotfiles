# backlot

CLI for the Backlot studio (see `../ARCHITECTURE.md`). Python 3.12, run through `uv`;
the launcher is `../bin/backlot` (linked to `~/.local/bin/backlot`).

```
backlot doctor                      # tools, key presence, vault, ComfyUI, model notes
backlot init <slug> [--format 16:9 --fps 24 --res 1920x1080 --budget 25]
backlot models [--kind image] [--provider fal] [--all]
backlot gen image --model fal-flux-schnell --prompt "..." [--shot S010] [--n 2]
            [--image <path|take>]... [--audio <path|take>]... [--video <path|take>]... [--end-image <path|take>]
            [--param k=v] [--parent img-003] [--depends-on Cast/Mia] [--dry-run] [--yes] [--force]
backlot tts --model kokoro --voice af_heart --text "..." | --file vo.txt [--shot S010] [--yes]
backlot batch plan.yaml [--dry-run] [--yes] [--force]      # several gen/tts requests, one table, one --yes
backlot recover img-003                                      # finish a failed/pending take by its request id
backlot takes [--shot S010] [--kind vid] [--status approved|pending|failed] [--stale]
backlot show img-003
backlot approve img-003 --reason "..." [--lock Cast/Mia]     # first approval of an untested model makes it active
backlot reject img-003 --reason "..."
backlot stale Cast/Mia --reason "..." [--dry-run]            # transitive through Context `depends_on`
backlot captions vo-001 [--model fal-elevenlabs-scribe] [--yes]
backlot sheet --shot S010 [--kind img]                       # contact sheet -> renders/sheets/S010.jpg + shot note
backlot stage [--advance]                                    # gate check for the current stage
backlot render [edit/timeline.yaml] [-o renders/x.mp4] [--preset youtube|shorts|draft] [--dry-run] [--allow-stale]
backlot reframe vid-002 --to 9:16 --focus left
backlot status | backlot cost | backlot thumbs
```

Every command accepts `--json` and `--project <slug>`; without `--project` the project is
found by walking up from the cwd to `project.yaml`. Config comes from
`~/projects/video/studio.yaml` (override with `BACKLOT_STUDIO`).

Exit codes: `0` ok, `1` error, `2` usage, `3` needs confirmation (`ask_before_generate`
is on and `--yes` missing; the estimate is printed), `4` budget exceeded.

## What a generation does

1. Reads the model note (`<vault>/Studio/Models/<id>.md`), builds the request, estimates
   the cost (`cost_unit` x n / seconds / chars).
2. Guards the spend (same path for `gen`, `tts`, `batch`, `captions`): budget 0 or
   exceeded -> exit 4; a single call above `max_call_eur` -> exit 4 unless `--force`;
   `ask_before_generate` and estimate above `confirm_over_eur` -> exit 3 unless `--yes`.
3. Under `takes/.lock`: re-checks the budget (pending and failed takes count as spent),
   reserves the next id and writes `takes/<id>/meta.yaml` with `status: pending`.
4. Runs the provider. fal records the `request_id` into the meta before waiting and gives
   up after `providers.fal.timeout_s` (default 900 s). A failure after the request was
   submitted leaves the take `failed` with its cost; `backlot recover <id>` fetches the
   result later. A failure before submission drops the reservation.
5. Saves `takes/<id>/out.<ext>`, `prompt.txt`, `meta.yaml`, appends `takes/manifest.jsonl`.
6. Writes the vault: `_thumbs/<id>.jpg` (also waveforms), `Takes/<id>.md` with
   vault-root-relative links (`[[Projects/<slug>/Shots/S010|S010]]`), then regenerates
   `Costs.md`, `Status.md` and `spent_eur` on the project home.

Take ids are `<kind>-<seq>` (`img-014`); `--parent img-014` yields `img-014.2` and must be
the same kind as the new take. `--image/--audio/--video` repeat when the model's `arg_map`
target ends in `s` (`image_urls`); a singular target with two values is an error.
`--end-image` maps through `arg_map.end_image` (default `end_image_url`) for models that
list `end_image` in `inputs`.

Thresholds (`project.yaml`, falling back to `defaults:` in `studio.yaml`):
`confirm_over_eur` (0 = always confirm), `max_call_eur` (1.0), `escalate_pct` (80; `status`
prints an ESCALATE line at or above this share of the budget).

## Batch plans

`backlot batch plan.yaml` plans every request first, prints one cost table, needs one
`--yes`, runs sequentially, stops at the first provider error and prints the take ids made
so far. Schema: `requests:` (or a top-level list) of maps with the gen/tts fields:

```yaml
requests:
  - {kind: image, model: fal-flux-schnell, prompt: "...", shot: S010, n: 2, depends_on: [Cast/Mia]}
  - {kind: video, model: fal-kling, prompt: "...", image: img-001, end_image: img-002, params: {duration: 5}}
  - {kind: tts, model: kokoro, voice: af_heart, file: vo/S010.txt, shot: S010}   # or text: "..."
```
Fields: `kind`, `model`, `prompt`, `text`|`file`, `voice`, `image`|`audio`|`video` (string or
list), `end_image`, `shot`, `n`, `params` (map), `parent`, `depends_on` (list or comma string).

## Timeline

`edit/timeline.yaml` as in the architecture spec. `src` is a take id, a render name or
a path. Stills take `duration` and optional `motion: kenburns`; clips take `in`/`out`,
an optional `transition: {type: xfade, name: fade, duration: 0.5}` into the next clip and
`audio: keep` (+ `gain_db`) to mix the clip's own sound at its timeline position.
Audio tracks: `at`, `gain_db`, `out` (trim, seconds), `fade_out_s`, `duck_under: <track>` + `duck_db`.
Sources that are rejected or stale takes are refused unless `--allow-stale` is given.
`captions: {from: vo}` merges the `.srt` of every `track: vo` row (from `backlot captions`),
each shifted by its `at`; `captions: {src: vo-003}` uses one file (shifted by that row's `at`
when it is in the audio list). The merged `renders/<name>.srt` is written next to the render
even with `burn: false`. Titles use `style: lower-third|center`.
Titles and captions are rendered with Pillow and composited with `overlay`, so the
Homebrew ffmpeg (no drawtext/libass) works.

## Layout

```
backlot/            package: cli, config, project, models, takes, vault, gen, batch, decisions,
                    stages, sheet, render, reframe, captions, thumbs, overlays, scaffold, doctor, providers/
templates/          project dir files for `init` (project.yaml, .gitignore, timeline); vault notes come from <vault>/_templates
workflows/          ComfyUI API-format workflows with {{placeholders}}
tests/              pytest (providers are mocked; render tests use ffmpeg lavfi media)
```

Run tests: `uv run pytest`.

## Adding a provider

1. Create `backlot/providers/<name>.py` with a class deriving from `BaseProvider`
   implementing `estimate(model, req) -> float` and `run(model, req) -> GenResult`
   (list of files written into `req.workdir`). Implement `call_json` if the provider
   serves stt-style JSON results.
2. Register it in `PROVIDERS` in `backlot/providers/__init__.py`.
3. Add `Studio/Providers/<name>.md` and model notes with `provider: <name>` to the vault;
   per-provider settings live under `providers.<name>` in `studio.yaml` and arrive as
   `self.config`.

`build_arguments()` in `providers/base.py` maps `inputs` + `defaults` + `--param` onto
endpoint arguments. Model note keys that steer it: `arg_map: {image: start_image_url}`
renames (a target ending in `s`, e.g. `image_urls`, gets a list; `a.b` nests),
`param_types: {duration: str}` coerces `--param` values after YAML parsing,
`optional_inputs: [image]` exempts a declared media input from the required check,
`min_duration_s` floors the per-second estimate.

ComfyUI models point `endpoint` at `workflows/<file>.json`; placeholders are filled from
`defaults`, `--param`, `prompt`, `image` (uploaded; the template must contain `{{image}}`),
`frames` (duration x `fps` when the template uses `{{frames}}`) and `seed` (random when `-1`).
