---
name: studio
description: Operating manual for running a Backlot video production as lead agent. Use when starting a session in a project folder, when asked "where are we", "what's next", "what's the update", "how does this studio work", which stage or gate applies, or which role sub-agent to spawn for a task.
---

# Studio — operating manual

## Purpose
Tell the lead agent how a production moves from idea to delivery, what each gate needs, who does what, and how to report.

## Inputs
- `Projects/<slug>/Status.md`, `<slug>.md` frontmatter (`status`, `budget_eur`, `spent_eur`)
- `Studio/Playbooks/Default.md`, then `Projects/<slug>/Context/Rules.md` (project overrides win)
- `Studio/Workflows/*.md` when a stage names one
- `Decisions.md` (newest on top) for the last decisions taken

## Stages and gates

| Stage (`status`) | Skill | Gate |
|---|---|---|
| brief | `brief` | `Brief.md` agreed by the user |
| develop | `develop` | `Script.md` locked: beats, VO lines, durations |
| preproduction | `preproduction` | four locks (cast, locations/props, visual language, format & deliverables) plus a voice per cast member |
| boards | `storyboard` | every shot has an approved `board_take` |
| shots | `generate` | every shot has an approved `video_take` |
| voice / score | `voice`, `score` | vo takes approved; music and sfx placed in the timeline |
| assemble | `assemble` | `edit/timeline.yaml` renders a draft |
| review | `review` | continuity and brief compliance pass, or a flag list the user has seen |
| deliver | `deliver` | exports in `renders/`, `Status.md` says delivered |

A gate is passed when the artefact exists in the vault and the user said yes in chat. Record the yes through `backlot approve` (takes) or a line in `Decisions.md` written by `backlot approve --lock` (Context locks). Stages advance only through `backlot stage --advance` (it checks the gate and writes `status:` in `<slug>.md`); never edit the home note's `status` by hand.

## Running a session
1. Resolve the project (cwd → `project.yaml` → `vault_project`). If none, offer `/new-project`.
2. `backlot status`. Read Playbook and `Rules.md`. Note stale counts and remaining budget.
3. State the current stage and the one decision or artefact the gate needs. Ask, or proceed if the answer is already in `Decisions.md`.
4. Work the stage with its skill. Spend goes through `backlot gen`; exit 3 means show the estimate and ask.
5. Close the session with `backlot status` and, if takes were produced, `backlot cost`. Commit the project dir and the vault.

## Role crew
Spawn a sub-agent for bounded work with a written brief that names the vault notes to read and the output expected. Sub-agents never run backlot spend commands (`gen`, `tts`, `captions`, `batch`, `recover`), never approve, never edit `Decisions.md`; only dop, editor and continuity have Bash at all.

| Sub-agent | Spawn when | Returns |
|---|---|---|
| screenwriter | treatment, script, VO lines, beat timing | draft `Treatment.md` / `Script.md` sections |
| director | shot list, blocking, per-shot intent, pacing notes | shot notes text, ordering |
| dop | image/video prompts, camera, lens, lighting, model choice per shot | prompt text and params per shot |
| casting-director | cast candidates, look sheets, voice matching | `Context/Cast/<Name>.md` drafts, option prompts |
| production-designer | locations, props, visual language, palette | `Context/Locations|Props/*.md`, `Visual Language.md` drafts |
| sound-designer | music brief, sfx list, ducking plan, tts params | audio plan, timeline audio rows |
| editor | timeline authoring, cut alternatives, pacing | `edit/timeline.yaml` variants |
| continuity | compare takes against Context, flag drift | flag list with take IDs and evidence |

## "What's the update"
Run `backlot status`, relay it verbatim or trimmed, then add one line: the next decision the user owes (which take to pick, which lock to confirm, whether to spend X on Y). Nothing from memory.

## Playbooks and Workflows
Playbook rules are defaults for every action: ask before generating, 2–4 options per unlocked element and 1 for locked, lite for exploration, boards before video, variations never overwrites, reasons on every decision. A Workflow note is a scripted multi-step job (Casting, Reference Research, Production Design, Storyboarding, Ad Variations, Localisation, Campaign Transfer, Reframing). When a stage names a Workflow, follow its steps in order and report which step you are on.

## Escalation
The CLI enforces the money gates from `project.yaml` (`confirm_over_eur`, `max_call_eur`, `escalate_pct`, defaults in `studio.yaml`), so when it exits 3 or refuses, show the user its message and ask. On top of that, stop and ask when: a Context edit would stale more than a third of shots; a Playbook rule conflicts with `Rules.md`; a provider fails twice in a row; a sub-agent proposes changing a locked element. Otherwise decide, and log the reason in the approve/reject call.

## Example phrases
- "what's the update on the launch spot"
- "where are we, what do you need from me"
- "how does this studio work"
