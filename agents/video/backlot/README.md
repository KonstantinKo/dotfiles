# backlot

CLI for the Backlot studio (see `../ARCHITECTURE.md`). Python 3.12, run through `uv`;
the launcher is `../bin/backlot` (linked to `~/.local/bin/backlot`).

```
backlot doctor                      # tools, key presence, vault, ComfyUI, model notes
backlot init <slug> [--format 16:9 --fps 24 --res 1920x1080 --budget 25]
backlot models [--kind image] [--provider fal] [--all]
backlot gen image --model fal-flux-schnell --prompt "..." [--shot S010] [--n 2]
            [--image <path|take>] [--audio <path|take>] [--video <path|take>] [--param k=v]
            [--parent img-003] [--depends-on Cast/Mia] [--dry-run] [--yes]
backlot tts --model kokoro --voice af_heart --text "..." | --file vo.txt [--shot S010] [--yes]
backlot takes [--shot S010] [--kind vid] [--status approved] [--stale]
backlot show img-003
backlot approve img-003 --reason "..." [--lock Cast/Mia]
backlot reject img-003 --reason "..."
backlot stale Cast/Mia --reason "..."
backlot captions vo-001 [--model fal-elevenlabs-scribe]
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
2. Refuses over budget; exits 3 without `--yes`.
3. Runs the provider, saves `takes/<id>/out.<ext>`, `prompt.txt`, `meta.yaml`, appends
   `takes/manifest.jsonl`.
4. Writes the vault: `_thumbs/<id>.jpg|png`, `Takes/<id>.md`, then regenerates
   `Costs.md`, `Status.md` and `spent_eur` on the project home.

Take ids are `<kind>-<seq>` (`img-014`); `--parent img-014` yields `img-014.2`.

## Timeline

`edit/timeline.yaml` as in the architecture spec. `src` is a take id, a render name or
a path. Stills take `duration` and optional `motion: kenburns`; clips take `in`/`out` and
an optional `transition: {type: xfade, name: fade, duration: 0.5}` into the next clip.
Audio tracks: `at`, `gain_db`, `out` (trim, seconds), `fade_out_s`, `duck_under: <track>` + `duck_db`.
Sources that are rejected or stale takes are refused unless `--allow-stale` is given. Captions burn the
take's `.srt` (from `backlot captions`); titles use `style: lower-third|center`.
Titles and captions are rendered with Pillow and composited with `overlay`, so the
Homebrew ffmpeg (no drawtext/libass) works.

## Layout

```
backlot/            package: cli, config, project, models, takes, vault, gen, decisions,
                    render, reframe, captions, thumbs, overlays, scaffold, doctor, providers/
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
`defaults`, `--param`, `prompt`, `image` (uploaded) and `seed` (random when `-1`).
