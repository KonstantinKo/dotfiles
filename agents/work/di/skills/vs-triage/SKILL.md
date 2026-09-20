---
name: vs-triage
description: Use when asked to triage the Video Studio alpha/beta feedback queue ("/vs-triage", "triage the content creation queue", "run the alpha triage again") — sweeps the Content Creation Linear triage state fed from #video-studio-alpha-feedback, closes duplicates, investigates and accepts bugs into Video Studio · Beta release, and refreshes the shared feature-review artifact; second mode applies the meeting decisions recorded on that artifact back to Linear.
user_invocable: true
---

# vs-triage

Repeatable sweep of the Content Creation triage queue for Video Studio (`apps/lesson-editor`). Two modes; pick from the argument or ask in one line.

- `sweep` (default): process every ticket that is still in Triage and not yet in the ledger.
- `apply`: read the decisions recorded on the review artifact and act on them in Linear.

## Fixed references

- Linear team **Content Creation** (id `792bdf8d-f606-40ad-a27b-bbeef689dee5`), project **Video Studio**, milestone **Beta release**. Accepted state is `Ready for Development` (the team's "To Do"). Declined = `Canceled`. Duplicate = set `duplicateOf` (Linear then moves it to `Duplicate` automatically; setting the state first fails).
- Slack channel `#video-studio-alpha-feedback` = `C0BUSV0N40H`. The bug-report bot posts each report; a `:ticket:` reaction makes Linear Asks create the ticket. Messages without a ticket are still feedback: list them in the artifact, and file a ticket yourself when one is a bug.
- Ledger: `~/projects/obsidian/agentdesk/content-studio/alpha-triage/LEDGER.md` (processed ids, artifact URL, open decisions). Read it first, append to it last.
- Review artifact: URL in the ledger. Republish with `url` so the link stays stable; decisions live in its `db` under collection `decisions`, doc id = ticket id (`{decision: act|skip|later|discuss, note, updatedAt}`).
- Every Linear comment or issue body you write ends with `(Written by {model name & version} for Konstantin)`, e.g. `(Written by Claude Fable 5.1 for Konstantin)`.

## sweep

1. `list_issues` team Content Creation, state `triage`, fields `id,title,description,createdAt,triageIntel`. Output is large; dump to a scratch file and read it with python, never inline. Skip ids already in the ledger. Ignore pre-alpha backlog items (created before the alpha, no Video Studio context) unless asked.
2. Read the Slack channel (also to a file). For each report note reporter, env commit, page, thread replies (a teammate may already have answered or linked an existing ticket), and reports without a `:ticket:` reaction.
3. Pull the last 100 lesson-editor commits and the CC tickets created in the same window (`createdAt` filter, all states) to spot fixes and existing tickets.
4. Classify each ticket: duplicate · praise/no action · bug · feature · mixed. **Bug means existing behaviour that should have worked from what is already there** (a control that does nothing, wrong output, a crash, a regression). Anything the product does not do yet is a feature request, even when the tester reasonably expected it: state kept after navigating back, editing something that has no edit control, files-only input, an ETA on a step that never had one. Konstantin corrected this on 10 Sep after CC-897, CC-859 and CC-863 were filed as bugs. When in doubt: feature, into the deck. Check the Triage Intelligence `relatedIssue` suggestions and the existing ticket list before calling anything new.
5. Bugs: investigate in parallel with read-only Explore agents on `main` (no worktree needed, nothing is edited). Ask each for finding, root cause, file:line refs, already-fixed?, fix, effort S/M/L, max ~400 words per item. Post the result as a comment, then `save_issue` with state Ready for Development, project, milestone, priority, labels (`Bug` + `Editor`/`Wizard`), `relatedTo` where useful. Priority: High for data loss, blocked export/flow, silent wrong output; Medium default; Low for cosmetics.
6. Mixed tickets: create a sub-issue (`parentId`) for the bug half with the investigation in its body and accept it; leave the parent in Triage with a "Triage split" comment; the feature half goes to the artifact.
7. Features: leave in Triage, add a short "Triage prep" comment when code findings exist, and add to the artifact with demand (names), fit 1–5, effort, confidence, recommendation, quotes, findings, proposal.
8. Republish the artifact (same URL). Append processed ids and the new features to the ledger. Log loose ends to the agentdesk per PRODUCER.md.

## apply

1. `read_db` on the artifact (`collection: decisions`, `db_op: list`).
2. `act` → create a real ticket (or move the triage ticket) into Video Studio · Beta release · Ready for Development with the proposal as body and the note; `skip` → comment the reason and set `Canceled`; `later` → comment and set `Needs Clarification`, or leave in Triage if told to; `discuss` → leave and list in the summary.
3. Update the ledger's decision table and report what changed.
