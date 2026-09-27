---
name: asset-pipeline-fal-first
description: Produce editable 3D game assets using reuse, early fal.ai auditions where suitable, and hybrid authored finishing. Use for asset requests or this workflow’s design; not whole-world reconstruction.
---

# Asset pipeline: fal-first

Turn a scene need into a reviewed asset with an explicit delivery contract. This workflow supports native sub-agent handoff when available and authorized. It supplies decisions and durable handoff conventions; it does not require a separate queue service. Respect discussion-only and source-only scope. Do not generate assets merely because the user asks to evaluate the pipeline.

“Fal-first” means an early economical test after reuse screening, when specialized generation plausibly helps; it is not a requirement to use fal.ai. Keep the requested finish and endpoint binding.

This is the default budget route for `preview_runtime` assets during scene construction. Its goal is a visually credible, measured asset that lets the implementing agent judge the complete scene quickly. It may also produce a production asset when all requested gates pass, but do not promote it merely because a beauty render looks convincing. Keep the high-detail source separate from the runtime derivative.

## Intake and route

Read the project's current design authority and existing asset catalog. Capture the requested use, references and their authority, dimensions/axes/pivot, viewing distance, visible sides, motion or modular interfaces, deliverable endpoint, and caller's actual cost/time/storage constraints. Distinguish hard constraints from preferences and inferred dimensions. For runtime work also capture target hardware/engine, expected simultaneous instances, performance/material/texture budgets and collision needs. Do not substitute a high-detail source for a requested runtime asset.

Preserve the requested visual standard when translating the user need into a worker brief. Source-only describes delivery/integration scope, not a lower artistic standard. Do not invent an ordinary-dressing tier, farther viewing distance or austere per-asset budget that removes defining reference features. Agent-imposed targets are planning choices; revise them before lowering quality. If an actual user constraint prevents the result, report it as incomplete.

Use sensible documented assumptions for ordinary dressing. Resolve a missing critical mating dimension or interaction contract before dependent construction; continue independent material/reuse work. Exact generated text, markings and physical labels are not trustworthy specifications.

Check existing sources, modules and materials first. Bound external research so routine sourcing does not consume the job. Verify the candidate's actual geometry, material bindings and license before accepting it. Preserve third-party provenance. A source thumbnail or a claimed PBR label is insufficient.

Resolve visual inputs using [reference intake](references/reference-inputs.md) when images are supplied or a comparison test is requested. A sufficient supplied concept skips initial concept generation. A scene image can identify one asset by description, region or mask; keep its context and authority when deriving necessary clarification. A new generated image does not silently replace the target. For a fixed-reference test, use the same image bytes, target region and brief across runs.

Choose a route using [route guidance](references/routes.md). For new construction, apply [audition and total-cost decisions](references/audition-economics.md): after library/free-source screening, prefer one small authorized specialized-3D audition early when it plausibly reduces the hardest visual work. Compare actual output before substantial bespoke modeling or shader work. Skip it with a recorded reason when unsuitable, unavailable, outside authorization or already answered by relevant evidence. Derive the route from visual, topology, interaction and delivery constraints, not an asset label. Do not force every asset through image generation or every shape through procedural construction. Generated concept candidates must establish the requested design and finish before modeling; if they contradict the brief or simplify defining features, correct them first. Additional views resolve consequential ambiguities; feeding all views into reconstruction is optional.

For scene-building requests, target `preview_runtime` unless the caller explicitly needs a production endpoint. Set a provisional budget from target hardware, frame target, expected screen coverage, maximum simultaneous instances and the current scene baseline. The preview must report actual triangles/vertices, renderer or primitive count, material slots, texture dimensions and estimated target-platform residency, collider complexity and LOD state. If those inputs are unavailable, report them as unknown and keep the result provisional rather than treating the portable source GLB as game-ready.

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

Build the cheapest runtime derivative that preserves the scene read: consolidate unnecessary renderers, reuse project materials and textures, apply target-platform texture limits/compression, add only the LODs and collision needed for expected use, and preserve pivots or separate moving parts. Do not embed the same material set independently into every asset. Inspect a representative gameplay view under ordinary scene lighting before spending on close-up polish. Keep diagnostic and beauty renders for diagnosis, not as the acceptance endpoint.

After scene integration, return one of three decisions:

- `retain_preview`: the asset meets its runtime budget and does not materially weaken expected gameplay views.
- `targeted_upgrade`: a bounded geometry, material or hierarchy repair can close the observed gap while retaining useful generated work.
- `escalate_full`: a defining visual defect remains, a hard motion/interface/runtime gate needs reconstruction, repetition amplifies the weakness, or the repair estimate is no cheaper than the full `asset-pipeline` route.

