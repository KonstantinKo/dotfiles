---
name: storyboard
description: Storyboard a Backlot project: create shot notes S010.., write a board prompt per shot from Visual Language, Cast and Location notes, generate board images and approve one per shot. Use for "storyboard this", "make the boards", "board S030", "shot list", or when Status.md shows stage boards.
---

# Storyboard

## Purpose
Give every shot an approved still (`board_take`) before any video is spent. Boards are cheap, video is not.

## Inputs
- `Projects/<slug>/Script.md` (beats, shot candidates)
- `Context/Visual Language.md`, `Context/Cast/*.md`, `Context/Locations/*.md`, `Context/Props/*.md` (locked, with `locked_take`)
- `Context/Rules.md`, `Studio/Playbooks/Default.md`, `Studio/Workflows/Storyboarding.md`
- `backlot models --kind image`; `references/prompt-craft.md` in this skill

## Steps
1. Shot list. Spawn `director` with the Script. It returns shots numbered S010, S020, ... (gaps for inserts), each with beat, intent, duration, cast, location, props, camera and movement. Write one `Shots/S###.md` per shot from `_templates/` with frontmatter: `shot, status: planned, duration_s, cast, location, props, depends_on` (the Context note names it draws on).
2. Prompts. Spawn `dop` with the shot notes and the Context notes. Per shot it returns a board prompt built as in `references/prompt-craft.md`: subject from Cast note, setting from Location note, action, camera and lens, lighting, style fragments from Visual Language, negatives. Store the prompt in the shot note under `## Board prompt`.
3. Generate. Per shot, lite tier unless `Rules.md` says otherwise:
   `backlot gen img --model <id> --prompt "<prompt>" --shot S010 --n 2 --image <locked_take of the lead cast member if the model takes a reference> --depends-on "Cast/Mia,Locations/Kitchen,Visual Language"`
   Exit 3: show estimate per shot or batched for the stage, ask once, rerun each with `--yes`.
4. Self-check before presenting: open each thumbnail, compare against the Cast and Location notes. Drop obvious misses with `backlot reject --reason`.
5. Present per shot: take IDs, one line each on what differs. The user picks. `backlot approve <take> --reason "..."`; the CLI sets `board_take` and `status: approved` on the shot (the shot became `boarded` when its first board take was saved).
6. Misses: variations with `--parent <take>` and a prompt delta, never a fresh unrelated prompt unless the shot intent changed.
7. `backlot status`. All shots at `approved`: set `status: shots`.

## Outputs
- `Shots/S###.md` per shot with `board_take`
- img takes with `depends_on`, decisions with reasons

## Gate
Every shot has an approved `board_take`.

## Example phrases
- "storyboard the whole script"
- "board S040 again, wider"
- "show me the shot list"
