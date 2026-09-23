# Backlot — agent-driven video production studio

Backlot is a local, file-based reimplementation of the workflow invideo pioneered with
Agent One / Agent Two (persistent project Context, expert role agents, pre-production
locks, model router, takes with thread IDs, self-review, conversational revision, guided
Workflows, Playbooks), rebuilt around three principles they don't have:

1. **Plain files are the product.** Every decision, lock, take and cost lives in Markdown
   or YAML that Obsidian renders and git versions. Nothing is trapped in a UI.
2. **Nothing is generated without a reason and a budget.** The agent knows what it is
   about to spend, says so, and by default asks first. Runaway generation is impossible
   by construction (per-project budget in `project.yaml`, enforced by the CLI).
3. **Providers are plugins.** fal.ai and the local ComfyUI Desktop are the first two.
   ComfyUI Cloud, Higgsfield or anything else is one adapter file plus model notes,
   with no change to skills or vault layout.

## The three places

| Place | Path | Role | Git |
|---|---|---|---|
| **Vault** | `~/projects/obsidian/Backlot/` | Source of truth: studio knowledge + per-project Context, shots, takes index, decisions, status, costs. Markdown only, plus small thumbnails. | own repo |
| **Projects root** | `~/projects/video/` | Working directory for all productions. Holds the agent instructions, skills, sub-agents, commands (all symlinked from dotfiles) and `studio.yaml`. Not a git repo itself. | none |
| **Project dir** | `~/projects/video/<slug>/` | Binaries and machine state for one production: inputs, takes (media + meta), edit timeline, renders. | own repo per project; media ignored |
| **Toolkit** | `~/dotfiles/agents/video/` | Everything tracked: this spec, skills, sub-agents, commands, `AGENTS.md`, `studio.yaml`, the `backlot` CLI. `make` in dotfiles links it into place. | dotfiles repo |

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

## Project dir layout (`~/projects/video/<slug>/`)

```
<slug>/
├── project.yaml     # slug, vault_project (abs path), format, fps, resolution, budget_eur,
│                    #   ask_before_generate, default models per kind
├── inputs/          # user-supplied: treatment PDFs, decks, footage, reference images
├── takes/
│   ├── manifest.jsonl          # append-only, one line per take (same fields as vault note)
│   └── <id>/                   # e.g. img-014/
│       ├── meta.yaml           # request, response, timing, cost, provider job id
│       ├── prompt.txt
│       └── out.<ext>           # the media
├── edit/
│   └── timeline.yaml           # the "Slate" substitute (see below)
├── renders/
└── .gitignore                  # takes/**/out.* renders/ inputs/**/*.{mp4,mov,wav} …
```

## `backlot` CLI (Python 3.12, `uv run`, single package at `agents/video/backlot/`)

Launcher `agents/video/bin/backlot` → linked to `~/.local/bin/backlot`. Reads
`~/projects/video/studio.yaml` for `vault`, `projects_root`, `currency`, provider config.
Project is resolved from cwd (walk up to `project.yaml`) or `--project <slug>`.

Commands (all print terse one-line results; `--json` for machine output):

- `backlot init <slug> [--format 16:9] [--fps 24] [--res 1920x1080] [--budget 25]`
  scaffolds vault project (from `_templates/`) + project dir + `git init` + `.gitignore`.
- `backlot models [--kind K] [--provider P] [--all]` lists active and untested models from
  the vault (untested marked); `--all` includes disabled ones.
- `backlot gen <kind> --model <id> --prompt "..." [--image <path|take>] [--audio <path|take>]
  [--video <path|take>] [--shot S010] [--n 2] [--param k=v]... [--parent <take>]
  [--depends-on Cast/Mia,...] [--dry-run] [--yes]`
  Validates ids, required inputs and `--depends-on` notes, then estimates cost (from the
  model note). If `ask_before_generate` is true and `--yes` is absent, prints the estimate
  and exits 3 (the agent asks the user, then re-runs with `--yes`). Refuses if the budget
  is 0, missing or would be exceeded. Runs provider, saves take, thumbnail, vault note,
  manifest line, updates `spent_eur`.
- `backlot tts --model <id> --voice <id> (--text "..."|--file f) [--shot] ...` same as gen with kind `vo`.
- `backlot takes [--shot S010] [--kind] [--status] [--stale]`, `backlot show <take>`.
- `backlot approve <take> [--lock Cast/Mia] --reason "..."`, `backlot reject <take> --reason "..."`
  update take + shot notes and append to `Decisions.md`; `--lock` sets `locked: true`
  and `locked_take` on a Context note.
- `backlot stale <Context note name> --reason "..."` marks every take/shot whose
  `depends_on` includes that note as `stale` (this is how "make Mia blonde" propagates).
- `backlot captions <take|audio> --model <stt-id>` → `.srt` + word timestamps JSON.
- `backlot render [edit/timeline.yaml] [-o renders/name.mp4] [--preset youtube|shorts|draft]
  [--allow-stale]` ffmpeg assembly (see timeline); refuses rejected or stale take sources
  unless `--allow-stale`.
- `backlot reframe <take|render> --to 9:16 [--focus center|left|right|auto]`.
- `backlot status` rewrites `Status.md` (stage, shots by status, stale count, spend, next
  actions) and returns it; `backlot cost` rewrites `Costs.md`.
