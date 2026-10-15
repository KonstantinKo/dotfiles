# Backlot — agent-driven video production studio

Backlot is a local, file-based reimplementation of the workflow invideo pioneered with
Agent One / Agent Two (persistent project Context, expert role agents, pre-production
locks, model router, takes with thread IDs, self-review, conversational revision, guided
Workflows, Playbooks), rebuilt around three principles they don't have:

1. **Plain files are the product.** Every decision, lock, take and cost lives in Markdown
   or YAML that Obsidian renders and git versions. Nothing is trapped in a UI.
2. **Nothing is generated without a reason and a budget.** Before every paid provider
   call, quote its exact inputs, settings, route and estimated cost, show the observed
   provider balance, and record the user's explicit approval for that call. The CLI
   enforces one-use authorization and the per-project budget in `project.yaml`.
3. **Providers are plugins.** fal.ai and the local ComfyUI Desktop are the first two.
   ComfyUI Cloud, Higgsfield or anything else is one adapter file plus model notes,
   with no change to skills or vault layout.

## The three places

| Place | Path | Role | Git |
|---|---|---|---|
| **Vault** | `~/projects/obsidian/Backlot/` | Source of truth: studio knowledge + per-project Context, shots, takes index, decisions, status, costs. Markdown only, plus small thumbnails. | own repo |
| **Projects root** | `~/projects/video/backlot/` | Working directory for Backlot productions. Holds the agent instructions, skills, sub-agents, commands (all symlinked from dotfiles) and `studio.yaml`. Not a git repo itself. | none |
| **Project dir** | `~/projects/video/backlot/<slug>/` | Binaries and machine state for one production: inputs, takes (media + meta), edit timeline, renders. | own repo per project; media ignored |
| **Toolkit** | `~/dotfiles/agents/video/backlot/` | Everything tracked: this spec, skills, sub-agents, commands, `AGENTS.md`, `studio.yaml`, the `backlot` CLI. `make` in dotfiles links it into place. | dotfiles repo |

Rule: the vault says *what is true and decided*; the project dir holds *what was produced*.
The CLI keeps them in sync (every take gets a vault note + thumbnail; every approval lands
in `Decisions.md`).

## Vault layout (`~/projects/obsidian/Backlot/`)

```
Backlot/
├── Backlot.md                 # home note: what this is, how a production flows, links
├── Dashboard.base             # Bases view over Projects/*/<slug>.md (status, stage, budget)
├── Studio/                    # studio-wide knowledge, reused by every project
│   ├── Playbooks/             # standing rules the agent obeys unless a project overrides
│   │   └── Default.md         #   e.g. ask-before-generate, 4 options per location, naming
│   ├── Workflows/             # guided multi-step jobs (invideo "Workflows"), one note each:
│   │   ├── Casting.md         #   Casting, Reference Research, Production Design,
│   │   ├── ...                #   Storyboarding, Ad Variations, Localisation,
│   │   └── Reframing.md       #   Campaign Transfer, Reframing 16:9→9:16
│   ├── Models/                # one note per model; frontmatter is machine-read by the CLI
│   │   ├── Models.base        #   table view: kind, provider, tier, cost, status
│   │   └── <model-id>.md
│   ├── Providers/             # one note per provider: how it's reached, auth, quirks
│   │   ├── fal.md
│   │   ├── comfyui-local.md
│   │   ├── comfyui-cloud.md   #   status: not configured (stub)
│   │   └── higgsfield.md      #   status: not configured (stub)
│   ├── Voices/                # voice catalog (provider, voice id, sample, character notes)
│   ├── Styles/                # reusable visual languages (prompt fragments, refs, LUT notes)
│   ├── Brands/                # brand guidelines usable across projects
│   └── Lessons/               # retros; distilled into Playbooks over time
├── Projects/
│   └── <slug>/
│       ├── <slug>.md          # project home (frontmatter: status, stage, format, fps,
│       │                      #   resolution, budget_eur, spent_eur, deliverables[])
│       ├── Brief.md           # the agreed brief (goal, audience, tone, length, deliverables)
│       ├── Treatment.md       # story/treatment; Script.md once locked
│       ├── Script.md
│       ├── Context/           # invideo "Context": what every sub-agent must respect
│       │   ├── Rules.md       #   project overrides of Playbooks, aspect, model choices
│       │   ├── World.md       #   world building, era, logic
│       │   ├── Visual Language.md
│       │   ├── Inspiration.md #   references with *intent* ("the lighting, not the palette")
│       │   ├── Knowledge.md   #   facts from source docs (PDF/deck/URL ingested)
│       │   ├── Cast/<Name>.md #   look, wardrobe, voice, lock status, sheet thumbs
│       │   ├── Locations/<Name>.md
│       │   └── Props/<Name>.md
│       ├── Shots/             # one note per shot, frontmatter machine-read
│       │   ├── Shots.base     #   board view: shot, status, duration, cast, location, take
│       │   └── S010.md        #   S010, S020… (gaps allow inserts)
│       ├── Takes/             # written by the CLI, one note per take, embeds thumbnail
│       │   ├── Takes.base
│       │   └── img-014.md
│       ├── _thumbs/           # ≤ 256 px JPEG/first-frame per take (tracked, small)
│       ├── Decisions.md       # ledger, newest on top: approve/reject/lock with reason
│       ├── Status.md          # "what's the update" rollup, regenerated by `backlot status`
│       └── Costs.md           # per-take spend, regenerated by `backlot cost`
└── _templates/                # Templater-free plain templates the CLI and skills copy
```

