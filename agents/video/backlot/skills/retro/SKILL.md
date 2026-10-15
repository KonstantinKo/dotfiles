---
name: retro
description: Evidence-led retrospective for a Backlot project. Use after delivery or an abandoned production when asked to run a retro, record lessons, or explain what was learned. Reads current project records and relevant local conversation archives, writes a lesson with explicit coverage, and proposes scoped guidance changes.
---

# Retro

## Purpose
Turn a completed or stopped production into a concise record of what happened, what evidence supports it, and which operation-specific behavior should change. One project can support a concrete incident lesson; it cannot establish a stable model ranking.

## Inputs
- `Projects/<slug>/<slug>.md`, `Status.md`, `Costs.md`, `Delivery.md`, and any current handoff or current-delivery pointer. Record which files were read and their dates or revisions.
- `Decisions.md`, registered operation/take records, project manifests, and saved request/result files. Include external-provider calls and accepted local derivatives when registered; identify unregistered work as a coverage gap.
- Relevant local conversation exports or session archives. Search by project name/slug, production dates, asset IDs and known thread titles. Use an existing source index when available; do not assume transcripts are unavailable.
- `Projects/<slug>/Takes/*.md`, `Shots/*.md`, edit records, and `Context/Rules.md` when present.
- `Studio/Playbooks/Default.md`, `Studio/Lessons/`, applicable workflows and model notes. Reuse a relevant lesson instead of copying its rule.

## Source discovery and coverage
Before asking the user to repeat a decision or approval:

1. Inspect the project and artifact roots for handoff notes, archives, transcript exports, request manifests, delivery records and current pointers. Search only conversations relevant to this project and period; do not scan unrelated personal history.
2. Read the relevant exports and record a compact inventory: source path or ID, thread/title, date range, message count or range when known, coverage (`complete`, `partial`, `supporting`, or `unknown`), and whether raw tool/provider logs are included.
3. Reconcile the latest scoped user approval, current delivery/version, accepted limitations and open decisions across the current handoff, project records and relevant archives. Preserve the original message reference and scope. An old approval is evidence of that old scope; it does not authorize a changed call.
4. Ask only about facts still missing after this search. State the missing evidence and why it matters. Do not ask the user to repeat a decision already present in an archive.

Separate user-authored decisions and delivery records from derived views. A current `Delivery.md` or `currentDelivery` pointer can be richer than a legacy stage tracker; retain the exact selected version and report a conflict for review instead of replacing it with an incomplete projection. Do not alter `Delivery.md`, `Status.md`, `Costs.md`, project status, approval records, or delivery pointers during inspection.

`backlot status` and `backlot cost` currently regenerate vault projections; `cost` also updates `spent_eur` on the project home. Do not run them as retrospective read commands. Read the existing files and authoritative ledgers/manifests, or use a documented read-only query if one is available. State the inspected CLI/runtime version and coverage. If a registered route, conversation, or provider log is missing, label the result as partial; never present registered-only totals as whole-project totals.

## Steps
1. Resolve the project and build the source/coverage inventory above.
2. Read the existing projections and underlying records without refreshing them. Compare the active delivery pointer and current project status/cost with the source records; report mismatches without writing them back.
3. Derive only reproducible counts and totals from the available records, including registered external-provider work and local derivatives. Keep estimate, actual charge, project-ledger allocation and provider-native units separate. Use the [metrics record](references/metrics-record.md); mark unsupported values `unknown`.
4. Describe the take or operation funnel only where the source set is complete enough to define its denominator. Group observed failures by operation and evidence. Missing logs mean unknown cause or incomplete coverage, not zero failures.
5. Identify friction and useful behavior with concrete IDs, message references, timestamps, paths or timecodes. Separate recorded facts from interpretation.
6. Write one lesson with one changed behavior and a small counterexample. Scope it to the operation and optional branch where it applies. Put the durable rule in one best home; link that dated evidence from model or skill guidance only when it informs that guidance. Reuse existing robust rules instead of restating them.
7. List proposed edits as concrete diffs with target files. Do not apply proposed Playbook, Workflow, model-note or skill edits until the user selects them.
8. Add a `## Retro` link on the project home only when writing the lesson has been requested and the current home note is safe to edit. Commit the vault only when the user’s task includes a commit.

## Lesson note template
```markdown
---
type: lesson
project: <slug>
date: <YYYY-MM-DD>
coverage: <complete|partial|unknown>
sources: [<source ids or paths>]
tags: [retro]
---
# Retro: <slug>

## Outcome
What was delivered or stopped, against which brief, with the exact current version and approval evidence when known.

## Evidence and coverage
List the source inventory and material gaps. Distinguish recorded facts from inference.

## Metrics
Link or embed `metrics.md`; leave unsupported values unknown. Keep provider-native charges, project currency and denominators explicit.

## What worked
- <operation-specific result> — <evidence reference>.

## What cost time or money
- <operation and observed issue> — <evidence reference; cause unknown if unsupported>.

## Model observations
| Model and route | Operation | Evidence / coverage | Observed result | Limit |
|---|---|---|---|---|

## Lesson
- Behavior to change: <one concrete check, template, or runtime behavior>.
- Counterexample: <nearby case where this rule does not apply>.
- Evidence/date: <source refs; YYYY-MM-DD>.

## Proposed edits
- `<path>`: <specific change and reason>.

## Open questions
- <only a genuine evidence gap>
```

## Outputs
- `Studio/Lessons/<date>-<slug>.md` with source coverage and a scoped lesson.
- A metrics record when project evidence supports one; unknowns remain explicit.
- Proposed guidance changes with evidence links and one appropriate home each.

## Gate
The retrospective is ready for review when its sources, gaps, delivered version, metrics units and evidence-bound lesson are visible. User-selected guidance changes and vault commits are separate actions.

## Example phrases
- “run the retro on the launch spot”
- “what did we learn from hello-backlot”
- “/retro”