- `backlot thumbs` regenerates thumbnails; `backlot doctor` checks keys, ffmpeg, ComfyUI
  reachability, vault path, model notes parse.

Providers (`backlot/providers/<name>.py`, a `Provider` protocol with `estimate(model,
req)` and `run(model, req) -> files`):

- `fal`: uses `fal_client` (`submit` + `get`); `FAL_KEY` from env or macOS Keychain (service `fal-api`,
  account `FAL_KEY`, same item ComfyUI uses). Never writes the key to disk. Endpoint and
  argument mapping come from the model note (`endpoint`, `defaults`, `inputs`, `arg_map`,
  `param_types`). Provider failures surface as one `ProviderError` line.
- `comfyui-local`: POSTs a workflow JSON to `http://127.0.0.1:8188/prompt`, polls
  `/history`, fetches outputs. Workflow templates live in
  `agents/video/backlot/workflows/<model-id>.json` with `{{prompt}}`-style placeholders
  named in the model note.
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
  - {src: img-014.2, duration: 3.0, motion: kenburns}   # stills get duration + optional motion
audio:
  - {track: vo, src: vo-003, at: 0.0, gain_db: 0}
  - {track: music, src: mus-001, at: 0.0, out: 32.0, fade_out_s: 1.0, gain_db: -14, duck_under: vo, duck_db: -10}
captions: {src: vo-003, style: default, burn: true}   # uses the take's .srt
titles:
  - {text: "...", at: 0.0, duration: 2.0, style: lower-third}   # optional, ffmpeg drawtext
```
Renders are deterministic from this file; agents edit the YAML, never a GUI. Exporting
to a real NLE later is a separate exporter, not part of v1.

## Skills (`agents/video/skills/<name>/SKILL.md`, harness-neutral)

The lead agent runs the production; role sub-agents do bounded work; every skill reads
the vault before acting and writes results back. Stages and their gates:

| Stage | Skill | Gate to pass |
|---|---|---|
| brief | `brief` | `Brief.md` agreed by user |
| develop | `develop` | `Script.md` locked (beats, VO lines, durations) |
| preproduction | `preproduction` | four locks: cast, locations/props, visual language, format & deliverables (invideo's "four locks", plus voice per cast member) |
| boards | `storyboard` | every shot has an approved `board_take` |
| shots | `generate` | every shot has an approved `video_take` |
| voice / score | `voice`, `score` | vo takes approved, music/sfx placed |
| assemble | `assemble` | `timeline.yaml` renders a draft |
| review | `review` | continuity + brief compliance pass, or a flagged list |
| deliver | `deliver` | exports in `renders/`, `Status.md` says delivered |

Cross-cutting skills: `studio` (operating manual + lead-agent behaviour, role crew,
"what's the update"), `project-init`, `revise` (context change → `backlot stale` →
regeneration plan), `ingest` (PDF/deck/URL/footage → `Context/Knowledge.md` +
`Inspiration.md`), `models` (how to read/extend the catalog and add providers).

Playbook defaults every skill honours: ask before generating (show estimate); prefer
`lite` tier for exploration and `pro|ultra` only for locked shots; generate boards before
video; 2–4 options per unlocked element, 1 for locked; never overwrite a take (new
variation instead); every generated asset lists its `depends_on` Context notes; every
approval/rejection has a reason in `Decisions.md`.

Role sub-agents (`agents/video/claude/agents/*.md`, linked to
`~/projects/video/.claude/agents/`): `screenwriter`, `director`, `dop` (shot & prompt
craft), `casting-director`, `production-designer`, `sound-designer`, `editor`,
`continuity` (vision-based reviewer that compares takes against Context and flags drift).
Each declares which vault notes it reads and which it may write.

Commands (`agents/video/commands/*.md`): `/new-project`, `/update` (status rollup),
`/lock`, `/approve`, `/reject`, `/gen` (thin wrappers that call the skill or CLI).

## How it reaches the machine (dotfiles `install.sh`)

```
agents/video/AGENTS.md           -> ~/projects/video/AGENTS.md  (+ CLAUDE.md shim)
agents/video/studio.yaml         -> ~/projects/video/studio.yaml
agents/video/skills/*            -> ~/projects/video/.claude/skills/*  and .agents/skills/*
agents/video/commands/*.md       -> ~/projects/video/.claude/commands/*.md
agents/video/claude/agents/*.md  -> ~/projects/video/.claude/agents/*.md
agents/video/bin/backlot         -> ~/.local/bin/backlot
```
Nothing is linked into `~/.claude`, so none of this appears in day-job or games sessions.
Claude Code discovers `.claude/skills`, `.claude/agents` and `CLAUDE.md` from the parent
directory when the cwd is a project subfolder (verified on 2.1.280).

## Open by design (not built in v1, but the seams exist)

- More providers: one adapter file + model notes.
- NLE export (FCPXML/EDL) from `timeline.yaml`.
- Remotion/HyperFrames as an alternative renderer for motion graphics.
- Multiplayer: the vault is a git repo; collaborators edit Context, the ledger merges.
- Region-annotated edits: `backlot gen --image <take> --mask <png>` once a model note declares `inputs: [mask]`.
