---
name: preproduction
description: Prepare only declared cast, world, visual and voice requirements for a Backlot project. Use for "cast this", "lock the look", "find locations", "pick voices", or "options for Mia".
---

# Preproduction

## Purpose
Lock the Context elements that the declared scenes depend on.

## Story and reference evidence
When the user asks to settle story first, resolve the arc, emotional turns and visible actions before opening prop, costume or production-detail questions, unless a detail changes the requested beat. Reference photos, likeness sheets and Blender previs are optional tools; use them when the brief or a concrete visual question calls for them. A reference has only the authority its record names, so an appearance or layout guide does not imply identity approval.

Keep source facts, modeling assumptions and approved deviations distinct. Tie each source fact to a reference ID and a locator that was checked; label assumptions with their basis and confidence; record deviations with their exact approval scope. Use [Reference records](../studio/references/reference-records.md) for provenance, limitations and authority. Search for semantic visual features, inspect the useful frame with nearby frames, and record a locator only after verification. Do not select from an approximate timestamp alone. A shot card lists only references actually sent for that request, in their exact order.

## Inputs
- `Projects/<slug>/Script.md` (locked), `Brief.md`
- `Context/Rules.md`, `Studio/Playbooks/Default.md`
- `Studio/Workflows/Casting.md`, `Studio/Workflows/Production Design.md`
- `Studio/Styles/*.md`, `Studio/Brands/*.md`, `Studio/Voices/*.md`
- `Studio/Models/` via `backlot models --kind image` (lite tier for options)

## Available locks

| Lock | Context notes | Workflow |
|---|---|---|
| Cast | `Context/Cast/<Name>.md` | Casting |
| Locations and props | `Context/Locations/<Name>.md`, `Context/Props/<Name>.md` | Production Design |
| Visual language | `Context/Visual Language.md` | Production Design |
| Format and deliverables | `<slug>.md` frontmatter, `Context/Rules.md` | none; confirm from Brief |
| Voice (per cast member) | `voice:` in each Cast note | Casting |

## Steps
1. Read `project.yaml workflow` and the Brief. Create Context notes only for elements used by the declared identity, world, voice or generated-board work. Frontmatter: `locked: false`, `depends_on: []`.
   Add a project-dir `references.yaml` record only when a reference helps answer a stated production question; it does not create a requirement to use a reference.
2. Visual language first. Spawn `production-designer` with Brief, Inspiration, Styles. It drafts `Visual Language.md`: palette, lens and light, grain, movement, prompt fragments, negatives. Present; the user picks.
3. Cast. Follow `Workflows/Casting.md`. Spawn `casting-director` to draft each Cast note (look, age, wardrobe, mannerisms, voice brief) and 2–4 option prompts per unlocked member. Generate options: `backlot gen img --model <lite image model> --prompt "..." --n <2-4> --depends-on "Cast/<Name>,Visual Language"`. For paid calls, follow [Decision and spend](../studio/references/decision-and-spend.md); free/local calls need no authorization. Present thumbnails by take ID.
4. Approve one per member with the exact user approval text and reference: `backlot approve <take> --lock Cast/<Name> --reason "..." --source-message "<approval text>" --source-ref "<message reference>" --scope "lock Cast/<Name>"`. Reject failed options with a reason and concrete review evidence when available; a rejection is a reviewer finding unless the user explicitly rejected it. See [Decision and spend](../studio/references/decision-and-spend.md).
5. Voices. From `Studio/Voices/`, shortlist two per speaking cast member. Generate a sample line each with `backlot tts --model <tts> --voice <id> --text "<a script VO line>" --depends-on Cast/<Name>`; paid calls follow [Decision and spend](../studio/references/decision-and-spend.md). Record the selected take with the user's explicit approval text/reference, reason, and voice-lock scope, then write `voice: <id>` into the Cast note.
6. Locations and props. Follow `Workflows/Production Design.md`; same option loop, `--depends-on "Locations/<Name>,Visual Language"`. Lock with `--lock Locations/<Name>`.
7. Format and deliverables: confirm aspect, fps, resolution, variants from Brief; write `Rules.md` overrides (aspect, default models per kind, playbook exceptions).
8. Run read-only `backlot stage --json`. Resolve only the declared lock or voice blockers; the project stage is a summary.

## depends_on discipline
Every Context note that borrows from another names it in `depends_on` (a Cast note that fixes wardrobe to the palette lists `Visual Language`). Every generation names the notes it drew from. This is what lets `backlot stale` find the blast radius later.

## Outputs
- `Context/Visual Language.md`, `Context/Cast|Locations|Props/*.md` with `locked: true`, `locked_take`, `voice`
- `Context/Rules.md`
- Approved option takes, reasons in `Decisions.md`

## Gate
Each declared lock resolves to a selected, approved take and each requested voice has exact media evidence. A project without those requirements has no preproduction lock gate.

## Example phrases
- "cast Mia, give me three looks"
- "lock the visual language"
- "pick a voice for the narrator"
