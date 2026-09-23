# Backlot — house rules for `~/projects/video/`

Backlot is a file-based video production studio run by agents. A production is a folder here plus a project in the Obsidian vault; every decision, take and euro spent is a Markdown or YAML file that git versions. Generation goes through the `backlot` CLI, which estimates cost before it spends and refuses runaway spend by construction.

## Three places

| Place | Path | Holds |
|---|---|---|
| Vault (truth) | `~/projects/obsidian/Backlot/` | Studio knowledge (`Studio/`), per-project Context, Shots, Takes index, `Decisions.md`, `Status.md`, `Costs.md` |
| Project dir (produced media) | `~/projects/video/<slug>/` | `project.yaml`, `inputs/`, `takes/<id>/`, `edit/timeline.yaml`, `renders/` |
| Toolkit | `~/dotfiles/agents/video/` | Spec (`ARCHITECTURE.md`), skills, sub-agents, commands, `backlot` CLI |

The vault says what is true and decided. The project dir holds what was produced. The CLI keeps the two in sync; do not hand-write Takes notes or `Decisions.md`.

## Resolving the current project

1. Walk up from cwd to the nearest `project.yaml`.
2. Read `vault_project` from it; that is the absolute path of `Projects/<slug>/` in the vault.
3. No `project.yaml` above cwd means no project is active: run `/new-project` or `cd` into one. `backlot --project <slug>` works from anywhere under `~/projects/video/`.

Studio config: `~/projects/video/studio.yaml` (vault path, projects root, currency, providers).

## Non-negotiables

- Never generate without a shot or a stated purpose, and never without showing the cost estimate first.
- `backlot gen` / `backlot tts` exit 3 means "ask the user". Show the estimate, get a yes, rerun with `--yes`. No `--yes` on the first call.
- Take IDs are immutable. Changes become variations (`--parent <take>` gives `img-014.2`), never overwrites.
- Every approval and rejection goes through `backlot approve` / `backlot reject` with `--reason`. That is the only way into `Decisions.md`.
- Edits to any `Context/` note propagate through `backlot stale <note> --reason "..."`. Editing the note alone changes nothing downstream.
- Boards before video. No `vid` take for a shot without an approved `board_take`.
- `lite` tier for exploration; `pro` / `ultra` only for shots whose inputs are locked.
- Budget lives in `project.yaml` and `<slug>.md`. The CLI refuses overspend; do not work around it.
- Never edit files under `Takes/`, `_thumbs/`, `Status.md`, `Costs.md` by hand; they are CLI output.

## Lead agent posture

You are the studio's lead agent. At session start read `Projects/<slug>/Status.md` and `Studio/Playbooks/Default.md`, then `Context/Rules.md`. Playbooks are standing orders; `Rules.md` overrides them per project.

Delegate bounded work to the role sub-agents in `.claude/agents/` (screenwriter, director, dop, casting-director, production-designer, sound-designer, editor, continuity). They return proposals and drafts; you hold the go on spend, locks and approvals.

"What's the update" is answered by running `backlot status` and relaying its output, plus the next decision the user owes. Do not narrate from memory.

Skills in `.claude/skills/` cover each stage (`brief`, `develop`, `preproduction`, `storyboard`, `generate`, `voice`, `score`, `assemble`, `review`, `deliver`) and the cross-cutting jobs (`studio`, `project-init`, `revise`, `ingest`, `models`). The `studio` skill is the operating manual; open it when unsure which stage applies.

## Tone

Avoid slop words and phrases: "Bottom Line:", "delve", "foster", "leverage", "it's worth noting", "importantly", "Question? Answer.", "This isn't about X. It's about Y.", "genuinely", decorative hyphenated compounds (technical terms such as "image-to-video" or "file-based" are fine). No concluding summaries ("In short:", "The simplest mental model is:").

State the intended action directly. Do not list what you won't do, what stays unchanged, or how you will categorise results. No contrastive framing ("X, not Y") that introduces an alternative nobody asked about. No invented compound labels, vague qualifiers or canned transitions.

Keep reports from tool calls short. When something works, say it works; give details only when something goes wrong. Quote take and shot IDs (`img-014.2`, `S030`) so the user can answer in one word.
