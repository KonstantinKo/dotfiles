---
name: preproduction
description: Pre-production for a Backlot project: the four locks (cast, locations and props, visual language, format and deliverables) plus a voice per cast member, via the Casting and Production Design workflows. Use for "cast this", "lock the look", "find locations", "pick voices", "options for Mia", or when Status.md shows stage preproduction.
---

# Preproduction

## Purpose
Lock every element the shots depend on, so boards and video are generated once against stable Context.

## Inputs
- `Projects/<slug>/Script.md` (locked), `Brief.md`
- `Context/Rules.md`, `Studio/Playbooks/Default.md`
- `Studio/Workflows/Casting.md`, `Studio/Workflows/Production Design.md`
- `Studio/Styles/*.md`, `Studio/Brands/*.md`, `Studio/Voices/*.md`
- `Studio/Models/` via `backlot models --kind image` (lite tier for options)

## The four locks plus voice

| Lock | Context notes | Workflow |
|---|---|---|
| Cast | `Context/Cast/<Name>.md` | Casting |
| Locations and props | `Context/Locations/<Name>.md`, `Context/Props/<Name>.md` | Production Design |
| Visual language | `Context/Visual Language.md` | Production Design |
| Format and deliverables | `<slug>.md` frontmatter, `Context/Rules.md` | none; confirm from Brief |
| Voice (per cast member) | `voice:` in each Cast note | Casting |

## Steps
1. From the seed list at the bottom of `Script.md`, create one Context note per cast member, location and prop from `_templates/`. Frontmatter: `locked: false`, `depends_on: []`.
2. Visual language first. Spawn `production-designer` with Brief, Inspiration, Styles. It drafts `Visual Language.md`: palette, lens and light, grain, movement, prompt fragments, negatives. Present; the user picks.
3. Cast. Follow `Workflows/Casting.md`. Spawn `casting-director` to draft each Cast note (look, age, wardrobe, mannerisms, voice brief) and 2–4 option prompts per unlocked member. Generate options: `backlot gen img --model <lite image model> --prompt "..." --n <2-4> --depends-on "Cast/<Name>,Visual Language"`. Exit 3: show estimate, ask, rerun with `--yes`. Present thumbnails by take ID.
4. Approve one per member: `backlot approve <take> --lock Cast/<Name> --reason "..."`. Reject the rest with a reason.
5. Voices. From `Studio/Voices/`, shortlist two per speaking cast member. Generate a sample line each with `backlot tts --model <tts> --voice <id> --text "<a script VO line>" --depends-on Cast/<Name>`. Approve one; write `voice: <id>` into the Cast note.
6. Locations and props. Follow `Workflows/Production Design.md`; same option loop, `--depends-on "Locations/<Name>,Visual Language"`. Lock with `--lock Locations/<Name>`.
7. Format and deliverables: confirm aspect, fps, resolution, variants from Brief; write `Rules.md` overrides (aspect, default models per kind, playbook exceptions).
8. `backlot status`. When all locks show true and each speaking cast member has a voice, set `status: boards`.

## depends_on discipline
Every Context note that borrows from another names it in `depends_on` (a Cast note that fixes wardrobe to the palette lists `Visual Language`). Every generation names the notes it drew from. This is what lets `backlot stale` find the blast radius later.

## Outputs
- `Context/Visual Language.md`, `Context/Cast|Locations|Props/*.md` with `locked: true`, `locked_take`, `voice`
- `Context/Rules.md`
- Approved option takes, reasons in `Decisions.md`

## Gate
All four locks plus voices. Ask for each lock explicitly; one message per element with the take IDs to choose from.

## Example phrases
- "cast Mia, give me three looks"
- "lock the visual language"
- "pick a voice for the narrator"
