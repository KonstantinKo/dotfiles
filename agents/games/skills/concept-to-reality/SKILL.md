---
name: concept-to-reality
description: Reconstruct or correct editable 3D environments, interiors, props or characters against selected concept references, using matched views and spatial validation. Applies to reconstruction workers, not neutral orchestration, workflow editing or unrelated software tasks.
---

# Concept to reality

Reproduce the defining visual relationships of the supplied concept in coherent, editable 3D. Progress means a demonstrably closer match at the requested level of finish. More geometry, attractive lighting, successful exports and passing gameplay checks do not establish resemblance.

Respect the user's current scope: a workflow discussion or skill-writing request does not authorize modeling. A blockout request does not authorize full production. Use the existing project tools and asset conventions; this workflow is engine- and modeling-tool independent.

## Assignment and continuation

Read the project's current reconstruction authority and assignment record when present before selecting work. Reuse their brief, checkpoint and review log rather than creating competing live documents. For a simple standalone task, the user's request and a short evidence note suffice; no control-file hierarchy or separate reviewer is required. Keep reference decisions separate from execution assignments. A neutral supervisor inspecting or evaluating this skill does not become a reconstruction worker.

For a supervised assignment, complete full correction cycles within the assigned work period: useful correction, actual comparison, diagnosis and justified follow-through as needed. Related local cycles may continue until a meaningful reviewable outcome or the assigned work-period boundary; if none is stated, use the requested reviewable outcome as the boundary. Return evidence then, or at a genuine blocker, without self-promoting the stage; a fixed trial count is not a worker stopping rule. The supervisor controls stage promotion after independent review. Autonomous direct work may continue within the requested endpoint with the same evidence standards.

## Establish the target

Inspect the actual reference images and any existing model renders before choosing an approach. Read the project's reference selections and explicit exceptions. Preserve original images unchanged.

For localized or material-only corrections, reuse valid reference notes, landmarks, calibration and existing comparison artifacts. Confirm that they still apply to the current revision and requested change; fresh outlines, camera fitting or a full comparison package are not required merely to repeat established work. Update the affected evidence with targeted matched renders and relevant diagnostics. Recheck shape, camera and spatial assumptions when they change, remain uncertain or are contradicted by the result; material-only scope does not establish that an unresolved shape match has passed.

Record a compact target brief in the project:
- Primary reference for each subject/view; supporting references and what each explains.
- Required resemblance: composition, silhouette, proportions, spatial relationships, characteristic forms, materials, lighting, pose or expression as applicable.
- User exceptions and technical constraints; distinguish observed features, inferred geometry and approved departures.
- Requested endpoint and review delivery, including existing HTML artifact conventions.

Do not silently replace a difficult reference with a generated reinterpretation, a convenient asset or the current blockout. Supporting plans and generated alternate views are hypotheses unless selected as authority. Their labels and scale bars are not automatically verified measurements. If references disagree, identify the affected region and preserve the primary target; seek a decision only when the conflict materially blocks progress.

Choose a few identifiable landmarks and outline major silhouettes and negative spaces in image coordinates. Select features that explain the subject, rather than mechanically tracing every painted edge. Infer depth and scale conservatively: one image cannot uniquely specify hidden geometry or absolute dimensions. Use known dimensions when available; label assumptions otherwise.

## Calibrate the comparison

Fit a reference camera using crude masses and widely distributed landmarks. Match aspect ratio, framing, projection, field of view, camera orientation and, where relevant, subject pose. Do not assume aerial art is orthographic. Check foreground and background together so lens errors are not mistaken for local shape errors.

Save the camera and capture settings. Lock them for a comparison series once a plausible fit is established. If later evidence requires recalibration, version and explain it, then recapture the baseline. Never quietly change the camera to make a revision appear better.

Use matching image dimensions and crops for reference/render comparisons. Overlays may use uniform alignment of the image frame; do not independently warp regions or stretch the render to manufacture agreement. Mark intentional exceptions. If perspective in the illustration is inconsistent, show where a single camera cannot match it and document the chosen compromise.

Keep one or more diagnostic views for depth, overlaps and hidden construction. Match each additional authoritative reference with its own camera. A good hero view must not depend on broken geometry elsewhere when the requested result is a navigable or rotatable object.

Separate **fitting evidence** from **validation evidence**. Agreement with the landmarks, contours or dimensions used to construct or fit the candidate establishes fit to those inputs; reprojecting those same inputs is not independent validation. Check relationships not forced by the fitting procedure: withheld reference features, additional authoritative views, measured constraints from an independent source, and actual same-model sections or alternate views. A second camera can expose implausibility but does not prove fidelity to an unseen side. If it becomes a tuning target, label it accordingly and retain another relevant check where feasible.

When depth, scale or projection is underconstrained, record plausible assumptions/ranges and test the consequential ones before investing in detail. Choose dimensional and secondary-view checks proportionate to the subject: room section and furniture/door scale; prop thickness and mating clearance; character profile and joint motion; terrain elevation/depth relationships and occupied-space scale. Use actual model measurements and renders, not a diagram that merely repeats generator parameters. No universal camera angles, metre values or view count apply. With only one reference, report spatial plausibility separately from reference fidelity and leave unsupported geometry provisional.

## Model by visual dependency

Advance only after inspecting evidence for the requested result. In supervised work, submit a readiness recommendation for the supervisor's independent review; in direct work, record the agent decision. Neither is user acceptance. Early export, access, rigging or performance feasibility probes are welcome when they resolve a consequential constraint, but do not pass a visual stage or authorize downstream detail while its prerequisite still fails.