Frontmatter contracts (the CLI parses these; keep keys stable):

- `Studio/Models/<id>.md`:
  `id, provider (fal|comfyui-local|comfyui-cloud|higgsfield|local), kind (image|video|tts|music|sfx|upscale|stt|lipsync), endpoint, tier (lite|pro|ultra), cost_unit (per_image|per_second|per_1k_chars|per_run), cost_eur, status (active|untested|disabled), inputs [prompt, image, audio, video, ...], optional_inputs [], max_duration_s, min_duration_s, resolutions [], defaults {}, arg_map {input: argument}, param_types {param: str|int|float|bool}` and a body with strengths, limits, prompt tips. Template: `_templates/Model.md`. Every declared media input is required at `gen` time unless listed in `optional_inputs`; `min_duration_s` floors the estimate; `arg_map` renames (targets ending in `s` get a list, `a.b` nests); `param_types` coerces `--param` values.
- `Projects/<slug>/<slug>.md`: `status (idea|brief|develop|preproduction|boards|shots|voice|score|assemble|review|delivered), format, fps, resolution, budget_eur, spent_eur`. `ask_before_generate` lives only in `project.yaml`.
- `Shots/S###.md`: `shot, status (planned|boarded|approved|generated|locked|stale), duration_s, cast [], location, props [], board_take, video_take, vo_take, depends_on [] (Context note names)`. The CLI moves `status`: first board take saved → `boarded`; board take approved → `approved`; video take saved → `generated`; `backlot stale` → `stale`. `locked` is set by hand and never changed by the CLI. `backlot gen --shot S###` creates a missing shot note from `Shots/_template.md`.
- `Takes/<id>.md`: `take, kind, model, provider, shot, status (new|approved|rejected|stale), cost_eur, parent (take id for variations), depends_on [], file (relative to project dir), prompt, params {}`.
- `Context/Cast|Locations|Props/*.md`: `locked (bool), locked_take, voice (Cast only)`.

Take IDs: `<kind>-<seq>` (`img-014`), variations `<id>.<n>` (`img-014.2`), where kind is
`img|vid|vo|mus|sfx|up`. Shot IDs `S010`. Stable, quotable in chat ("combine img-014.2 and vid-009").

## Project dir layout (`~/projects/video/backlot/<slug>/`)

```
<slug>/
├── project.yaml     # slug, vault_project (abs path), format, fps, resolution, budget_eur,
│                    #   ask_before_generate, default models per kind
├── inputs/          # user-supplied: treatment PDFs, decks, footage, reference images
├── takes/
│   ├── manifest.jsonl          # rebuildable current projection, one line per take
│   └── <id>/                   # e.g. img-014/
│       ├── meta.yaml           # request, response, timing, cost, provider job id
│       ├── prompt.txt
│       └── out.<ext>           # the media
├── edit/
│   ├── timeline.yaml           # native renderer input when that route is selected
│   └── assemblies/<id>.yaml   # exact source ranges, recipe hash and output probe
├── deliverables/<id>.yaml      # named output version and approval scope
├── deliverables/historical-acceptances/<id>.yaml # imported original approval for one artifact/recipe
├── renders/
└── .gitignore                  # takes/**/out.* renders/ inputs/**/*.{mp4,mov,wav} …
```

## `backlot` CLI (Python 3.12, `uv run`, single package at `agents/video/backlot/`)

Launcher `agents/video/backlot/bin/backlot` → linked to `~/.local/bin/backlot`. Reads
`~/projects/video/backlot/studio.yaml` for `vault`, `projects_root`, `currency`, provider config.
Project is resolved from cwd (walk up to `project.yaml`) or `--project <slug>`.

