# Supplied concepts and assets inside scene images

Treat reference selection as an input decision, separate from asset construction. Use existing request fields or prose; the names below are a compact optional contract, not a requirement for a queue service.

## Choose the reference path

| Input | Worker action |
| --- | --- |
| Sufficient asset concept, photograph or approved drawing | Inspect it and use it directly. Skip initial concept generation. Infer unobtrusive hidden details conservatively. |
| Scene image with a clearly identified asset | Inspect the whole scene and the target region. If visible form/material detail suffices for the requested view/use, build from it directly. |
| Identified asset lacks a consequential view/detail | Explain the specific uncertainty. Derive only the useful clarification, attaching the original image and relevant crop/annotation through the image tool's reference mechanism. Keep original visible features authoritative. |
| No relevant design reference | Generate and review a concept against the written brief before modeling. Record the selected image as the working target. |

Sufficiency depends on the requested result: visible silhouette, part proportions, characteristic construction/materials, and any critical interaction. An unknown decorative rear often permits inference; an unseen mating socket may need a dimension or supporting view. Do not generate a concept merely to satisfy a delivery checklist. A supplied image counts as the concept artifact with its provenance. If a required referenced file is unavailable, resolve access instead of replacing it with an imagined design.

When multiple similar objects appear, use the caller's description, bounding region or mask to identify the target. Ask only if ambiguity materially affects which asset to build. Keep unrelated scene objects out of the asset. A region is an identification aid, not permission to discard contextual scale, attachments, color relationships or wear causes.

## Preserve authority

Record the primary image path/URI and content hash, what it constrains, any supporting references, the target description/region and explicit exceptions. Retain the unaltered original; a crop links back to it. Store coordinates with their convention, for example normalized `[left, top, right, bottom]` from the image's top-left. A text pointer is sufficient when unambiguous; do not fabricate a precise box without inspecting the image.

Inspect local images before sending them as generation references, and pass the actual supported reference input rather than only mentioning the filename in a prompt. The derived prompt states which visible features stay fixed and what missing information it may clarify. Review the derived result against the original region and context. New viewpoints, enhanced detail, scale labels and occluded construction are hypotheses, not new facts. Upscaling does not recover unknown detail. If the derivation changes the observed design or lowers its finish, reject or repair that derivation; do not make the easier image the modeling target.

Explicit dimensional/function constraints remain binding. If they conflict with the image, record the affected departure before expensive work. Continue on unambiguous aspects; ask the requester only when competing authoritative requirements prevent a coherent decision. Do not quietly model written proportions and later claim a match to an incompatible image.

## Derive with the fewest necessary changes

For a reference-derived image, start with the actual reference and a short description of the transformation and what must be preserved. Add output constraints needed by the next tool. Introduce further directions to address an observed failure, not to replace the reference with a speculative recipe. Invented area percentages, color ratios, damage scales and long exclusion lists can change the target even while the original file remains attached. Treat inferred parameters as hypotheses, not visual authority.

Use a supplied usable material image or reference region as a texture donor when source-access rules permit; do not regenerate an already good input just to complete a generation stage. Compare its raw palette/pattern and a simple binding on the actual representative surface before inventing corrective image recipes, crop/quilting/restoration chains or shader synthesis. Such methods remain available when a simpler baseline exposes a specific need. Compare each derived source with the original at the relevant scale; preserving a flawed intermediate's layout can preserve its errors. Restored fine detail is generated interpretation, not recovered evidence.

A texture image and a finished material are different outputs. Preserve the image's observed palette and pattern while testing physical mapping, reflectance and any derived channels separately. A whole-scene image can supply both a target object and a material reference without requiring a new design concept.

## Example request fragments

Direct supplied reference:

```json
{
  "references": [{
    "id": "primary",
    "uri": "assets/concepts/selected-prop.png",
    "role": "primary",
    "constrains": ["silhouette", "part proportions", "construction", "surface finish"]
  }],
  "concept_policy": {"mode": "use_supplied"}
}
```

Asset extracted from a place:

```json
{
  "references": [{
    "id": "place",
    "uri": "assets/concepts/workshop.png",
    "role": "primary",
    "target": "The hanging fabric pouch to the left of the doorway",
    "constrains": ["visible shape", "fabric and seams", "attachment", "scene style"]
  }],
  "concept_policy": {"mode": "derive_if_needed"}
}
```

`use_supplied` skips the initial generation; `derive_if_needed` permits reference-guided clarification only after the sufficiency check; `create` serves a missing design. With no policy, infer the appropriate path from the supplied inputs. These choices do not grant paid authorization or change reference authority.

## Comparable workflow tests

Fix image bytes and target region, written specs/exceptions, viewing/evidence conditions and resource/source-access policy. Record skill/model/tool versions and intentional differences. Vary the method under test, not the visual goal. Separate a requested first-delivery freeze from a normal job that includes correction to acceptance. Do not confuse repeated use of one prompt with a fixed reference: stochastic concepts change the task. Measure time/cost to the same achieved quality; keep partial outcomes in the comparison instead of counting them as cheap successes.
