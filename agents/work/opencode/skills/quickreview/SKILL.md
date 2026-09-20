---
name: quickreview
description: Independent fresh-context review of current changes. Use when user says quickreview, asks for review after edits, or requests validation from another context.
---

# Quickreview

Review changes from fresh context, then verify findings in primary session.

## Workflow

1. Determine exact review scope: working tree, branch merge-base diff, commit, or
   user-specified files.
2. Gather concise context: goal, constraints, diff, relevant tests, project rules.
3. Start independent read-only review with a fresh `opencode run --agent plan`
   session using a deliberately chosen capable model.
4. Ask for behavioral bugs, regressions, unsafe assumptions, integration risks,
   and missing tests. Reject style-only noise.
5. Validate every finding against current code and project context.
6. Fix only verified issues when review follows own implementation or user asks.
7. Rerun targeted checks after fixes.

Independent reviewer should not edit files. Primary session owns disposition,
edits, and final report.

Report verified findings first. Mention rejected findings only when useful.
