---
name: workflow-report
description: Write workflow-authored primary HTML reports in devEnv runs.
---

Use this skill when a workflow asks for a primary HTML report.

Rules:

- Write the report only to the exact path provided in the workflow prompt.
- Do not create fallback reports.
- Keep reports self-contained.
- Include enough context for a human to inspect the run later.
