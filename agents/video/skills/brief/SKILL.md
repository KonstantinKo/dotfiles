---
name: brief
description: Write or revise the project Brief for a Backlot production. Use for "write the brief", "update the brief", "what are we making", "change the audience/length/tone", or when Status.md shows stage brief.
---

# Brief

## Purpose
Agree in writing what the film is for before anything is written or generated. The Brief is the yardstick `review` measures against.

## Inputs
- `Projects/<slug>/Brief.md` (may be a template)
- `Context/Knowledge.md`, `Context/Inspiration.md` if `ingest` ran
- `Studio/Brands/<brand>.md` when the project belongs to a brand
- `<slug>.md` frontmatter (format, fps, resolution, budget_eur, deliverables)

## Steps
1. Read what exists. List the fields still empty.
2. Ask only for the empty fields, one message. Offer a default for each so a single "ok" closes it.
3. Write `Brief.md` with these sections, each a short paragraph or list:
   - Goal (one sentence: what changes in the viewer)
   - Audience (who, where they watch, what they already know)
   - Message (the one thing they must take away)
   - Tone (three words plus one sentence)
   - Length and format (seconds, aspect, fps; variants)
   - Deliverables (files, aspect, captions yes/no, languages)
   - Mandatories (logo, claim, legal, brand rules)
   - Constraints (budget line, no-go content, deadline)
   - References (links into `Context/Inspiration.md` with intent)
   - Open questions
4. Mirror deliverables and budget into `<slug>.md` frontmatter if they changed.
5. Read the Brief back in five lines and ask for the go.

## Outputs
- `Projects/<slug>/Brief.md`
- `<slug>.md` frontmatter updated (`deliverables`, `budget_eur`)
- Stage set to `develop` once agreed

## Gate
The user says the Brief is agreed. Note it in chat and move `status` to `develop`.

## Example phrases
- "write the brief for this one"
- "the audience is now field workers, update the brief"
- "what exactly are we making here"
