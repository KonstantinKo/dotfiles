---
name: develop
description: Develop a Backlot project from Brief to locked Script: treatment, beats, VO lines, durations, shot candidates. Use for "write the treatment", "script this", "break it into beats", "lock the script", or when Status.md shows stage develop.
---

# Develop

## Purpose
Turn the Brief into a Treatment, then a Script with timed beats, VO lines and shot candidates, and lock it.

## Inputs
- `Projects/<slug>/Brief.md`
- `Context/Knowledge.md`, `Context/Inspiration.md`, `Context/World.md` if present
- `Context/Rules.md`, `Studio/Playbooks/Default.md`
- `Studio/Workflows/Reference Research.md` when references are thin

## Steps
1. Treatment. Spawn `screenwriter` with the Brief and Knowledge. Ask for two treatment directions, each under 200 words: premise, arc, ending, why it fits the audience. Present both; the user picks or merges. Write `Treatment.md`.
2. Script. Spawn `screenwriter` again with the chosen treatment. Deliver `Script.md` as a beat table:

   | Beat | Duration (s) | Action | VO | On-screen text | Shot candidates |
   |---|---|---|---|---|---|

   Durations must sum to the Brief length within 10%. VO lines are speakable at 2.5 words per second; check each line's word count against its beat duration.
3. Spawn `director` to review pacing and propose shot candidates per beat (one to three per beat, named by intent, no prompts yet).
4. Read the script back to the user as beats with durations. Take changes in place; keep the table shape.
5. On the user's yes, write `locked: true` and `locked_at` into `Script.md` frontmatter and set `status: preproduction` in `<slug>.md`.

## Outputs
- `Projects/<slug>/Treatment.md`
- `Projects/<slug>/Script.md` (beat table, `locked` frontmatter)
- Cast, location and prop names mentioned in the script listed at the bottom of `Script.md` as the seed for `preproduction`

## Gate
`Script.md` locked by the user. After lock, script edits go through `revise`, which stales affected shots.

## Example phrases
- "write the treatment, two directions"
- "script it in six beats, 45 seconds total"
- "lock the script"
