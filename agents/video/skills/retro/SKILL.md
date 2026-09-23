---
name: retro
description: Post-production retrospective for a Backlot project. Use after a delivery or an abandoned production when asked to "run the retro", "what did we learn", "write up lessons", "retro this project", or via /retro. Reads the project's ledger, costs, takes and status, writes a Lessons note, and proposes concrete Playbook, Workflow, model-note and skill edits.
---

# Retro

## Purpose
Turn one finished (or stopped) production into durable studio knowledge: what cost more than planned, which models and prompts worked, where the agent or the user got stuck, and which standing rules should change. The retro is the only mechanism by which the studio improves between projects.

## Inputs (read all, in this order)
- `Projects/<slug>/<slug>.md` frontmatter: status, budget_eur, spent_eur, format
- `Projects/<slug>/Decisions.md`: every approve, reject, stale, lock with its reason
- `Projects/<slug>/Costs.md` and `backlot cost --json`: spend per model and per shot
- `Projects/<slug>/Takes/*.md` frontmatter: status, model, parent, cost, prompt
- `Projects/<slug>/Shots/*.md`: how many takes each shot needed before approval
- `Projects/<slug>/Status.md`, `Review.md` if present
- `Projects/<slug>/Context/Rules.md`: project overrides that may deserve promotion to the Playbook
- `Studio/Playbooks/Default.md`, `Studio/Lessons/` (do not repeat a lesson that already exists; link it)
- `<project>/edit/CUTS.md` and `edit/*.yaml` if present
- The session transcripts are not available; ask the user for anything that only happened in chat (two or three questions at most, asked once).

## Steps
1. Compute the numbers with the CLI, never by hand: `backlot cost --json`, `backlot takes --json`, `backlot status --json`.
2. Build the take funnel per shot: generated → rejected → approved, and the reject reasons grouped by theme (prompt, model, continuity, taste, cost).
3. Compare planned vs actual: budget vs spent, shots planned vs delivered, stage dates from `Decisions.md` if present.
4. Rate each model used: approval rate, cost per approved take, notable failures. Note any model whose note still says `untested` although it was used.
5. Identify friction: places where the ledger shows repeated rejects with the same reason, stale cascades, budget escalations, or provider failures (`backlot takes --status failed`).
6. Ask the user the questions from the Inputs section, if any.
7. Write `Studio/Lessons/<date>-<slug>.md` using the template below.
8. Propose edits, each as a concrete diff-like suggestion with the target file: Playbook rules to add, change or drop; Workflow steps that were skipped or missing; model notes (prompt tips, defaults, tier, status); skill wording that misled the agent. Do not apply them; list them under "Proposed edits" and ask which to apply.
9. Apply the edits the user approves. Commit the vault with `retro: <slug>`.

## Lesson note template
```
---
type: lesson
project: <slug>
date: <YYYY-MM-DD>
budget_eur: <n>
spent_eur: <n>
takes: <n>
approved: <n>
models: [<ids>]
tags: [retro]
---
# Retro: <slug>

## Outcome
One paragraph: what was delivered, against which brief, and whether it met it.

## Numbers
| Metric | Planned | Actual |
|---|---|---|
| Budget (EUR) | | |
| Shots | | |
| Takes per approved shot | | |
| Cost per approved shot (EUR) | | |

## What worked
- Bullets with take or shot IDs as evidence.

## What cost time or money
- Bullets with take or shot IDs, grouped by theme.

## Model verdicts
| Model | Takes | Approved | Cost/approved | Verdict |
|---|---|---|---|---|

## Proposed edits
- `Studio/Playbooks/Default.md`: ...
- `Studio/Workflows/<name>.md`: ...
- `Studio/Models/<id>.md`: ...
- `skills/<name>/SKILL.md`: ...

## Open questions
```

## Outputs
- `Studio/Lessons/<date>-<slug>.md`
- Approved edits applied to Playbooks, Workflows, model notes; skill edits are reported to the user for the dotfiles repo (skills live in `~/dotfiles/agents/video/skills/`, not in the vault)
- A `## Retro` section on the project home note linking the Lessons note

## Gate
The retro is done when the Lessons note exists, every proposed edit has been accepted or declined by the user, and the vault is committed.

## Example phrases
- "run the retro on the launch spot"
- "what did we learn from hello-backlot"
- "/retro"
