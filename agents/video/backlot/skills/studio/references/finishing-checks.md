# Finishing and preservation checks

Apply only the checks for the outputs requested by the Brief or user. Music, SFX, dialogue, VO, native sound, exact graphics, captions, vertical versions and localization are optional modules; none is implied by assembling a picture. Keep custom renderers and project-local recipes supported.

The `backlot assembly`, `deliverable`, `delivery`, score and archive commands record and inspect the exact files. This reference adds the human visual and listening checks that media probing cannot establish.

## Bind finishing work to the picture

- Identify the exact accepted picture cut, its content hash, probed frame rate, frame count and duration. A filename or matching duration alone does not identify the cut.
- Bind every cue map and exact graphic to that picture identity and an explicit time origin. State whether timing starts at the first picture frame or at a specific boundary such as the end of a title. Convert frame positions using the cut's measured frame rate; do not assume a rate or mix origins silently.
- Keep approval scope clear. An accepted picture remains the picture approval. A later score, graphic or share version has its own variant and review record; it does not silently replace the accepted master.

## Sound when requested

- Use the exact title end frame when placing score after a title. Check the title sound and score join together, including the intended gap or overlap.
- Probe the actual selected audio file. Use its measured duration and decoded sample count where sample-accurate trimming matters; a requested generation duration is not evidence of the file's actual length. Trim or pad to the accepted picture boundary as specified by the finishing request.
- For a score-only change, verify the full accepted picture frame sequence and timing are preserved in the composite. Matching duration or frame count alone is insufficient; compare the decoded frames or verify an unchanged picture stream where the renderer supports it.
- Listen to the assembled output at cue starts and ends, picture cuts, the title/SFX boundary and critical synchronization points. Check VO masking only when VO exists in the requested cut.
- Report technical checks (decode, stream metadata, duration, frame preservation) separately from listening review, visual review and the user's decision. If actual listening or visual review was unavailable, say so; a clean decode does not establish a semantic review.

## Exact graphics when requested

- Use deterministic lettering or overlay rendering for text that must be exact. Keep generated background imagery separate from the approved text and sound layers.
- Inspect the final rendered output at its target size for exact wording, spelling, placement and legibility. Record the source assets and the reproducible overlay recipe with the finishing variant.
- Preserve the original outcome for a rejected generated source. Acceptance of a corrected local derivative does not change the raw source's rejection.

## Variant and archive provenance

For each finished variant, retain enough information to identify its picture and audio sources, their content identities and probe results, the renderer or mix recipe and settings, the output's measured media properties, the checks performed, and the approval scope. Give variants distinct names, mark which one is current, and preserve supersession relationships. Record share-link expiry separately from master identity; an expired link does not change the file it once pointed to.

A media archive manifest must enumerate the external and Git-ignored media needed to reproduce the selected final, including the files themselves or stable content identities. Its check must establish that required files are present and match those identities. A documentation commit or temporary share URL alone does not prove the media can be recovered. When practical, reproduce the selected final from the chosen source bundle in a fresh folder and compare its output identity with the recorded variant.
