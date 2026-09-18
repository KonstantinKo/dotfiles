---
name: asset-pipeline
description: Fulfill a requested 3D game asset from scene specifications. Use for asset production requests and asset-pipeline design; use concept-to-reality alone for an existing reconstruction's visual correction.
---

# Asset pipeline

Turn a scene need into a reviewed asset with an explicit delivery contract. This workflow supports native sub-agent handoff when available and authorized. It supplies decisions and durable handoff conventions; it does not require a separate queue service. Respect discussion-only and source-only scope. Do not generate assets merely because the user asks to evaluate the pipeline.

Treat `source`, `preview_runtime`, and `production_runtime` as different endpoints. A beauty-render source is not a game-ready asset. `preview_runtime` is a bounded asset that can be placed in the current scene for composition and gameplay evaluation, with measured geometry, materials, texture residency assumptions, pivots and basic collision. `production_runtime` additionally meets the scene's final LOD, shader, collision, memory, instancing and platform checks. Preserve the editable high-detail source separately when deriving either runtime endpoint.

## Intake and route

Read the project's current design authority and existing asset catalog. Capture the requested use, references and their authority, dimensions/axes/pivot, viewing distance, visible sides, motion or modular interfaces, deliverable endpoint, and caller's actual cost/time/storage constraints. Distinguish hard constraints from preferences and inferred dimensions. For runtime work also capture target hardware/engine, expected simultaneous instances, performance/material/texture budgets and collision needs. Do not substitute a high-detail source for a requested runtime asset.

Preserve the requested visual standard when translating the user need into a worker brief. Source-only describes delivery/integration scope, not a lower artistic standard. Do not invent an ordinary-dressing tier, farther viewing distance or austere per-asset budget that removes defining reference features. Agent-imposed targets are planning choices; revise them before lowering quality. If an actual user constraint prevents the result, report it as incomplete.

Use sensible documented assumptions for ordinary dressing. Resolve a missing critical mating dimension or interaction contract before dependent construction; continue independent material/reuse work. Exact generated text, markings and physical labels are not trustworthy specifications.

Check existing sources, modules and materials first. Bound external research so routine sourcing does not consume the job. Verify the candidate's actual geometry, material bindings and license before accepting it. Preserve third-party provenance. A source thumbnail or a claimed PBR label is insufficient.

Resolve visual inputs using [reference intake](references/reference-inputs.md) when images are supplied or a comparison test is requested. A sufficient supplied concept skips initial concept generation. A scene image can identify one asset by description, region or mask; keep its context and authority when deriving necessary clarification. A new generated image does not silently replace the target. For a fixed-reference test, use the same image bytes, target region and brief across runs.

Choose a route using [route guidance](references/routes.md). Derive it from visual, topology, interaction and delivery constraints, not an asset label. Do not force every asset through image generation or every shape through procedural construction. Generated concept candidates must establish the requested design and finish before modeling; if they contradict the brief or simplify defining features, correct them first. Additional views resolve consequential ambiguities; feeding all views into reconstruction is optional.

During iterative scene construction, default a missing noncritical asset to the installed `asset-pipeline-fal-first` workflow at the `preview_runtime` endpoint when paid use is authorized and its audition can answer a real question. Integrate the preview into a representative gameplay view before deciding whether to spend on the full workflow. Go directly through this full workflow when deformation, exact repeated interfaces, close interaction, a defining thin/hollow structure, or prior evidence makes a generated donor unlikely to survive into the result.

Escalate a preview to the full workflow when a representative in-engine view shows a major defining visual defect, a hard motion/interface/export/runtime gate fails without a small local repair, repetition makes the defect conspicuous, or the estimated repair is no cheaper than rebuilding by the stronger route. Retain the preview when it passes its runtime budget and its remaining defects do not materially weaken the scene at expected distance. Record the evidence and decision; do not infer importance from an asset category alone.

Name the defining visual features that must survive the chosen route, including characteristic construction and surface response. Read [visual acceptance guidance](references/visual-quality.md) for high-fidelity work and appearance failures.

Record a compact plan: geometry route and appearance route, dominant visual risks, cheapest discriminating proof, acceptance evidence, resource budget, and the boundary for returning that proof. Exact geometry does not imply a procedural surface route. Check available task-specific capabilities before inventing a new material or conversion system. Separate proving a method from fulfilling an asset with a proven method.

## Work and review

Use the available `concept-to-reality` skill for reference matching and staged visual corrections. If unavailable, retain its essential behavior: lock a plausible comparison camera; inspect actual renders against the target; resolve dominant shape/construction errors before fine surfaces; record concrete discrepancies and the predicted effect of each edit; recheck the retained candidate against the delivered export.

Judge each candidate against the target as well as its predecessor: an improvement can still fail acceptance. Keep visual resemblance, construction/function and export integrity as separate verdicts. Unresolved defining visual features require revision; a limitations paragraph does not waive them.

For high-fidelity work with an unproven route or prior visual failures, demonstrate the hardest visual feature on a representative region before committing to full finishing: recognizable shape/contact plus actual surface response at target size. Use the [visual proof and correction loop](references/visual-quality.md). In delegated work, the requester independently reviews that checkpoint before dependent full finishing; this is an internal agent handoff, not a new user approval requirement. Continue unaffected work while review is pending. Proven reusable methods and simple low-risk assets need no extra checkpoint ceremony. Produce the full diagnostic/assembly/reimport suite once visual evidence merits it, except for early export/fit feasibility probes.

