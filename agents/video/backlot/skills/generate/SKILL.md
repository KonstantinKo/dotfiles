---
name: generate
description: Generate video takes for a Backlot project from approved boards: image-to-video, model routing by tier and model strengths, variations, self-review, cost discipline. Use for "generate the shots", "animate S020", "make a variation of vid-009", "which model for this", or when Status.md shows stage shots.
---

# Generate

## Purpose
Turn each approved board into an approved `video_take` at the lowest cost that meets the shot.

## Inputs
- `Shots/S###.md` (`board_take`, `duration_s`, `depends_on`, `## Board prompt`)
- `Takes/<board_take>.md` for the reference image and its prompt
- `Context/Rules.md` (default models per kind, tier policy), `Studio/Playbooks/Default.md`
- `Studio/Models/*.md` via `backlot models --kind video`; `references/model-routing.md` in this skill
- `storyboard/references/prompt-craft.md` for the video prompt shape

## Steps
1. Preconditions per shot: `status: approved` (board approved), `board_take` set, `depends_on` notes all `locked: true`. A stale shot goes back to `storyboard`.
2. Route. Pick model by `references/model-routing.md`: kind `video`, `inputs` includes `image`, `max_duration_s` >= `duration_s`, resolution matches `<slug>.md`, tier by lock state (lite while exploring motion, pro or ultra for the final pass on locked shots). Note strengths in the model note decide ties.
3. Prompt. Spawn `dop` for the motion prompt when the shot note has none; store it under `## Video prompt`.
4. Estimate. `backlot gen vid --model <id> --image <board_take> --prompt "<video prompt>" --shot S020 --param duration=<s> --depends-on "<same list as the shot>" --dry-run`. Batch estimates for the stage into one table: shot, model, seconds, EUR.
   Pass `--param` values in the model's own format (`duration=10` for Kling, `duration=8s` for Veo); only add parameters the model note's Arguments section lists.
5. Ask. Show the table and the remaining budget. On yes, run each with `--yes`. One take per locked shot; two only when the motion is uncertain.
6. Self-review before presenting: watch each take (extract three frames with ffmpeg if the harness cannot play video), check against the board and the Cast note: identity held, wardrobe unchanged, motion plausible, no morphing, duration right. Reject clear failures with a reason. Present the rest by ID with one line each.
7. Variations on request: `--parent <take>` with a prompt delta or a param change. Same model unless the model is the problem.
8. `backlot approve <take> --reason "..."`; the CLI sets `video_take`. The shot moved to `status: generated` when the video take was saved. When every shot has an approved `video_take`, set `status: voice`.

## Cost discipline
- Never generate longer than `duration_s` plus one second of handle.
- A shot that fails twice on one model moves to the next candidate, once. A third failure is reported to the user with the cost so far.
- Upscale (`up`) only at deliver, and only for approved takes.

## Outputs
- vid takes with `depends_on`, `parent` on variations
- `Shots/S###.md` with `video_take`, `## Video prompt`
- Decisions with reasons

## Gate
Every shot has an approved `video_take`.

## Example phrases
- "generate all the shots from the boards"
- "animate S020 with a slow push in"
- "give me a variation of vid-009 with less camera movement"
