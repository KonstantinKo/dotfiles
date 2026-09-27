---
name: asset-pipeline-staged
description: Produce reference-driven 3D assets through separate shape, material-planning, texture-generation and final-review agents. Use for staged asset creation or adaptation; not for unrelated scene reconstruction or discussion-only pipeline evaluation.
---

# Staged asset pipeline

Deliver the requested asset using the explicit stages below. This is a standalone alternative workflow; do not import another pipeline's full process. Keep construction, independent judgment and material creation in their assigned agents. Do not generate an asset for a discussion-only request.

## Establish the job

Read project authority and search its asset library before substantial generation. Reuse compatible sources/materials after inspecting actual geometry, appearance and license; reused assets still pass the relevant stages. Record a short durable request in the project's asset-request folder: reference paths/hashes and identified object, use/viewing distance, necessary dimensions and inferred values, motion/modular interfaces, source/export/runtime endpoint, constraints, budget and write ownership. Resolve only consequential missing inputs; continue independent work meanwhile.

Set correction policy before work: default `n = 3` unsuccessful correction cycles, one escape intervention, and an initial total allowance of `2n` correction cycles across the whole job. Both the unsuccessful streak and reaching `n` total corrections without completion trigger escape review. These are configurable job settings, not quality claims or an immutable six-cycle ceiling. Record counters durably. A cycle is one implemented correction batch followed by its required independent review. Initial stage assessments are not correction cycles. A cycle is unsuccessful if its stage remains unaccepted; record whether it improved anyway. Count every correction cycle in the total; count consecutive unsuccessful cycles across stages, resetting that streak only on actual stage acceptance. Tool retries are recorded separately and consume real resource limits; after three failures of the same operation, diagnose or change method rather than retry indefinitely. Do not split one edit into tiny “successful” batches, or reset totals after a stage/method/agent change.

## Independent agents and execution

Use native spawn/message/follow-up and durable files; no queue daemon is required. Follow the actual project model policy for normal workers/reviewers and record model availability honestly. The escape judge must be a fresh Astra agent, as required by this workflow; if unavailable, report that dependency and ask the parent to broker it or obtain an explicit substitution. Do not silently rename another model Astra.

Reserve capacity for dependent children before dispatch. Serialize material tasks when slots are tight. If a worker cannot spawn a judge, send the parent a ready-to-dispatch brief and evidence paths for judge brokerage, then actively wait for the result using native waits; do not end the dependency by self-review or treat a notification as completion. Reclaim completed agent capacity where supported. If independent review cannot run, retain an incomplete checkpoint rather than claiming passage.

Judges receive the authoritative concept/object region, actual current render(s), necessary hard constraints and a narrow question, without the maker's desired verdict. Use fresh context without construction history for normal judgment. Shape judges and material planners are separate from the maker; the final reviewer is a NEW agent, distinct from the maker, shape judge, planner and material workers. Use a fresh final reviewer for each final-review cycle. Escape review alone receives full history.

## 1. Fix the concept

A sufficient supplied concept skips generation, including a scene image with an identified object. Retain full context plus a crop/mask when helpful; keep the original authoritative. Generate a concept only if needed, using available appropriate tools and image-generation skill instructions. Do not silently substitute a more convenient design. Record defining silhouette, proportions, construction and surface qualities, and consequential hidden-side uncertainty. Additional views clarify ambiguity without replacing a fixed target.

## 2. Create the first 3D version

Choose an established method suited to the object: manual/procedural construction, sculpting, reference-conditioned reconstruction, simulation, reuse or a combination. Choose for shape, topology and delivery needs, not a universal asset recipe. Preserve editable source. Produce an actual render under a plausible comparable camera, with readable form and simple materials; use additional views where depth, underside, deformation or fit matters. Screen-space alignment alone cannot prove 3D shape.

## 3. Obtain shape judgment; correct until OK

Spawn the independent shape judge with concept and actual render. Request **OK** or a concrete prioritized change plan: visible discrepancy, affected region, intended geometric change and expected visual effect. Judge silhouette, proportions, construction, negative spaces and defining details; include applicable joint/part relationships. Neither polish nor a high overall score excuses a major shape error. Implement the plan, render and seek independent judgment again, updating counters. Do not begin full texture work before OK. Shape acceptance is provisional evidence, not an immutable freeze: later evidence of a shape error reopens this stage and invalidates dependent appearance acceptance.

## 4. Commission a separate material plan

After shape OK, a separate agent inspects the concept and current asset and lists only needed texture/material tasks with important application notes. A solid color or shader setting may suffice; do not demand a full map set for every surface. Distinguish geometry, texture, lighting and shader effects. Cover object-specific needs such as leaf translucency, fabric weave/drape, skin or hair, glass thickness/transmission, emission, and architectural scale only where relevant. Plan motion/deformation-compatible mapping and modular seams when required.