Classify each failure before acting: reference ambiguity, silhouette/geometry, functional fit, UV/material, camera/presentation, export/tooling, or runtime integration. Repair the failing layer. If geometry is good and weave/grain is missing, test a local material repair before regenerating geometry. Higher resolution and more polygons do not establish better resemblance.

For meaningful iterations, log the hypothesis, changed layer, actual evidence, effect on the original target, regressions and retained revision. Camera/tooling repairs are distinct from artistic gains. A sharper texture or more complex mesh can move the whole result farther from the target. Preserve useful regions as recovery candidates; only an evidenced visual pass makes their appearance settled.

When a targeted correction leaves the same dominant defect, use the diagnostic and method-review boundary in [visual acceptance guidance](references/visual-quality.md). Return the failed proof before starting another speculative treatment. The requester reassesses the cause, including its own prior instructions, and chooses a bounded different experiment. This continues authorized work without turning every partial gain into another polishing batch or inventing user approval requirements.

Use shared materials with physical UV scale and appropriate grain/end cuts. Inspect roughness, normal strength, UV channel bindings and actual export behavior. Generated/derived channels may be useful authored approximations; do not call them measured PBR. Keep shader choices compatible with the requested delivery format.

For `preview_runtime` or `production_runtime`, measure actual triangles/vertices, renderer or primitive count, material slots, texture dimensions and estimated resident texture memory after target-platform compression, collider complexity, LOD availability and maximum expected simultaneous instances. Derive budgets from target hardware, frame target, scene baseline, screen coverage and repetition; do not impose universal per-prop numbers. Use shared material/texture dependencies instead of embedding duplicate copies in every asset. Check the asset in a gameplay camera with the scene's ordinary lights and effects. A standalone hero render remains supporting evidence only.

For modular/interactive requests, preserve metric geometry, named parts, pivots, connector coordinate frames, mating clearances and interface versions. Reuse actual compatible parts instead of remodeling lookalikes. Render a real alternate assembly and normally hidden surfaces. Verify relevant intersections or motion envelopes on actual geometry; names and overall bounding boxes do not prove fit. Scale verification to visibility and use rather than engineering every decorative prop.

## Resource control and resumability

Paid permission belongs to the request/session scope; an earlier unlimited experiment is not a future default. Check exact current endpoint pricing and supported parameters before a paid call. Reserve estimated cost, including outstanding or billing-uncertain attempts, within both job and shared batch budgets. Persist endpoint, input hash, settings, seed where supported, provider job ID and estimate before waiting. On timeout/restart, reconcile the existing job rather than blindly resubmitting. Provider completion status must yield a valid artifact before success is recorded.

Optimize cost and time among routes that meet the quality target. A cheap result that fails that target is not a successful efficiency result. Budget for finishing and review, not only initial construction. A source plus a hypothesis-driven alternative can be a useful initial plan, not a fixed iteration ceiling or reason to abandon authorized local correction. Stop paid submission at the actual ceiling; preserve the best candidate and state the unmet requirement. Continue authorized local work when useful. Do not manufacture approval requirements for already authorized work.

Record provider wait, local render/build, active work when measurable, total elapsed, infrastructure retries, estimated versus confirmed charges and bytes retained. Unknown costs/timings remain unknown. Do not copy base64 media or whole conversations into manifests.

Keep the retained source/export, necessary unreproducible inputs and paid source candidates, scripts/settings/provenance, plus compact comparison evidence. Prune only owned reproducible intermediates after verification; do not delete another worker's data. Avoid duplicate texture packs and full alternate-assembly exports. Track shared dependencies before cleanup. Do not add large binaries to ordinary Git history against project conventions.

## Handoff and asynchronous use

For an implementing agent with authorized delegation, follow [native sub-agent workflow](references/subagents.md): search the library, write a compact request, spawn a worker with this skill and that request, then continue independent implementation. Read [request and result contract](references/request-contract.md) when a durable workflow is needed. An asset request should return a ticket and stable proxy contract promptly so scene work can continue. If a queue/worker is unavailable, say the request is recorded rather than claiming it is executing asynchronously. Use an existing authorized orchestration mechanism. When the user asks for sub-agent asset work, native spawn/message/follow-up tools are sufficient; a separate SQLite queue and persistent daemon are optional future infrastructure.

The worker owns candidate files; the requesting agent owns scene integration. Publish an immutable revision with source/runtime paths as requested, hashes, preview evidence, dimensions/axes/pivots, named parts/interfaces, material dependencies, provenance, costs and limitations. Inspect the delivered export under the comparison settings and run checks appropriate to the endpoint. For runtime requests, verify the actual engine appearance and requested budgets through the project's integration route.

A failed defining visual criterion leaves the job working in review, with a retained candidate and a concrete correction. A checkpoint message can end the worker turn without completing the asset request; the parent resumes the same worker. Return an incomplete outcome only at a real scope/resource boundary or blocker. A first-delivery experiment may intentionally freeze a deficient candidate when explicitly requested; ordinary fulfillment does not inherit that stopping rule.

Distinguish a retained recovery candidate, technical verification, requester visual acceptance and user acceptance. A later failed review must be visible in library search and the gallery for that exact revision, while preserving historical evidence; do not keep recommending a known deficient revision as accepted. Distinguish worker-reviewed, requester-accepted and user-accepted states. Return concrete unmet criteria if the result cannot pass. A ready event points to durable state; it is not the only copy of the result. Changed specifications require a new revision and stale workers must not overwrite it. Do not replace the scene proxy automatically unless integration is part of the authorized worker scope.
