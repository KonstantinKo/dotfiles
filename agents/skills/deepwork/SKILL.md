---
name: deepwork
description: High-cost scheduler workflow for large, high-risk, multi-phase coding efforts likely to cross compaction or span dependent implementation lanes. Do not use for routine multi-file work.
---

# Deepwork

Use Deepwork only when work has meaningful phase dependencies, high partial-change
risk, parallel implementation lanes, or enough duration/context to make compaction
likely. Multiple files alone do not qualify.

Do not use Deepwork for routine features, bounded fixes, ordinary refactors, docs,
or work one capable primary model can complete cleanly in one session.

## Core Contract

When Deepwork is active, primary model is scheduler by default, not default
implementation worker.

- Understand goal, constraints, current repo state, and success evidence first.
- Maintain OpenCode todos for active phase and next concrete action.
- Maintain durable task state under `.agent-work/deepwork/`.
- Draft phased plan before implementation.
- Choose workers by capability and task fit. Do not require named specialist
  personas.
- Delegate bounded implementation lanes with explicit ownership, inputs, outputs,
  and verification.
- Keep dependent work sequential. Parallelize only independent lanes.
- Reconcile worker results before updating shared state or starting dependent work.
- Validate each meaningful phase before continuing.
- Request independent plan or diff review only when findings could materially
  change remaining work. Review is risk-based, not mandatory ceremony.
- Primary model may implement a small integration or corrective edit when another
  handoff would cost more than it protects.
- Finish with final validation, state reconciliation, and concise report.

## Task State

Create one task-specific file:

```text
.agent-work/deepwork/<short-task-slug>.md
```

Keep `.agent-work/` local. Add it to path returned by
`git rev-parse --git-path info/exclude` when needed. Never modify tracked
`.gitignore` or `.ignore` solely for agent state. Explicit file reads work even
when path is ignored.

Use this shape, adapting details to task:

```markdown
# <task>

## Current State
- Goal:
- Scope:
- Constraints:
- Active phase:
- Completed:
- Next action:
- Blockers:
- Validation:

## Confirmed Context

## Decisions

## Phase Plan

## Follow-ups
```

Keep `Current State` authoritative: replace stale claims instead of appending
contradictory status. Append durable decisions and evidence below it. Reference
source files by path rather than copying their full contents.

Update task state after:

- material decisions or scope changes;
- reconciled research;
- phase completion;
- review findings and their disposition;
- validation results;
- blockers or ownership changes.

After compaction, resume, session handoff, or context uncertainty, read task state
before taking action. Keep its path in todo/session summaries so recovery does not
depend on memory.

Task state may disappear when disposable worktree is removed. Before cleanup,
promote truly cross-task facts into proper durable source: project docs, ADRs,
AGENTS.md, issue tracker, or user/project memory. Do not retain completed journals
only as an archive.

## Scheduler Discipline

- Record worker/session IDs and ownership boundaries in task state when useful.
- Do not duplicate same work across workers.
- Do not advance dependent phases while relevant work is running or unreconciled.
- Continue independent work while background lanes run; otherwise yield until
  completion event.
- Keep primary context focused on decisions, accepted findings, integration, and
  verification rather than raw worker output.

## Worktrees

Use `worktrees` skill when isolation or parallel branches are warranted. Keep each
worker inside assigned worktree. Treat `git worktree list` as source of truth.
