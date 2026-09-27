---
description: Launch scan agent for docs, shared, frontend, and backend scan
agent: scan
subtask: true
---

# Do Scan

Scan this request across devEnv docs, shared packages, frontend, and backend:

```text
$ARGUMENTS
```

Optional focus argument is allowed inside `$ARGUMENTS`:

- `--focus docs|shared|frontend|backend|all`
- `focus=docs|shared|frontend|backend|all`
- `focus: <path, symbol, package, or product surface>`

Focus changes scan depth only. The `scan` agent must still spawn all four helpers concurrently.

Return the final `## Scan Result` in nested list format. The `scan` agent must always spawn `scan/scanDocs`, `scan/scanShared`, `scan/scanFrontend`, and `scan/scanBackend`.

The `scan` agent must write `.project/docs/work/YYYY-MM-DD-topic/scan/result.md` and include that path in the final result. Downstream agents should consume that result file path.
