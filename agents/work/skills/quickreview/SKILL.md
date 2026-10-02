---
name: quickreview
description: Independently review a requested diff and verify findings.
disable-model-invocation: true
---

# Quickreview

Review the requested changes with fresh context, then verify findings in the primary session.

## Workflow

1. Determine the scope from the user's request. Otherwise review current working-tree changes and branch-owned commits against their merge base, when applicable.
2. Give an available independent reviewer the goal, constraints, relevant project rules, and exact diff. Use a native subagent or a separate read-only session; keep the reviewer from editing files. Choose a capable reviewer without relying on a particular harness or model.
3. Ask it to find behavioral bugs, regressions, unsafe assumptions, integration risks, and missing tests. Ignore style-only noise.
4. Check each proposed finding against the current code and relevant behavior. Discard false positives. Fix verified issues when reviewing your own implementation or when the user requested fixes, then run focused checks.
5. Report verified findings with file and line, ordered by severity. Mention rejected findings only when useful. If no independent reviewer is available, review directly and say so; do not present that as an independent review.
