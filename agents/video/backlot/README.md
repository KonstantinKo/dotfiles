# backlot

CLI for the Backlot studio (see `ARCHITECTURE.md`). Python 3.12, run through `uv`;
the launcher is `bin/backlot` (linked to `~/.local/bin/backlot`).

```
backlot doctor                      # tools, key presence, vault, ComfyUI, model notes
backlot init <slug> [--format 16:9 --fps 24 --res 1920x1080 --budget 25]
backlot models [--kind image] [--provider fal] [--all]
backlot gen image --model fal-flux-schnell --prompt "..." [--shot S010] [--n 2]
            [--image <path|take>]... [--audio <path|take>]... [--video <path|take>]... [--end-image <path|take>]
            [--param k=v] [--parent img-003] [--depends-on Cast/Mia] [--dry-run] [--yes --authorization auth-...] [--force]
backlot tts --model kokoro --voice af_heart --text "..." [--shot S010]  # local zero-cost
backlot tts --model <paid-model> --text "..." --dry-run --json > quote.json
backlot tts --model <paid-model> --text "..." --yes --authorization auth-...
backlot batch plan.yaml [--dry-run] [--yes --authorization auth-...] [--force]
backlot authorize quote.json --source-message "Yes, submit this exact call" --source-ref <message-id> \
            --balance 10 --balance-unit EUR --balance-source "account page, now" --expires <ISO-time>
backlot decision approve picture picture-master --version <sha256> --scope "final picture" \
            --reason "accepted" --source-kind user --source-message "..." --source-ref <message-id> [--source-at <ISO-time>]
backlot handoff [--refresh] [--claim "House / S012" --worker editor --base-revision 0]
backlot recover img-003                                      # finish a failed/pending take by its request id
backlot takes [--shot S010] [--kind vid] [--status approved|pending|failed] [--stale]
backlot show img-003
backlot approve img-003 --reason "..." --source-ref <message-id> --source-message "..." [--scope "provisional production use"] [--lock Cast/Mia]
backlot reject img-003 --reason "..." [--source-message "<review finding or user decision>" --source-ref <evidence-or-message-ref>]
backlot stale Cast/Mia --reason "..." [--dry-run]            # transitive through Context `depends_on`
backlot captions vo-001 --model fal-elevenlabs-scribe --dry-run --json > quote.json
backlot captions vo-001 --model fal-elevenlabs-scribe --yes --authorization auth-...
backlot recover cap-001                                     # fetch or parse accepted STT job, no new create
backlot register existing-media.json --dry-run               # hash/probe and validate an existing output
backlot register existing-media.json                         # record external/supplied/local output; no provider call or media copy
backlot expense existing-operation.json                     # native-unit charge/estimate for one provider operation
backlot expense-allocation expense-... current_final --source-ref <evidence> --reason "..."
backlot lineage                                             # exact-source descendants needing review
backlot migrate --dry-run | backlot manifest                # schema preview; rebuild current take projection
backlot sheet --shot S010 [--kind img]                       # contact sheet -> renders/sheets/S010.jpg + shot note
backlot stage [--advance]                                    # gate check for the current stage
backlot requirements                                         # requirement registry used by stage and docs
backlot assembly edit-assembly.json [--dry-run]              # verify exact recipe, sources/ranges and output
backlot deliverable final-output.json [--dry-run]            # name the exact output version and approval scope
backlot historical-import approval-import.json [--dry-run]   # import an original user final approval for one old artifact
backlot delivery [--refresh]                                 # inspect; optionally write Deliverables.md
backlot review-record review.json | backlot repair-plan plan.json | backlot repair-result result.json
backlot score-plan score.json | backlot score-mix score.json
backlot archive create archive.json | backlot archive check <manifest> | backlot archive bundle <manifest> <new-dir>
backlot render [edit/timeline.yaml] [-o renders/x.mp4] [--preset youtube|shorts|draft] [--dry-run] [--allow-stale]
backlot reframe vid-002 --to 9:16 --focus left
backlot status [--refresh] | backlot cost [--refresh] | backlot thumbs
```

Every command accepts `--json` and `--project <slug>`; without `--project` the project is
found by walking up from the cwd to `project.yaml`. Config comes from
`~/projects/video/backlot/studio.yaml` (override with `BACKLOT_STUDIO`).

Exit codes: `0` ok, `1` error, `2` usage, `3` missing/mismatched exact-call
authorization, `4` budget exceeded.

## Existing media and expenses

`register` reads a JSON object with `kind` (`img|vid|vo|mus|sfx|up|cap`), `origin`
(`provider|supplied|local_derivative|assembly`), and `media` path. Optional `id`
enriches an existing take. Set `provider`, `operation_id`, `sha256`, `original_request`,
`effective_request`, `review_scope`, ordered `source_refs` (`id` or `path`, `sha256`,
`role`), and `coverage` (`shot` or `story`, inclusive `source_frames`/`output_frames`)
when known. A derivative or assembly requires exact source references. `register`
hashes and probes the original file, then stores a versioned hash reference to it;
it never calls a provider or copies media. `backlot lineage` checks registered output
bytes against that hash and flags changed or missing media and affected descendants.
The referenced file can still be overwritten externally; preserve a separate archive
when reproducibility requires the original bytes. Repeating the same provider/job/hash
import keeps its ID.
Use `backlot approve` with the original user message and narrow scope to accept a new
imported take; registration alone cannot create approval.