Commands (all print terse one-line results; `--json` for machine output):

- `backlot init <slug> [--format 16:9] [--fps 24] [--res 1920x1080] [--budget 25]`
  scaffolds vault project (from `_templates/`) + project dir + `git init` + `.gitignore`.
- `backlot models [--kind K] [--provider P] [--all]` lists active and untested models from
  the vault (untested marked); `--all` includes disabled ones.
- `backlot gen <kind> --model <id> --prompt "..." [--image <path|take>]... [--audio <path|take>]...
  [--video <path|take>]... [--end-image <path|take>] [--shot S010] [--n 2] [--param k=v]...
  [--parent <take>] [--depends-on Cast/Mia,...] [--dry-run] [--yes --authorization auth-...] [--force]`
  Validates ids, required inputs and `--depends-on` notes, then estimates cost (from the
  model note). `--dry-run --json` produces the normalized quote. After the user approves
  that exact call, `backlot authorize <quote.json>` records the original approval text
  and message reference, observed balance with its native unit and source, and expiry.
  Execute with `--yes --authorization <id>`; `--yes` alone is never approval. Each accepted
  paid call consumes one authorization. A changed request or paid retry needs a new quote
  and approval. Free local calls need no spend authorization. The spend guard, shared by
  `gen`, `tts`, `batch` and `captions`, rejects missing/mismatched approval with exit 3;
  budget 0, missing or exceeded → exit 4; a single provider call above `max_call_eur` →
  exit 4 unless `--force`. Then, under an
  `fcntl` lock on `<project>/takes/.lock`: re-check the budget counting `pending` and
  `failed` takes as spent, allocate the id, write `takes/<id>/meta.yaml` with
  `status: pending`. Provider runs outside the lock (fal records `request_id` into the
  meta before waiting; `providers.fal.timeout_s`, default 900 s). Save (again under the
  lock): take, thumbnail, vault note, manifest projection, `spent_eur`. A failure after the
  request was submitted keeps the take as `failed` with `request_id` and cost; a failure
  before submission drops the reservation. `--image/--audio/--video` repeat when the
  model's `arg_map` target ends in `s` (list argument); a singular target refuses more
  than one. `--end-image` maps via `arg_map.end_image` (default `end_image_url`) and needs
  `end_image` in the model's `inputs`. `--parent` must be a take of the same kind.
- `backlot tts --model <id> --voice <id> (--text "..."|--file f) [--shot] ...` same as gen with kind `vo`.
- `backlot batch <plan.yaml> [--dry-run] [--yes --authorization auth-...]... [--force]` plans a list of gen/tts requests
  (`requests:` or a top-level list; fields as the CLI flags: `kind, model, prompt, text|file,
  voice, image|audio|video (string or list), end_image, shot, n, params {}, parent,
  depends_on []`), prints ordered quotes; each paid call needs its own authorization in
  request order. It applies
  the same budget/max-call rules to the whole batch, runs sequentially, stops at the first
  provider error (exit 1) and prints the take ids produced.
- `backlot recover <take>` re-fetches a `failed`/`pending` take's result by its
  `request_id` (`fal_client.status` + `result`) and completes it (media, thumb, note).
- `backlot takes [--shot S010] [--kind] [--status new|approved|rejected|stale|pending|failed] [--stale]`, `backlot show <take>`.
- `backlot approve <take> [--lock Cast/Mia] --reason "..." --source-message "..." --source-ref <message-id>`,
  `backlot reject <take> --reason "..." [--source-message "..."] [--source-ref <evidence>]`
  record scoped decisions with their source, update take + shot notes and refresh
  `Decisions.md`; `--lock` sets `locked: true`
  and `locked_take` on a Context note. Approving a take of a model whose note is
  `status: untested` sets it `active` and appends a `## Observed` line (date, take,
  seconds, cost) to the note body.
- `backlot stale <Context note name> --reason "..." [--dry-run]` marks every take/shot whose
  `depends_on` includes that note as `stale` (this is how "make Mia blonde" propagates).
  Transitive: Context notes whose frontmatter `depends_on` lists a marked note are marked
  too (`stale: true`, `stale_reason`), recursively and cycle-safe, and their dependants
  follow. `--dry-run` prints what would be marked without writing.
- `backlot captions <take|audio> --model <stt-id> [--dry-run] [--yes --authorization auth-...] [--force]`
  → `.srt` + word timestamps JSON; goes through the same spend guard as `gen`.
