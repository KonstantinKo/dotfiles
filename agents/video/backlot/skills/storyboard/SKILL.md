---
name: storyboard
description: Storyboard a Backlot project: create shot notes S010.., write a board prompt per shot from Visual Language, Cast and Location notes, generate board images and approve one per shot. Use for "storyboard this", "make the boards", "board S030", "shot list", or when Status.md shows stage boards.
---

# Storyboard

## Purpose
Use this workflow for scenes that declare `board`. Give each such generated shot an approved still (`board_take`) before video generation.

## Inputs
- `Projects/<slug>/Brief.md` (goal, audience and message), `Projects/<slug>/Script.md` (beats, shot candidates)
- `Context/Visual Language.md`, `Context/Cast/*.md`, `Context/Locations/*.md`, `Context/Props/*.md` (locked, with `locked_take`)
- `Context/Rules.md`, `Studio/Playbooks/Default.md`, `Studio/Workflows/Storyboarding.md`
- `backlot models --kind image`; `references/prompt-craft.md` in this skill
- `../studio/references/production-checks.md` for active reference roles and shot-card fields

## Steps
1. Shot list. Resolve semantic scene/beat names to stable shot IDs. Spawn `director` with the Script. For each shot, record the relevant prior/current/next beat, emotional intent, visible action and start/end state, scene geography, actor facing/gaze/travel, and camera side/movement separately. Write one `Shots/S###.md` per shot from `_templates/` with frontmatter: `shot, status: planned, duration_s, cast, location, props, depends_on` (the Context note names it draws on).
2. References and prompts. List active references by purpose and submission order, with what each establishes and its limits. Spawn `dop` with the shot notes and relevant Context notes. Per shot it returns a board prompt built as in `references/prompt-craft.md`: subject from Cast note, setting from Location note, action, camera and lens, lighting, style fragments from Visual Language, negatives. Store the card and prompt in the shot note.
3. Route and estimate. Confirm the exact image provider/model/version/operation, effective controls and any promotion’s route scope before pricing. Honor the selected output resolution; choose a pilot only for a material unresolved question and at enough fidelity to answer it. Per shot, lite tier unless `Rules.md` says otherwise:
   `backlot gen img --model <id> --prompt "<prompt>" --shot S010 --n 2 --image <locked_take of the lead cast member if the model takes a reference> --depends-on "Cast/Mia,Locations/Kitchen,Visual Language"`
   On exit 3, show the exact ordered inputs, effective settings, promotion, quote and remaining budget, then follow [Decision and spend](../studio/references/decision-and-spend.md). Run the quoted paid call only with its returned authorization ID; `--yes` alone is not approval. Free/local calls need no spend authorization.
4. Self-check and present first results: open each thumbnail at useful size and compare against the shot card, active reference roles, Cast and Location notes. Separate technical validity from action, framing, context and story intent. Present take IDs and material differences before proposing another paid call.
5. The user picks. Record that exact message and reference with `backlot approve <take> --reason "..." --source-message "<approval text>" --source-ref "<message reference>" --scope "approved storyboard use"`; see [Decision and spend](../studio/references/decision-and-spend.md). The CLI sets `board_take` and `status: approved` on the shot (the shot became `boarded` when its first board take was saved).
6. Misses: repair a selected take with `--parent <take>` and a narrow prompt delta, preserving effective controls and nearby story context. Every paid retry needs a new exact quote and authorization; a previous submission consumed its authorization. Record causes only when evidence supplies them.
7. `backlot status`. All shots at `approved`: set `status: shots`.

## Outputs
- `Shots/S###.md` per shot with `board_take`
- img takes with `depends_on`, decisions with reasons

## Gate
Every scene that declares `board` has an approved exact `board_take`; inspect `backlot stage --json` for remaining blockers.

## Example phrases
- "storyboard the whole script"
- "board S040 again, wider"
- "show me the shot list"
