---
name: deliver
description: Verify and record the named final output versions of a Backlot project, using a native, external or custom assembly. Use for "export the final", "deliver", "make the shorts version", "render for youtube", or "localise to German".
---

# Deliver

## Purpose
Produce and verify the deliverables declared in `project.yaml workflow`, then preserve their exact sources and scoped approvals.

## Inputs
- The agreed Brief and `project.yaml workflow` named scenes and deliverables
- Registered M2 media artifacts and `edit/assemblies/<id>.yaml` source maps
- User decisions in `Records/decisions/`; optional typed reviews in `Records/reviews/`
- [Workflow requirements](../studio/references/workflow-gates.md) and [Finishing checks](../studio/references/finishing-checks.md)

## Steps
1. Resolve the current named deliverables from the Brief and `project.yaml`. Clarify only an actual conflict or omission. Select the native Backlot renderer, an external editor, or a custom recipe based on the work. A new aspect, language, score or caption variant gets its own named output.
2. Produce requested versions. Use `backlot render` for a native timeline; use the selected external/custom assembly recipe for another route. Upscale, reframe, localise or add sound only when requested. Paid calls follow [Decision and spend](../studio/references/decision-and-spend.md).
3. Register exact source media and final output with `backlot register`. Record the ordered source/output frame map, output artifact, actual probe, and hashed recipe using `backlot assembly <spec.json>`. `backlot deliverable <spec.json>` binds the named output to that assembly, its SHA-256 and the required approval scope. A different version gets a different record ID.
4. Check the rendered media itself. Inspect frame count, format, cuts, exact graphics when declared, and audio/caption timing when present. Keep technical decode, visual review, listening, user acceptance and unsupported checks distinct. A rejected raw take remains rejected when an accepted local derivative uses selected material from it.
5. Record the user's exact decision on the output hash with `backlot decision approve picture|scored|share <deliverable-id> --version <sha256> --scope <declared-scope> --source-kind user --source-message <original-text> --source-ref <message-ref>`. Include `--source-at` when the original timestamp is known. For an archived approved final, use `backlot historical-import <spec.json>` to bind the original approval JSON, user decision, registered artifact and assembly recipe once; reference its ID as `historical_acceptance_id` in the deliverable. A share request approves sharing only; it does not replace an earlier picture-master decision.
6. Run read-only `backlot delivery --json` and `backlot stage --json`. Resolve actual blockers. Once all declared checks pass, `backlot stage --advance`, then refresh the derived `Deliverables.md`, `Status.md`, `Costs.md` and `Handoff.md` as needed with `--refresh`. Preserve the hand-written `Delivery.md` narrative.
7. Archive requested media with `backlot archive create`, inspect with `backlot archive check`, and bundle when needed. A checked local bundle is not proof of an off-machine backup. Commit project and vault records at a useful checkpoint.

## Gate
Every required or scene-referenced named deliverable has existing output bytes, a matching registered hash/probe, complete exact source coverage, and a scoped user approval of that output version. Every declared scene has a verified picture range. Each additional declared scene requirement has its own evidence or an imported exact historical acceptance.
