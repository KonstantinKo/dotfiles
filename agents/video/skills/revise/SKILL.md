---
name: revise
description: Apply a natural-language change to a Backlot project after locks: work out which Context notes change, edit them, mark dependants stale with backlot stale, plan regeneration with a cost estimate, and ask. Use for "make Mia blonde", "change the location to a rooftop", "the script needs a new line in beat 3", "what would it cost to change X".
---

# Revise

## Purpose
Turn a change request into edited Context, a known blast radius, and a priced regeneration plan the user approves before anything is spent.

## Inputs
- `Projects/<slug>/Context/**` (`depends_on`, `locked`, `locked_take`)
- `Shots/S###.md` (`depends_on`, `board_take`, `video_take`, `vo_take`), `Script.md`
- `backlot takes --stale` after staling; `backlot gen --dry-run` for costs
- `Studio/Playbooks/Default.md`, `Context/Rules.md`

## Steps
1. Restate the change in one line and map it to Context notes. Wording cues: a person means `Cast/<Name>`; a place, `Locations/<Name>`; an object, `Props/<Name>`; look or mood, `Visual Language`; facts, `Knowledge`; a line or beat, `Script.md`; length or aspect, `<slug>.md` and `Rules.md`.
2. Read each affected note and its `depends_on`. Notes that depend on the changed note are affected too (a Cast note that borrows palette from Visual Language).
3. Edit the notes. Locked notes: set `locked: false`, clear `locked_take`, keep the old value in a `## History` line with the date and reason.
4. Propagate: `backlot stale "<Note name>" --reason "<change>"` per edited note. Script changes: stale each shot whose beat changed, via the Context notes it depends on, or by marking the shot `status: stale` in its frontmatter when no note captures it.
5. Blast radius: `backlot takes --stale`. Count shots, boards, videos, VO lines. If more than a third of shots are stale, say so before planning.
6. Plan: for each stale item, the step that redoes it (re-lock in `preproduction`, board in `storyboard`, video in `generate`, VO in `voice`) and its `--dry-run` estimate. Present as a table with a total and the remaining budget. Cheaper paths first: a variation with `--parent` when the change is small; a fresh option round when the element is unlocked.
7. Ask. On yes, run the plan stage by stage through the normal skills; the estimate flow still applies per call. On no, leave the stale marks; `backlot status` shows them until resolved.

## Outputs
- Edited Context notes with `## History`
- Stale marks on takes and shots, reason in `Decisions.md`
- The regeneration plan in chat (and in `Review.md` when the change came from a review)

## Gate
User approves the plan and its total. Nothing regenerates before that.

## Example phrases
- "make Mia blonde"
- "move the whole thing to a rooftop at dusk"
- "what would it cost to change the ending"
