---
name: dev-env-workflow-report
description: Write devEnv workflow-authored primary HTML reports. Use when a devEnv workflow prompt asks Codex to create `primary-report.html` at the exact runner-provided path.
---

# Dev Env Workflow Report

Copied from the team workflow report skill. Follow the original unless the runner prompt is stricter:

- Write the report only to the exact path provided in the workflow prompt.
- Do not create fallback reports.
- Keep reports self-contained.
- Include enough context for a human to inspect the run later.

Reference: `references/team-workflow-report-SKILL.md`.