- `backlot sheet --shot S010 [--kind img|vid]` writes a labelled contact sheet (≤ 1600 px
  wide) to `<project>/renders/sheets/S010.jpg`, a ≤ 512 px copy to `_thumbs/sheet-S010.jpg`,
  and replaces the `## Candidates` section of the shot note with the embed + take links.
- `project.yaml workflow` declares named scenes, deliverables and a short requirement
  vocabulary. `backlot stage --json` checks each scene and exact output version without
  writing. The base path needs an agreed Brief, registered output, complete ordered
  source coverage, actual media hash/probe and a version/scoped user decision. Optional
  board, identity, world, spatial/Blender, voice, caption, score, graphic, review and
  share checks activate only when declared. A required scene or deliverable missing
  entirely fails. `--advance` updates the project home summary only after a pass.
  Projects explicitly marked `workflow.preset: legacy` retain the older stage gates.
- `backlot assembly <spec.json>` registers a native, external or custom edit recipe,
  exact source/output frame map, actual output probe and content hashes. Its output is
  an M2 registered artifact whose `source_refs` cover every used source. `backlot
  deliverable <spec.json>` records a named immutable output version and its approval
  scope. `backlot delivery` verifies the output, recipe, source lineage, frame coverage
  and matching typed user approval. `--refresh` writes only derived `Deliverables.md`;
  the hand-written `Delivery.md` remains a narrative record.
- `backlot render [edit/timeline.yaml] [-o renders/name.mp4] [--preset youtube|shorts|draft]
  [--allow-stale]` ffmpeg assembly (see timeline); refuses rejected or stale take sources
  unless `--allow-stale`. Writes the merged captions as `renders/<name>.srt` next to the
  render whenever the timeline has a `captions:` block, burned or not.
- `backlot reframe <take|render> --to 9:16 [--focus center|left|right|auto]`.
- `backlot status` and `backlot cost` compute read-only views by default. Their
  `--refresh` flags rewrite the derived `Status.md` or `Costs.md` projections and the
  EUR home-note projection. The native charge ledger remains separate from EUR.
- `backlot thumbs` regenerates thumbnails (always JPEG, `_thumbs/<id>.jpg`, waveform for
  audio); `backlot doctor` checks keys, ffmpeg, ComfyUI reachability, vault path, model
  notes parse.

Spend thresholds live in `project.yaml` (written by `init`) and fall back to `defaults:` in
`studio.yaml`: `confirm_over_eur` (default 0 = always confirm), `max_call_eur` (default 1.0),
`escalate_pct` (default 80).

Vault links written by the CLI are vault-root-relative so they stay unambiguous across
projects: `[[Projects/<slug>/Shots/S010|S010]]`, `[[Projects/<slug>/Context/Cast/Mia|Mia]]`,
`thumb: "[[Projects/<slug>/_thumbs/img-001.jpg]]"`, embeds `![[Projects/<slug>/_thumbs/...]]`.

Providers (`backlot/providers/<name>.py`, a `Provider` protocol with `estimate(model,
req)` and `run(model, req) -> files`):

- `fal`: uses `fal_client` (`submit`, then `status` polling until completed, then `get`);
  the request id is handed back to the CLI right after `submit` and stored in the pending
  take's meta; `timeout_s` (default 900) bounds the wait; `fetch` re-reads a finished
  request by id for `backlot recover`. `FAL_KEY` from env or macOS Keychain (service
  `fal-api`, account `FAL_KEY`, same item ComfyUI uses). Never writes the key to disk.
  Endpoint and argument mapping come from the model note (`endpoint`, `defaults`, `inputs`,
  `arg_map`, `param_types`). Provider failures surface as one `ProviderError` line.
- `comfyui-local`: POSTs a workflow JSON to `http://127.0.0.1:8188/prompt`, polls
  `/history`, fetches outputs. Workflow templates live in
  `agents/video/backlot/workflows/<model-id>.json` with `{{prompt}}`-style placeholders
  named in the model note. `{{frames}}` is filled from the request duration × `fps`
  (defaults/`--param`) when present; `{{image}}` receives the uploaded input image and the
  provider fails with "workflow template has no {{image}} node" when an image is given
  but the template lacks it.
- `local`: no-network helpers used by tts (`kokoro`, `edge-tts` CLIs) and by render.
  Subprocesses get a hard timeout (`providers.local.timeout_s`, default 120 s).
- `comfyui-cloud`, `higgsfield`: stubs raising `ProviderNotConfigured` with a pointer to
  the provider note. Adding one = implement the two methods.

