---
name: generate
description: Generate requested video takes for a Backlot project from their declared sources, with model routing, variations, review and cost discipline. Use for "generate the shots", "animate S020", "make a variation of vid-009", or "which model for this".
---

# Generate

## Purpose
Turn each requested shot into an approved video take using its declared source evidence.

## Inputs
- `Shots/S###.md` (`board_take`, `duration_s`, `depends_on`, `## Board prompt`)
- `Takes/<board_take>.md` for the reference image and its prompt
- `Context/Rules.md` (default models per kind, tier policy), `Studio/Playbooks/Default.md`
- `Studio/Models/*.md` via `backlot models --kind video`; `references/model-routing.md` in this skill
- `storyboard/references/prompt-craft.md` for the video prompt shape
- `../studio/references/production-checks.md` for shot intent, effective routes, review, and repair

## Steps
1. Preconditions per shot: check `project.yaml workflow`. A scene declaring `board` needs an approved `board_take`; a scene using supplied footage or another guide uses its declared exact source. Relevant `depends_on` locks must be current. Read the story/action card and ordered reference roles; resolve semantic names to exact take IDs.
2. Route. Pick model by `references/model-routing.md`: kind `video`, `inputs` includes `image`, `max_duration_s` >= `duration_s`, resolution matches `<slug>.md`, tier by lock state (lite while exploring motion, pro or ultra for the final pass on locked shots). Honor an explicit resolution choice. Choose a pilot only for a material unresolved question and at enough fidelity to answer it. Confirm the exact provider, model/version and operation, effective controls, and promotion scope before estimating. Note strengths in the model note decide ties.
3. Prompt. Spawn `dop` for the motion prompt when the shot note has none; store it under `## Video prompt`. Preserve actor action/facing/gaze/travel separately from camera side/movement; include relevant beat and end-state context.
4. Estimate. `backlot gen vid --model <id> --image <board_take> --prompt "<video prompt>" --shot S020 --param duration=<s> --depends-on "<same list as the shot>" --dry-run --json > /tmp/backlot-quote.json`. Batch estimates for the stage into one table: shot, provider/model/version/operation, ordered references, effective settings, seconds, applicable promotion, EUR.
   Pass `--param` values in the model's own format (`duration=10` for Kling, `duration=8s` for Veo); only add parameters the model note's Arguments section lists.
5. Ask. Show each exact call, estimate and observed provider balance. For each explicitly approved paid call, follow [Decision and spend](../studio/references/decision-and-spend.md) to record the approval source, native balance and expiry, then repeat the quoted command with `--yes --authorization <returned ID>` and without `--dry-run`. A batch needs one authorization per paid call in request order. Prompt feedback or approval for another call does not authorize this one.
6. Review, then present the first-pass results before proposing another paid call. Watch full playback where possible; sample risky middle regions and cut context if needed. State whether review covered full playback or only samples; a decode or endpoint check does not establish full visual review. Check technical validity separately from shot action, story continuity, identity, wardrobe, and subjective user judgment. Reject clear failures with evidence and a reason. Record unexplained failures as `failed; cause unavailable`.
7. Variations on request: `--parent <take>` with a narrow prompt delta or param change. Start from the parent manifest; keep proven inputs and controls, inspect nearby semantic content, and change only what fixes the defect. A paid retry needs a new exact quote and authorization; an accepted attempt consumed its prior authorization. Preserve accepted limitations unless the user reopens them.
8. `backlot approve <take> --reason "..." --source-message "<approval text>" --source-ref "<message ID>" --scope "<approved use>"`; the CLI sets `video_take`. The shot moved to `status: generated` when the video take was saved. When every shot has an approved `video_take`, set `status: voice`.

## Cost discipline
- Never generate longer than `duration_s` plus one second of handle.
- A shot that fails twice on one model moves to the next candidate once, only when the existing approval covers that route and retry. Otherwise present the result and request fresh approval. Report a third failure with the cost so far.
- Upscale (`up`) only at deliver, and only for approved takes.

## Outputs
- vid takes with `depends_on`, `parent` on variations
- `Shots/S###.md` with `video_take`, `## Video prompt`
- Decisions with reasons

## Gate
Every scene declaring generated video has an exact selected output or a recorded blocker in `backlot stage --json`.

## Example phrases
- "generate all the shots from the boards"
- "animate S020 with a slow push in"
- "give me a variation of vid-009 with less camera movement"
