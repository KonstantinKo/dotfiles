---
name: project-init
description: Start a new Backlot video production. Use for /new-project, "new video project", "set up a project for", "let's make a video about", or when no project.yaml exists above the cwd and the user wants to produce something.
---

# Project init

## Purpose
Turn a one-sentence idea into a scaffolded project (vault + project dir) with a filled `Brief.md`, in one short interview.

## Inputs
- `~/projects/video/backlot/studio.yaml` (vault path, currency, default budget)
- `Studio/Playbooks/Default.md`
- `_templates/` in the vault (the CLI copies them)

## Steps
1. Interview, at most five questions, skip any already answered in the request:
   - What is it for and who watches it (goal, audience)?
   - Length and format (default 16:9, 24 fps, 1920x1080; shorts imply 9:16 variants at deliver).
   - Tone in three words, one reference if they have one.
   - Deliverables (one master, plus variants?).
   - Budget in EUR (default from `studio.yaml`; say the number back).
2. Pick a slug: lowercase, hyphens, no dates. Confirm it.
3. Run `backlot init <slug> --format <f> --fps <n> --res <WxH> --budget <eur>`. Relay the one-line result.
   `init` must leave `~/projects/video/backlot/<slug>/.claude/settings.json` in place (copy or link of `~/dotfiles/agents/video/claude/settings.json`): it holds the spend-confirmation hook, and Claude Code does not read settings from the parent directory. Run `make` in `~/dotfiles` after init to link the Backlot skills.
4. `cd ~/projects/video/backlot/<slug>`.
5. Fill `Projects/<slug>/Brief.md` from the interview using the `brief` skill's layout. Leave unknowns as open questions at the bottom.
6. If the user handed over material (PDF, deck, URL, footage), run the `ingest` skill now.
7. `backlot status`. Report: slug, vault path, budget, the open questions.

## Outputs
- Vault `Projects/<slug>/` from templates, `Brief.md` filled
- `~/projects/video/backlot/<slug>/project.yaml`, git initialised
- `Status.md` at stage `brief`

## Gate
User confirms the slug and the budget line. Brief agreement belongs to the `brief` skill.

## Example phrases
- "/new-project product teaser for the onboarding app"
- "set up a new video project, 30 seconds, vertical"
- "let's make a launch film for the autumn collection"
