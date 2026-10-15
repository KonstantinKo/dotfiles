# Project metrics record

Keep this as a small plain-text attachment to a lesson. Fill values only from cited records. This is a project log, not a model leaderboard.

```markdown
---
type: project-metrics
project: <slug>
period: <start..end or unknown>
source_inventory: <path to inventory or lesson section>
coverage: <complete|partial|unknown>
---
# Metrics: <slug>

## Source inventory
| Source ID/path | Role and date/range | Messages or records in scope | Coverage | Raw tool/provider logs |
|---|---|---|---|---|
|  |  |  |  |  |

| Measure | Numerator (value + native unit) | Denominator (value + native unit and eligible scope) | Result | Evidence | Coverage / unknowns |
|---|---|---|---|---|---|
| Failed paid calls |  |  |  |  |  |
| Unneeded paid calls |  |  |  |  |  |
| Repeated same-defect corrections |  |  |  |  |  |
| User correction rounds |  |  |  |  |  |
| Review-to-submission mismatches |  |  |  |  |  |
| Handoff recovery time |  |  |  |  |  |
| Cost per usable segment |  |  |  |  |  |
| Context and tool volume |  |  |  |  |  |
```

## Recording rules

- Name the event unit and denominator for every rate. For example, “2 failed submissions / 14 registered paid submissions” says more than “14% failed.” Count only the operations covered by the cited source set.
- Count an operation as unneeded only when a record shows it had no delivery-relevant purpose or conflicted with the approved intent. An unsuccessful result alone does not make a call unneeded. Count a user correction round when a presented candidate receives a user-requested correction to agreed criteria; keep new creative direction separate.
- Record actual provider charges in their native unit (`credits`, `USD`, or another provider unit). Keep project-ledger EUR separate. Do not convert currencies or combine account balances without a dated, sourced conversion basis. Estimates are not actual charges.
- For cost per usable segment, define “usable” and the denominator in the row, such as approved segments or delivered seconds. Separate routes and native units; show unknown actual charges separately.
- Count repeated defects only when the same named criterion recurs after it was identified. Record correction rounds and affected outputs; ordinary exploration is not a correction.
- Count a review-to-submission mismatch only when the submitted operation differs from the latest reviewed or authorized inputs. Denominator is the set of submissions whose review/authorization records were available to audit.
- Compute handoff recovery time only from recorded handoff and recovered-state timestamps. Define recovery as locating the active version, latest scoped approval, and open work; report known minutes per handoff and do not estimate from message gaps.
- For context/tool volume, record the source scope: threads and messages read versus available, plus tool events only when a tool log records them. Assistant claims that a tool ran do not establish a complete tool-call count.
- Mark a missing denominator, charge, timestamp, or log `unknown`, with the reason. Do not fill unknowns with zero, infer historic counters, or backfill a guessed total.
- One project may support a dated, route-specific observation. It is insufficient for a stable model ranking. Compare models only after multiple comparable projects and disclose differences in task, route, quality bar, coverage and native cost unit.
