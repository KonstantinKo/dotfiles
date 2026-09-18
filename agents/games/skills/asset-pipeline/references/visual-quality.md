# Visual acceptance at the requested finish

Use this guidance for high-fidelity assets and when a technically correct candidate still looks wrong. It is not a mandatory map inventory or asset taxonomy.

## Preserve the target

Before production, identify the few features that make the reference convincing: for example the layered assembly around a joint, the relationship between a binding and soft contents, or erosion across a stone edge. Translate these into observable acceptance criteria, not implementation counts. A named material, a part named “bearing”, hundreds of strands, nonzero noise or a full set of texture slots does not prove the feature is visible.

Review original reference, previous retained candidate and current actual render at comparable object size; use the delivered export once it exists. Check the whole asset and the details carrying its identity. A small model surrounded by empty space can hide failures visible in the larger concept. Use an existing valid camera and targeted detail views; don't restart calibration or a full render suite for every local correction. Judge silhouette, negative spaces, part proportions and characteristic profiles explicitly. A correct part count or pivot does not establish those visual relationships. Keep geometry fixed during a material experiment when useful, without treating that experimental control as visual acceptance. Camera landmarks or projected points used to fit the candidate are fitting evidence, not independent shape validation; check remaining relationships and state projection uncertainty before deforming geometry to absorb a camera error.

Keep three decisions separate: visual fidelity, construction/function, and export/integration. None substitutes for another. A mechanically valid asset can remain visually unfinished. An attractive render can hide invalid construction. An improved candidate can still fall substantially below the target. Preserve it as a recovery point and continue the relevant work; do not silently relabel it as a simpler quality tier.

## Diagnose material and construction together

Choose the representation by visible effect and scale:

- Silhouette changes, substantial pits, chipped rims, layered housings and compressed bundles need geometry or displacement that survives the delivery route. Shading normals cannot produce silhouette changes or real occlusion depth.
- Fine surface relief may use normals/bump; judge its physical scale and lighting response in the actual render. Larger and finer relief should not collapse into uniform noise.
- Base color, roughness and metallic/specular response must describe the same surface. A color photograph plus an unrelated roughness map is a candidate approximation, not evidence of coherent material behavior. Wear should follow edges, contact, handling, exposure or deposition when those causes define the reference.
- Oxidized metal needs the observed relationship between worn metal, corrosion and accumulated dirt, not merely brighter brown mottling. Wood needs appropriate grain direction/scale and local shape/wear; staining a regular cylinder does not produce a natural branch.
- Where objects constrain each other, model the visible consequence: compression and strand deflection under a binding, compression at upholstery seams, seating of a fitted collar. Moving a band outward until it no longer intersects the contents may remove the very contact relationship the reference requires.

When mechanical faces read rounded or parts appear detached, separate the actual profile, face normals, bevel/smoothing boundaries and seating gaps under plain material. A sloped profile plus fully smooth normals can erase intended planar faces; extra smoothing or detail can worsen that cause. Judge the contact gap by its visible assembly relationship as well as clearance.

Use a small material/construction sample when it resolves the main risk: one joint and grip, one bound cross-section, one worn rim. Preserve interfaces on modular assets while adding surface character away from critical mating regions.

Inspect in the reference-like lighting and use a neutral or grazing-light diagnostic when relief or reflectance is uncertain. Separate baked illumination from surface color when it causes a false appearance; avoid double-darkening crevices with multiple occlusion treatments. Use the material workflow appropriate to delivery: metallic-roughness does not universally need separate diffuse and specular maps, and not every asset needs displacement or baked AO. More maps do not guarantee depth. Verify the visible result and exported bindings; source-only shader displacement may require real geometry or a supported runtime implementation.

## Use a proof that distinguishes causes

For an unproven high-fidelity route, identify the dominant discrepancy and the smallest test that can resolve its cause. State one question and an observable outcome before editing. Compare the original, last useful baseline and current result at both whole-object and decisive-detail scales. Broad value/color balance, material distribution and part proportions precede extra scratches or microrelief.

For appearance failures, separate the layers instead of compensating for one with another:

| Uncertainty | Discriminating evidence |
| --- | --- |
| Wrong source pattern or palette | Original region beside the unmodified source; assess feature size and distribution before shader changes |
| Stretch, seams, direction or repeated marks | Simple checker/directional source on the affected curved, flat and joining surfaces at the intended UV scale |
| Shading or baked-light contamination | Same source and mapping with a simple material baseline, then the questioned channel under fixed exposure and two light directions |
| Shape/contact hidden by a rich finish | Plain-material silhouette/profile/contact view against the reference relationships |

Use only diagnostics relevant to the observed defect. A color source's brightness is not automatically height, roughness or metalness. Derive such channels as explicit hypotheses and inspect their effect individually. Preserve a baseline before desaturation, color gains, procedural overlays or threshold-based material masks. If the source already looks wrong, repairing its symptom downstream adds uncertainty. If the source looks plausible but its application fails, hold source and mapping fixed and directly disable or vary inherited normal/height and roughness response before generating another source. Color-derived channels are hypotheses, not ground truth; excessive granular relief or reflectance can overwhelm a sound color source. Retain only channel changes whose actual surface response improves the reference match.

Prove the chosen treatment on an actual representative region, including a meaningful edge/contact and enough different surface orientations to expose mapping problems. A disconnected flat swatch is insufficient when geometry or mapping causes the failure. Transfer only after the region passes, then inspect the full object for repetition, material zoning and overall resemblance before final baking/export. A localized wear source applied uniformly across unrelated parts can erase the reference's construction and use history.

## End an experiment before starting another

A bounded proof returns its question, changed layer, raw images, outcome relative to the original, regressions and next decision. Label a local gain separately from overall fidelity: sharper boundaries can coexist with worse color or wear coverage. In delegated work, return the proof when that question is answered, including failure; don't silently append more source-generation, mapping and shading experiments before the requester sees it. Routine correction of a known tool error can stay local. Keep compact evidence current without packaging a full release at every checkpoint.

The requester opens the original and raw evidence, reassesses all dominant discrepancies, and records whether the proposed edit can actually close them. When feedback repeats the same leading failure after a targeted correction, enter `method_review`: inspect the last useful baseline, source and binding, falsify the diagnosis, and select a bounded different method test. Changing a seed, provider name or number of texture layers does not establish a different effective method. A failed alternative is evidence to reassess the route, not an automatic invitation to another polishing batch.

This boundary pauses the failing technique, not the user's authorized task. The requester can continue independent work and authorized method development without new user permission. It must not lower the acceptance gate, mark the job finished, or send an indefinite "keep refining" assignment. Reopen provisional shape or material choices when evidence contradicts an earlier retention decision; do not preserve the parent’s mistake as a constraint.

Measure efficiency at comparable achieved quality, including unsuccessful route tests, implementation effort and review. Track artistic changes, integration/tooling repairs and provider waits separately. A cheap provider bill and many completed renders do not establish a scalable pipeline.
