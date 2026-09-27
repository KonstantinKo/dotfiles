---
description: Launch fastFull for quick current-worktree implementation with one brief search, optional playwright delegation, and tests after
agent: fastFull
---

# Do Fast Full

Run the fast full workflow for this request:

```text
$ARGUMENTS
```

Use the `fastFull` primary agent. Always work in the current branch/worktree. Do one `fastFull/briefSearch` discovery pass, skip product flow and formal planning, allow product questions about user-visible behavior/scope, never ask test/process questions by default, implement directly, delegate browser checks to `playwright` when useful, never call Playwright MCP tools directly, then run targeted tests/checks after the implementation. Do not commit unless explicitly asked.
