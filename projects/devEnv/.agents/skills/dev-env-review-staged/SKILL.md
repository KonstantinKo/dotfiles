---
name: dev-env-review-staged
description: Staged diff review workflow adapted from Opencode review-staged. Use to review only staged devEnv changes for bugs, regressions, missing tests, spec violations, auth/isolation issues, DB/migration risk, and docs gaps.
---

# Dev Env Review Staged

Verify current repo is devEnv before running.

Read `references/opencode-command-review-staged.md` and follow it with Codex review stance.

Review only staged changes. Findings first, ordered by severity, with file/line references. If no serious findings, say so and list residual test risk.

Do not modify files unless the user asks for fixes.
