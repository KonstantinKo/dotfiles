---
name: higgsfield-seedance-prompt-builder
description: Design and repair cinematic Seedance shots in Higgsfield, including blocking, acting, camera devices, reference roles and dialogue timing. Use alongside prompt-seedance-2-5 for Seedance 2.5 platform details.
license: MIT
metadata:
  version: "4.4.2-adapted"
---

# Higgsfield Seedance prompt builder

Adapted from the user-supplied CINEDANCE v4.4.2 guide. The complete supplied file, including its MIT declaration, is preserved in [original-v4.4.2.md](references/original-v4.4.2.md). Its professional provenance is user-reported; its prompting preferences are not provider guarantees or measured success rates.

## Compose a shot

Use [shot-direction.md](references/shot-direction.md) when designing or repairing a shot. Identify its dominant purpose, active references, opening frame, physical geography, action and ending. Match framing to the performance detail that needs to read. Give camera movement a reason and preserve requested creative devices through concrete physical instructions.

For Seedance 2.5, also read [prompt-seedance-2-5](../prompt-seedance-2-5/SKILL.md) for reference syntax, endpoint constraints, audio controls and platform observations. The supplied guide targets Seedance 2.0/Higgsfield; do not assume its advice establishes 2.5 capabilities. Check current provider documentation/schema when resolving an API or capability question. Prompt writing does not authorize paid generation; use `higgsfield-generate` and the project's spending rules when generation is requested.

For a simple shot, write compact prose. For complex shots, use only the sections that clarify it:

```text
BRIEF: <the shot's purpose>
REFERENCES: <actual attached assets and their scoped roles>
OPENING / SPACE: <visible starting state, subjects, orientation, camera side>
CAMERA: <framing, physical position, one strategy or requested device>
BEATS: <action and reactions in order, ending or hold>
LIGHT / SOUND: <motivated sources; exact supplied dialogue if any>
CONTINUITY: <specific invariants and relevant failure prevention>
```

Respect the user's requested language and output format. For a final/copy-paste request, return the clean prompt. Keep generation settings separately when the interface controls them. During revisions, preserve successful wording and change the part responsible for the failure.

For a narrative sequence, briefly establish what happened before it, the current story turn, and what follows. Treat an emotion reference as a vocabulary or range, then let each beat's action motivate its expression; avoid repeating one fixed expression instruction in every beat. If a supplied video governs the sequence's cuts, camera and blocking, assign that role once and use beat descriptions for the actions that need clarification. Let prop references establish dimensions; add size words only when a scale contrast matters to the story.

## Use the full guide selectively

Read relevant sections of [the original](references/original-v4.4.2.md) for extended examples: `SPATIAL BLOCKING`, `SHOT ANGLE AND VIEWPOINT SOLVER`, `UNIVERSAL CREATIVE DEVICE TRANSLATOR`, `CHARACTER ACTING RULES`, and `COMMON FAILURE FIXES`. Its separate auditor/workbench skills are optional and are not installed dependencies.

These adaptations take precedence over conflicting advice in the original:

- Treat its FOV ranges, section template, lighting preferences and device counts as creative suggestions. Framing and readable subject size matter more than numeric lens metadata. Its approximate diagonal FOV table assumes rectilinear projection on a 36×24 mm sensor; sensor dimensions and crop change the mapping ([ARRI camera FAQ](https://www.arri.com/en/learn-help/learn-help-camera-system/frequently-asked-questions)). Describe camera distance as well as lens choice when directing perspective compression.
- Correct the original dolly-zoom example: moving closer requires zooming out (widening FOV) to hold subject size; moving away requires zooming in. Describe the held subject size and changing background perspective without inventing an exact distance/FOV pairing.
- Numeric timestamps, FOV, shutter language and “100% matches” are direction, not guaranteed controls. Natural motion blur is useful for ordinary action; retain an intentionally crisp/staccato look when requested.
- Opening frames must match the intended reveal. Do not force an off-screen character or hidden prop into frame zero. Distinguish reference images from images that actually pin the first frame.
- Resolve incidental conflicts with a reasonable design choice. Preserve explicit requirements, dialogue, casting and creative devices. If a conflict forces a material change, explain the tradeoff and ask only if needed to proceed; do not silently rewrite the user's brief.
- Use only attached assets and the selected interface's actual identifiers. Scope location references to layout/materials unless they also control framing. Avoid copying the guide's invented example tags into a real submission.
- Use constraints and negative fields supported by the endpoint. The guide's preference for positive wording does not remove another model's negative-prompt field. Audio instructions likewise do not replace audio settings.
