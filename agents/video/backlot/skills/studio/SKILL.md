---
name: studio
description: Operating manual for running a Backlot video production as lead agent. Use when starting a session in a project folder, when asked "where are we", "what's next", "what's the update", "how does this studio work", which stage or gate applies, or which role sub-agent to spawn for a task.
---

# Studio — operating manual

## Purpose
Tell the lead agent how a production moves from idea to delivery, what each gate needs, who does what, and how to report.

## Inputs
- `Projects/<slug>/Status.md`, `<slug>.md` frontmatter (`status`, `budget_eur`, `spent_eur`)
- Current handoff and delivery/version pointer, plus relevant archived conversation exports when recent approvals or state are not in the active thread. Search project-local sources before asking the user to repeat a decision; note missing coverage.
- `Studio/Playbooks/Default.md`, then `Projects/<slug>/Context/Rules.md` (project overrides win)
- `Studio/Workflows/*.md` when a stage names one
- `Decisions.md` (newest on top) for the last decisions taken

## Declared workflow and gates

`project.yaml workflow` names the scenes, their requirements, and the deliverables. The base path needs an agreed Brief, one or more named scenes, exact source coverage, a verified deliverable and an approval for that output version and scope. Add boards, identity/world locks, spatial or Blender guides, voice, captions, score, exact graphics, typed review, or remote share only when the project needs them. [Workflow requirements](references/workflow-gates.md) is generated from the evaluator's registry.

`backlot stage --json` reports blockers per scene and deliverable without writing. `backlot stage --advance` updates the home note's summary to delivered only after the declared checks pass. A legacy project may still use the old stage path until its workflow is declared. A current version is established by its deliverable record and matching user decision, rather than by the summary stage. Record original user approval text, source reference and timestamp when available; mark agent reviews and unverified legacy text with their own source kind. See [Decision and spend](references/decision-and-spend.md).

## Running a session
1. Resolve the project (cwd → `project.yaml` → `vault_project`). If none, offer `/new-project`.
2. Read the current handoff/delivery pointer, `Status.md`, `Costs.md`, Playbook, and `Rules.md`; reconcile them with the relevant `Decisions.md` entries and archived approvals before asking for a repeated decision. Note source coverage and stale counts.
3. State the current stage and the one decision or artefact the gate needs. Ask, or proceed if the answer is already supported by current records or a scoped archived approval.
4. Work the stage with its skill. For paid calls, quote first and use [Decision and spend](references/decision-and-spend.md); exit 3 requires recorded authorization for the exact call. Free/local calls need no authorization.
5. Close the session with read-only `backlot status` and `backlot delivery`; use `backlot cost` when spend changed. Refresh the derived notes only when needed. Commit the project dir and the vault.

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
Run `backlot status`, `backlot delivery`, and `backlot cost` for computed read-only inspection; add one line naming the next decision the user owes. `--refresh` rewrites the respective derived note. Keep the hand-written `Delivery.md` narrative untouched.

## Playbooks and Workflows
Playbook rules apply to the work actually declared: quote each paid call, present options for an unlocked selected element, use lite for exploration, keep variations immutable, and record reasons on decisions. Boards precede generated video when the scene declares `board`. A Workflow note is a scripted job to use when that activity is selected, not a mandatory phase for every film.

## Escalation
The CLI enforces the money gates from `project.yaml` (`confirm_over_eur`, `max_call_eur`, `escalate_pct`, defaults in `studio.yaml`), so when it exits 3 or refuses, show the quote and follow [Decision and spend](references/decision-and-spend.md). On top of that, stop and ask when: a Context edit would stale more than a third of shots; a Playbook rule conflicts with `Rules.md`; a provider fails twice in a row; a sub-agent proposes changing a locked element. Log each take decision with its explicit source and reason.

## Example phrases
- "what's the update on the launch spot"
- "where are we, what do you need from me"
- "how does this studio work"