An optional `expense` object, or standalone `backlot expense`, records one operation
keyed by provider and operation ID. It keeps `estimate`, actual `charge_status`
(`charged|zero|unknown`), `charge`, and any `project_ledger` entry in their original
units, with source evidence and optional balance observations. `unknown` has no amount;
known zero records an explicit zero and unit. `allocation` records current-final use
as a subset of sunk spend. `Costs.md` keeps the EUR project budget projection from
takes separate from native provider charges; do not add a USD quote, EUR ledger entry,
and credit charge as if they were distinct payments. Accepted paid CLI calls also
record one operation with the quoted EUR budget estimate and unknown actual charge
until native provider evidence is supplied. Unregistered operations remain outside
the ledger's coverage.

Cloud routes with missing prices or undocumented zero prices stop before a quote or
provider call. `backlot models --json` shows route and readiness. `comfyui-local`
workflows claiming zero marginal provider cost need `local_zero_evidence` tied to the
exact model, route, workflow SHA-256, verification date and local-only cost scope;
an arbitrary graph on localhost does not establish this. Cloud zero-price promotions
need a route-specific source, observation time and expiry. The Higgsfield and
ComfyUI Cloud adapters remain non-callable stubs.

## Declared workflow and delivery

New `project.yaml` files declare a base workflow with named scenes and deliverables.
Add `requires` per scene only for the branches the Brief needs. The supported names
and evidence are generated from the runtime registry in
[`skills/studio/references/workflow-gates.md`](skills/studio/references/workflow-gates.md).
An older project can explicitly use `workflow: {schema_version: 1, preset: legacy}`
until its records are reconciled.

Register source media first. Register the final output as an `assembly` origin M2
artifact with `source_refs` for every used source. `backlot assembly` then records
`{id, route: native|external|custom, output: {artifact, sha256}, recipe: {path,
sha256}, segments: [{scene, output_frames: [start,end], source: {artifact|path,
sha256}, source_frames: [start,end]}], attachments: [...]}`. Inclusive output ranges
must cover every actual video frame exactly once. `backlot deliverable` records
`{id, kind: picture|scored|share, assembly, output: {artifact, sha256},
approval_scope}` and optional `share` or `historical_acceptance_id`. Changed media
needs a new artifact and deliverable ID. A matching `backlot decision` binds the
user's message and exact approval scope to the output hash. A partial decision
uses one or more `--coverage START:END` ranges.

Assembly registration counts frames once per unique source/output and stores the
probe facts with their SHA-256 values. Inspection rehashes current media and
reuses those facts for unchanged bytes. Older records count each unique asset
once per inspection without rewriting the record.

`backlot stage`, `status`, `cost` and `delivery` inspect without writing. Explicit
`--refresh` updates their derived notes; `stage --advance` changes the home note
summary only when all declared checks pass. The hand-written `Delivery.md` is not
overwritten. Actual media hash/probe and source-version checks apply to native,
external and custom routes alike. Every declared scene needs verified picture
frame coverage. For an archived final, `backlot historical-import` records
`{id, deliverable, kind, approval_scope, artifact, sha256, assembly, decision_id,
source_ref, source_at, source_evidence: {path, sha256}, covers}` after its typed
original user decision. The approval JSON must hold that output hash and user
quote. The original approval time must precede artifact migration registration.
The imported record applies only to that artifact and assembly recipe; new bytes
must satisfy declared requirements normally.

## What a generation does

1. Reads the model note (`<vault>/Studio/Models/<id>.md`), builds the request, estimates
   the cost (`cost_unit` x n / seconds / chars).
2. `--dry-run --json` prints the normalized quote and request fingerprint. Record the
   user's explicit approval for that exact call with `backlot authorize`; the balance
   must be observed separately and its source recorded. The CLI checks budget, per-call
   ceiling, quote, expiry and one-use authorization before the provider call. `--yes`
   alone is never approval. Local zero-cost operations do not need authorization.
3. Under `takes/.lock`: re-checks the budget (pending and failed takes count as spent),
   reserves the next id and writes `takes/<id>/meta.yaml` with `status: pending`.
4. Runs the provider. fal records the `request_id` into the meta before waiting and gives
   up after `providers.fal.timeout_s` (default 900 s). A failure after the request was
   submitted leaves the take `failed` with its cost; `backlot recover <id>` fetches the
   result later. A proven pre-submit failure drops the reservation; uncertain submission
   stays recorded for billing review.
   Paid captions reserve `cap-###` before submission, store the accepted job ID and raw
   response, and count the estimate even when timestamp parsing fails. `recover cap-###`
   fetches the accepted result or reparses the saved response without creating another job.
5. Saves `takes/<id>/out.<ext>`, `prompt.txt`, `meta.yaml`, and rebuilds the current `takes/manifest.jsonl` projection.
6. Writes the vault: `_thumbs/<id>.jpg` (also waveforms), `Takes/<id>.md` with
   vault-root-relative links (`[[Projects/<slug>/Shots/S010|S010]]`), then regenerates
   `Costs.md`, `Status.md` and `spent_eur` on the project home.

Take ids are `<kind>-<seq>` (`img-014`); `--parent img-014` yields `img-014.2` and must be
the same kind as the new take. `--image/--audio/--video` repeat when the model's `arg_map`
target ends in `s` (`image_urls`); a singular target with two values is an error.
`--end-image` maps through `arg_map.end_image` (default `end_image_url`) for models that
list `end_image` in `inputs`.

Thresholds (`project.yaml`, falling back to `defaults:` in `studio.yaml`):
`max_call_eur` (1.0) and `escalate_pct` (80; `status` prints an ESCALATE line at or
above this share of the budget). Legacy `confirm_over_eur` and
`ask_before_generate` do not waive exact-call approval.

## Batch plans

`backlot batch plan.yaml --dry-run --json` plans every request first and prints ordered
`quotes`. Each paid call needs its own authorization; pass the IDs in call order with
repeated `--authorization` flags and `--yes`. The batch stops at the first provider error and prints the take IDs made
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