| Stage | Work | Evidence needed to advance |
| --- | --- | --- |
| Major forms | Minimal editable masses, silhouette, volumes and voids | Matched view reproduces dominant proportions, spacing, overlaps and negative spaces; no unresolved major camera error; consequential depth/scale assumptions survive relevant dimensional and secondary-view checks |
| Structure | Secondary forms, openings, connections and characteristic curves | Landmark arrangement and distinctive internal contours agree; diagnostic views show coherent depth and construction |
| Surface and identity | Materials, color groups, vegetation, clothing or ornament as relevant | Characteristic surface treatment and density match without disguising structural mismatches |
| Presentation | Lighting, atmosphere, pose/expression refinement and final rendering | Intended visual impression matches at the target viewing scale; neutral and alternate views retain the structural match |
| Delivery | Export, engine integration, collision, rigging or performance work as requested | Technical checks pass and the delivered result is visually rechecked for regressions |

Use simple controlled lighting early and preserve a neutral diagnostic render through later stages. Establish broad value/color relationships early when they define the concept, but do not spend fine-detail effort while dominant shapes fail. Low-poly sketching means economical geometry, not mandatory cubes, straight lines or rigid grids. Use editable curves, silhouettes and simple custom meshes where those express the concept better.

Before choosing a narrow edit, assess whether its editable scope can resolve the dominant discrepancy; if not, include the related provisional forms or dependencies that determine it. Preserve user-approved constraints, explicit write boundaries and unrelated work, while reshaping related provisional implementation within the authorized scope instead of treating it as fixed. Choose techniques based on the observed shape error; generated 3D assets are candidates that must pass the same review.

Adapt the emphasis to the subject:
- Environments: landform and skyline relationships, voids, occupancy, elevation and route curves before paving or repeated architecture. Keep circulation adjustable; test critical scale/access early without freezing an inaccurate layout.
- Interiors: room envelope, ceiling profile, opening positions, depth layering and furniture scale before dressing. Check that the interior fits its intended exterior where relevant.
- Props: outline, profile, thickness, part ratios, joints and defining asymmetry before bevels and texture detail. Check rotation and practical dimensions.
- Characters: silhouette, gesture, anatomy/stylized proportions, facial landmarks and costume masses. Compare in the reference pose; check neutral/alternate poses and intended deformation before committing production topology.

For a large assignment, validate a representative finished portion after the overall structural match, before replicating expensive detail across everything.

## Run the visual correction loop

For each meaningful iteration:
1. Render the actual current asset from the saved comparison camera and relevant diagnostic views. Open and inspect the images; producing files alone is not review.
2. Compare reference, previous retained render and candidate at equal framing, both as thumbnails and at useful detail scale. Use side-by-side plus an overlay, blink toggle or silhouette/landmark comparison when alignment matters. Keep unaltered renders available.
3. Write the few largest remaining discrepancies, in priority order. Identify location, visible evidence, likely cause and a concrete geometry/camera/material action. Prefer "the opening is too narrow relative to the flanking columns; move its side walls apart" over "improve fidelity." Mark uncertain diagnoses and use a cheap diagnostic render to distinguish them.
4. Make a small related set of edits addressing those discrepancies. Re-render and assess the predicted effect, including regressions elsewhere. Retain an improvement or revert/rework the trial.
5. Decide **revise this stage**, **ready for stage review**, or **cannot verify**, citing the actual comparison. Direct autonomous work may advance on substantiated review; supervised workers return the recommendation. Do not advance with an unresolved dominant silhouette, proportion or spatial mismatch. A technical pass cannot overrule a failed visual gate.

Use measurements where they clarify a discrepancy: landmark displacement as a fraction of image width, silhouette overlap, or relative opening/part widths. Record what was actually measured. Do not invent similarity percentages or use a global pixel score as proof: materials, lighting and intentional exceptions can dominate it.

When trials repeatedly fail to improve the prioritized mismatch, or improving one view repeatedly breaks another, compare the last useful baseline, diagnose the failing assumption or representation, and change the approach or editable scope within the assignment. While the work period permits, carry out the justified change and compare again; an authorized structural correction should not be deferred solely as a next recommendation because local trials failed. Preserve the best result, avoid repeating the failed approach or adding unrelated ornament, and return at the outcome/work-period boundary or a genuine blocker. Neither stagnation nor an improved render alone establishes completion.

## Review artifact and handoff

Maintain the project's requested review artifact, using a stable HTML page when requested or established. Include the authoritative reference, latest actual render, previous retained result, matched comparison, relevant diagnostic views, explicit exceptions, prioritized discrepancies and next edits. Make selected references, agent-reviewed candidates and user-accepted results visibly distinct. Publish only within existing authorization.

Record the asset revision, camera/settings, evidence paths, current stage and decision in a short review log. Keep visual fidelity, functional validation and performance results separate. Final delivery must show the requested endpoint against the original target, remaining departures, editable sources and relevant technical checks. If only a coarse stage was requested, stop there with its limitations clear; do not imply the workflow has already proven final fidelity.

Keep resumable states distinct: **working** is the current trial; **retained** is the chosen recoverable baseline, possibly still deficient; **verified** names the exact revision, criterion, evidence and reviewer/check that passed; **user-accepted** records an explicit user selection and its scope. A retained model may have verified export but unverified resemblance. Acceptance of a reference is not acceptance of its reconstruction. Preserve the last retained source and evidence until a replacement is reviewed; invalidate affected checks after changes rather than inheriting old passes.

A batch return needs only the source revision/checkpoint, changed scope, matched and diagnostic evidence paths, observed gains/regressions, fit-versus-validation limits, unresolved leading discrepancy and recommended next action. Include reproducible camera/check settings or links. The supervisor should inspect raw reference/render evidence and relevant independent checks, not adopt the worker's verdict or amount of work as proof. Resume from the recorded assignment and retained baseline; do not silently select the newest file or restart concept selection.