Timeline (`edit/timeline.yaml`), the "Slate" substitute, rendered by ffmpeg:

```yaml
format: 16:9
fps: 24
resolution: 1920x1080
video:                     # ordered clips; `src` is a take id, a render, or a file
  - {src: vid-009, in: 0.0, out: 4.5, transition: {type: xfade, name: fade, duration: 0.5}}
  - {src: vid-010, in: 0.0, out: 3.0, audio: keep, gain_db: -6}   # mix the clip's own sound at its position
  - {src: img-014.2, duration: 3.0, motion: kenburns}   # stills get duration + optional motion
audio:
  - {track: vo, src: vo-003, at: 0.0, gain_db: 0}
  - {track: vo, src: vo-004, at: 4.5}
  - {track: music, src: mus-001, at: 0.0, out: 32.0, fade_out_s: 1.0, gain_db: -14, duck_under: vo, duck_db: -10}
captions: {from: vo, style: default, burn: true}   # every `track: vo` row's .srt, shifted by its `at`
# or: captions: {src: vo-003}                       # one file, shifted by that row's `at`; merged .srt always written
titles:
  - {text: "...", at: 0.0, duration: 2.0, style: lower-third}   # optional, ffmpeg drawtext
```
Renders are deterministic from this file; agents edit the YAML, never a GUI. Exporting
to a real NLE later is a separate exporter, not part of v1.

## Skills (`agents/video/backlot/skills/<name>/SKILL.md`, harness-neutral)

The lead agent runs the production; role sub-agents do bounded work. Skills are
selected for the declared scene or deliverable requirement. The requirement table is
generated from `backlot.workflow.REQUIREMENTS` in
`skills/studio/references/workflow-gates.md`. The project home stage is a summary;
`backlot stage --json` reports actual blockers by scene and deliverable.

Cross-cutting skills: `studio` (operating manual + lead-agent behaviour, role crew,
"what's the update"), `project-init`, `revise` (context change → `backlot stale` →
regeneration plan), `ingest` (PDF/deck/URL/footage → `Context/Knowledge.md` +
`Inspiration.md`), `models` (how to read/extend the catalog and add providers).

Playbook defaults every skill honours: obtain exact-call approval before paid provider
submission; prefer
`lite` tier for exploration and `pro|ultra` only for locked inputs; generate boards before
video when declared; 2–4 options per unlocked element, 1 for locked; never overwrite a take (new
variation instead); every generated asset lists its `depends_on` Context notes; every
approval/rejection has a reason in `Decisions.md`.

Role sub-agents (`agents/video/backlot/claude/agents/*.md`, linked to
`~/projects/video/backlot/.claude/agents/`): `screenwriter`, `director`, `dop` (shot & prompt
craft), `casting-director`, `production-designer`, `sound-designer`, `editor`,
`continuity` (vision-based reviewer that compares takes against Context and flags drift).
Each declares which vault notes it reads and which it may write.

Commands (`agents/video/backlot/commands/*.md`): `/new-project`, `/update` (status rollup),
`/lock`, `/approve`, `/reject`, `/gen` (thin wrappers that call the skill or CLI).

## How it reaches the machine (dotfiles `install.sh`)

```
agents/video/AGENTS.md                 -> ~/projects/video/AGENTS.md
agents/video/backlot/AGENTS.md         -> ~/projects/video/backlot/AGENTS.md
agents/video/backlot/studio.yaml       -> ~/projects/video/backlot/studio.yaml
agents/video/backlot/skills/*          -> ~/projects/video/backlot/.claude/skills/* and .agents/skills/*
agents/video/backlot/commands/*.md     -> ~/projects/video/backlot/.claude/commands/*.md
agents/video/backlot/claude/agents/*.md -> ~/projects/video/backlot/.claude/agents/*.md
agents/video/backlot/bin/backlot       -> ~/.local/bin/backlot
```
Nothing is linked into `~/.claude`, so none of this appears in day-job or games sessions.
`install.sh` also links skills into each Git-backed production for Codex and Claude.
Claude Code reads `AGENTS.md` when no `CLAUDE.md` is present in the project.

## Open by design (not built in v1, but the seams exist)

- More providers: one adapter file + model notes.
- NLE export (FCPXML/EDL) from `timeline.yaml`.
- Remotion/HyperFrames as an alternative renderer for motion graphics.
- Multiplayer: the vault is a git repo; collaborators edit Context, the ledger merges.
- Region-annotated edits: `backlot gen --image <take> --mask <png>` once a model note declares `inputs: [mask]`.
