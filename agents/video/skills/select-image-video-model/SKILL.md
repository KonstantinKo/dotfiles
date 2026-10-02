---
name: select-image-video-model
description: Use when deciding which image or video model to use.
---

# Select an image or video model

Select a fal.ai or Higgsfield model for the brief using the sourced decision table. Respect explicit model and project choices. Generation runs through the applicable provider or production skill.

## Read only the relevant evidence

- Start with the relevant section of [the decision table](references/model-decision-table.md): images, video, or specialist tools. Its price and evidence legends apply to every row.
- Read [image](references/image-evidence.md), [video](references/video-evidence.md), [specialist](references/specialist-evidence.md), [additional model](references/additional-evidence.md), or [creator test](references/youtube-evidence.md) evidence only for shortlisted models or disputed claims. Search for the exact version instead of loading every reference.
- Snapshot: **2026-10-01**. Verify current availability, inputs, restrictions, and price when they change the choice. A listed endpoint does not prove that the account/reference will be accepted.

## Choose by the constraint that can cause failure

Identify required output, references, continuity, motion/edit, text accuracy, sound, duration, resolution, and budget. Ask only when a missing constraint materially changes selection.

Eliminate incompatible routes. Distinguish text-to-video, start/end frames, identity references, motion transfer, video editing, and lip sync; raster versus actual SVG; generated audio versus a recording that must stay synchronized. The same model can expose different controls and moderation across providers.

Weigh supported task fit against price and likely retries. Recommend one model and, when helpful, one alternative with the tradeoff. Anecdotes do not establish retry rates.

## Interpret the evidence

Providers establish advertised capabilities and contracts. Independent tests/forums expose failure patterns; isolated reports remain provisional. Flag reseller/affiliate incentives and repeated crossposts. For creator videos, record visible prompts/settings, version, sponsorship, and whether outputs are selected or first attempts; distinguish transcript claims from inspected results.

Match evidence to the exact version, tier, operation, and route. Older releases and consumer apps do not establish newer API performance. Arena preference does not prove identity, physics, labels, or camera accuracy on this shot. Keep unsupported advantages and prices unknown.

**Not useful for** includes incompatibilities and comparative weaknesses; read the evidence before treating a weakness as absolute.

## Confirm the route

Higgsfield: read-only `higgsfield model list --json` and `model get <job_type> --json`. `nano_banana_flash` means Nano Banana 2; `nano_banana_pro` means Pro; legacy `nano_banana_2` resolves to Pro. Some Cinema Studio workflows require explicit lookup despite absence from the list.

fal: `list_models` with `search`, then exact endpoint schema/billing text. Discovery caps at 100; search missing families separately. Generic `units`, `videos`, or processed megapixels require a billing formula.

Use the matching prompt/generation skill after selection. Product photoshoot, marketplace cards, thumbnails, explainers, and Cinema/Marketing Studio add workflows around models; verify the underlying route and controls.

Selection/research does not authorize spending. Follow the workspace's paid-call rule: exact inputs, estimate, current balance, and explicit approval for that call.

## Maintain the reference

Update the row and evidence together when findings change. Record URL, source/observation date, version, operation, provenance, and limits. Preserve task-specific evidence.