Each task states the reference image/region, target surface, visual purpose, minimal required image or justified channel/asset set, mapping/UV strategy, real-world scale and orientation, color-space conventions, and shader/application notes. Missing physical parameters are authored assumptions, not values measured from an RGB image.

## 5. Generate materials in separate focused workers

Assign a separate subagent per needed texture/material task, serially if necessary. Pass the actual reference image and minimal focused request from the plan; avoid embellishing it with an invented material recipe. Prefer direct reference-driven images with only necessary prompt transformations. A map/channel set is justified by the planned use, not habit. A no-image material task can return explicit shader values or a reusable material asset; no generation call is required when none helps.

Each worker returns source and output paths, prompt/model/settings/seed if available, license/provenance/cost, intended surface, mapping/scale/orientation, color space per channel (typically sRGB color, linear data), channel packing and normal convention if relevant, plus application cautions. Preserve generated channels as authored approximations; RGB-derived roughness, depth or normals are not measured PBR truth. Workers write only their assigned candidate folder and publish scoped status/artifact links.

## 6. Apply, render and request NEW independent review

The asset maker applies the materials using that handoff and renders the actual asset. For a requested GLB, export, reimport the actual delivered file and render it for final review; source renders alone cannot establish delivered fidelity. Use the requested runtime for runtime appearance claims. Test relevant scale/pivots, part motion or assembly, dependencies and export validity separately; character deformation, modular fit and transparent/emissive export behavior need the corresponding actual evidence when in scope.

The new reviewer inspects concept and rendered evidence and returns:

- **Fidelity rating** and **visual appeal rating**, independently anchored to the concept: 100% means as good, below means the concept is better, above means the render is better. These are subjective anchored ratings, not measured percent similarity. Fidelity rewards preserving the target's identity; added beauty cannot compensate for a wrong object. Give evidence, uncertainty/confidence and concept strengths for each rating.
- **Functional/export validity:** pass, fail or unverified against the requested endpoint; no numerical averaging with appearance.
- Concrete prioritized improvements, major defects and major quick wins: changes likely to materially improve fidelity/appeal with modest effort using established methods. Identify geometry errors that require reopening shape review.

Compare the asset itself: silhouette, construction, material identity and detail hierarchy. Do not reward a backdrop, dramatic lighting or framing that hides defects. Use clear alternate views if presentation prevents judgment. Insufficient evidence means unverified, not a confident pass.

## 7. Finish or invoke bounded escape

Aim for both subjective appearance ratings **at least 80%**, no major defects, no remaining major quick wins, sufficient review confidence, and valid requested delivery. No averaging away a failed dimension. Correct, render and repeat the appropriate independent stage(s); keep reference and comparison settings stable enough to attribute changes.

At `n` consecutive unsuccessful cycles, or when the total reaches `n` without completion, invoke the fresh Astra escape judge before more corrections. Give original concept, candidate/render history, reviews, attempted methods, counters and remaining resources. It chooses an intelligently changed method, a specifically bounded continuation, or quit with retained failure, with reasons and predicted evidence. It may spend the remaining allowance or explicitly revise the total cap once in a bounded plan when evidenced progress justifies more work within authorized resources. Record old/new cap, additional cycles, changed method, expected gain and stop condition. One intervention is the default; it cannot reset counters, increase authorized spending or grant itself endless extensions. Stop incomplete when that explicit allowance or resource boundary is exhausted without acceptance. Further scope requires a new explicit requester/user continuation budget, retaining the history and lifetime totals.

## Durable return and resource care

Keep a compact result/status beside the request: immutable revision, source/export paths and hashes, actual previews, review decisions/counters, dimensions/axes/pivot and interfaces, material handoffs, provenance, costs/time/retained bytes, limitations and next action. Use statuses such as working, ready for requester review, accepted by requester, or incomplete with retained failure; worker review is not user acceptance. A requester can continue independent scene work with a stable proxy while the worker runs. The requesting agent owns integration and shared catalog/commit coordination unless explicitly delegated; the worker publishes its own scoped evidence and promptly signals completion or blockage.

Check exact paid endpoint pricing before submission and honor current session/project caps, including pending jobs. Persist job IDs and reconcile uncertain jobs before resubmission. Preserve retained source, requested exports, necessary inputs/settings and compact evidence; prune only owned reproducible intermediates after verification. Register reusable results with honest review state through the catalog owner; known failed revisions must not remain recommended as accepted. Never replace a scene proxy automatically outside assigned integration scope.