The implementing agent makes this decision from actual scene evidence. Do not spend a separate independent-review turn on every ordinary prop; batch scene-level review when several assets share the same view and reserve design-heavy review for focal failures.

For modular/interactive requests, preserve metric geometry, named parts, pivots, connector coordinate frames, mating clearances and interface versions. Reuse actual compatible parts instead of remodeling lookalikes. Render a real alternate assembly and normally hidden surfaces. Verify relevant intersections or motion envelopes on actual geometry; names and overall bounding boxes do not prove fit. Scale verification to visibility and use rather than engineering every decorative prop.

## Resource control and resumability

Paid permission belongs to the request/session scope; an earlier unlimited experiment is not a future default. Check exact current endpoint pricing and supported parameters before a paid call. Reserve estimated cost, including outstanding or billing-uncertain attempts, within both job and shared batch budgets. Persist endpoint, input hash, settings, seed where supported, provider job ID and estimate before waiting. On timeout/restart, reconcile the existing job rather than blindly resubmitting. Provider completion status must yield a valid artifact before success is recorded.

Optimize cost and time among routes that meet the quality target. A cheap result that fails that target is not a successful efficiency result. Budget for finishing and review, not only initial construction. A source plus a hypothesis-driven alternative can be a useful initial plan, not a fixed iteration ceiling or reason to abandon authorized local correction. Stop paid submission at the actual ceiling; preserve the best candidate and state the unmet requirement. Continue authorized local work when useful. Do not manufacture approval requirements for already authorized work.

For a preview, compare the projected remaining native-agent work with a fresh full-route estimate after the first imported audition and again after one bounded repair. Escape early when extraction, retopology, rematerialing and export repair would erase the provider saving. A low provider invoice is useful evidence, not the total cost of the asset.

Record native agent usage across makers, parent/coordinator, reviewers, replacements and failed attempts alongside provider costs; follow the accounting fields in [audition economics](references/audition-economics.md). Record provider wait, local render/build, active work when measurable, total elapsed, infrastructure retries, estimated versus confirmed charges and bytes retained. Unknown costs/timings remain unknown. Do not copy base64 media or whole conversations into manifests.

Keep the retained source/export, necessary unreproducible inputs and paid source candidates, scripts/settings/provenance, plus compact comparison evidence. Prune only owned reproducible intermediates after verification; do not delete another worker's data. Avoid duplicate texture packs and full alternate-assembly exports. Track shared dependencies before cleanup. Do not add large binaries to ordinary Git history against project conventions.

## Handoff and asynchronous use

For an implementing agent with authorized delegation, follow [native sub-agent workflow](references/subagents.md): search the library, write a compact request, spawn a worker with this skill and that request, then continue independent implementation. Read [request and result contract](references/request-contract.md) when a durable workflow is needed. An asset request should return a ticket and stable proxy contract promptly so scene work can continue. If a queue/worker is unavailable, say the request is recorded rather than claiming it is executing asynchronously. Use an existing authorized orchestration mechanism. When the user asks for sub-agent asset work, native spawn/message/follow-up tools are sufficient; a separate SQLite queue and persistent daemon are optional future infrastructure.

The worker owns candidate files; the requesting agent owns scene integration. Publish an immutable revision with source/runtime paths as requested, hashes, preview evidence, dimensions/axes/pivots, named parts/interfaces, material dependencies, provenance, costs and limitations. Inspect the delivered export under the comparison settings and run checks appropriate to the endpoint. For runtime requests, verify the actual engine appearance and requested budgets through the project's integration route.

A failed defining visual criterion leaves the job working in review, with a retained candidate and a concrete correction. A checkpoint message can end the worker turn without completing the asset request; the parent resumes the same worker. Return an incomplete outcome only at a real scope/resource boundary or blocker. A first-delivery experiment may intentionally freeze a deficient candidate when explicitly requested; ordinary fulfillment does not inherit that stopping rule.

Distinguish a retained recovery candidate, technical verification, requester visual acceptance and user acceptance. A later failed review must be visible in library search and the gallery for that exact revision, while preserving historical evidence; do not keep recommending a known deficient revision as accepted. Distinguish worker-reviewed, requester-accepted and user-accepted states. Return concrete unmet criteria if the result cannot pass. A ready event points to durable state; it is not the only copy of the result. Changed specifications require a new revision and stale workers must not overwrite it. Do not replace the scene proxy automatically unless integration is part of the authorized worker scope.
