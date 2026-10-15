# Production checks for shots and repairs

Read the checks that apply to the current operation. Keep them scoped to the brief and shot.

## Active intent and references

Resolve a shot by its semantic scene/beat name and stable ID. Precedence is: user-approved shot-specific direction, active Brief/Script, shot note, approved Context/locks, then purpose-scoped reference inputs. If active records conflict or a request would change a lock, surface the conflict before changing the plan.

For each shot, preserve a compact card in its note or handoff:

- story context: the relevant prior, current, and next beat; emotional intent;
- visible action and start/end state;
- scene geography and actor facing, gaze, and travel;
- camera position/side, framing, and movement, stated separately from actor direction;
- only the fixed constraints relevant to this shot.

List references by purpose and in submission order. For each one, record what it establishes, what it must not contribute, and its approved scope or exceptions. Keep identity/appearance, location geometry, camera or motion guide, and lighting/look authorities distinct when the task needs those roles. Preserve semantic context from nearby beats or shots when it matters to continuity. Do not reuse a reference outside its approval scope.

Until structured records exist, these compact text blocks can live in a shot note or review handoff; they are guidance, not CLI schema:

```text
Shot: <semantic scene> / <shot ID>
Story: previous beat → current beat → next beat; emotional intent
Action: visible action; start state → end state
Space: geography; actor facing/gaze/travel; camera side/framing/movement
Fixed: constraints that apply to this shot

Reference: <take ID or path> | role/purpose | proves | exclude | scope/exception
Submission order: <reference IDs in exact provider order>
```

## Route and estimate

Before quoting a cost, resolve the exact provider, model and version, route/endpoint, operation, ordered inputs, and settings. Check the provider schema and effective input behavior: which controls the selected route actually retains, ignores, or requires. Check whether each relevant promotion applies to that exact route, version, and operation. Use only supported effective controls. Record unknowns plainly; do not price a guessed configuration as exact.

For the full quote, authorization, and retry procedure, follow [Decision and spend](decision-and-spend.md). Each authorization binds to one exact paid call; a paid retry needs a separate authorization. Free/local calls need no spend authorization.

## Review and repair

Separate technical validity (decode, duration, resolution, audio, expected files) from semantic/story intent, continuity/context, and the user’s subjective decision. Check the full shot or cut where possible; include risky middle regions, transitions, and the context needed to judge the requested action. State review coverage as full playback, sampled frames/segments, or technical checks only. Sample-only review leaves unsampled motion and transitions unresolved; decode and endpoint checks do not establish a full visual pass. The lead’s review is evidence for the user, not the user’s approval. Present first-pass results before proposing another paid call.

For a repair, start from the exact parent manifest and inspect the requested feature plus nearby semantic content. Preserve proven references, controls, and unaffected action; change only the authority needed to fix the defect. Compare before/after and neighboring context. A completed API job or valid file with no visible target change is an ineffective repair, not a success.

Record a review/repair in a compact note or handoff: render and take IDs; intended criterion; technical result and evidence; semantic/context result and timecodes; user judgment/decision; accepted limitations; repair parent and request; preserved inputs/controls; changed inputs/controls and estimate; before/after plus neighboring context; visible outcome; cause or `failed; cause unavailable`. Keep each check scoped to the requested operation.

Use “failed; cause unavailable” when returned evidence gives no cause. Do not infer moderation, model limitation, or user-input fault. Keep user-accepted limitations closed unless the user reopens them.

Choose a pilot only when a material question remains and at a fidelity that can answer it. Use readable identity detail for likeness questions. Honor the user’s selected full-resolution path; a smaller proxy cannot validate full-resolution requirements.

## Optional review branches

- **Timed sound:** when the deliverable requests music, SFX, dialogue, VO, captions, or native sound, listen to the actual assembled mix at the title/SFX boundary, cue starts and ends, cut transitions, and critical synchronization points. Verify timing against the current picture version. If listening is unavailable, record semantic audio review as pending; a clean decode alone is a technical pass.
- **Blender previs/export:** when Blender is part of the requested workflow, verify the saved scene version, active scene/camera/frame range, evaluated geometry and parenting/contact, start/end poses, screen direction/timing, lighting across cuts, and silhouette/readability at the chosen output size. Record the scene’s scale assumption and basis; a model-facing illustrative blockout does not require exact real-world scale. Leave the intended editor on the requested scene/camera/frame for handoff. Apply a scene-review-before-export gate only when the user requested it. Inspect rendered output and confirm the exported frames came from that saved scene/camera/range and its readability settings. Skip these checks for productions that do not use Blender.
- **Mobile review page:** when the user selects an HTML/mobile review surface, show the whole frame and readable detail with active version and submitted-input context. Check the actual page on the target mobile viewport, identify the published revision, and report publication failure honestly. Skip this branch for other review surfaces.

For a requested Blender handoff, keep a compact record with the scene file/version/hash, active scene, camera and frame range, scale assumption/basis, evaluated-geometry result, contact/parenting result, start/end poses, screen direction and timing, lighting across cuts, silhouette/readability settings, intended editor state, review gate status, and exported frame/version. Use a minimal blockout when it answers the spatial question; another guide or no guide may fit better. Put temporary previews in a temp directory. Remove only unreferenced drafts under an explicit retention policy; preserve selected sources, editable scenes, and reproduction inputs.
