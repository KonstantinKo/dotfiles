---
description: Slow, diligent full devEnv workflow with scan, flow, grill, implementation, verify, and review
agent: full
---

# Full Orchestrator

Run the full feature workflow for this request:

```text
$ARGUMENTS
```

Use the `full` primary agent. First, before scan/flow/planning, ask whether to work in place or use a new worktree unless `$ARGUMENTS` already says. If a new worktree is used, the worktree branch/path must use the exact same `YYYY-MM-DD-topic` slug as `.project/docs/work/YYYY-MM-DD-topic/`. Then phase through intake, scan, flow, and decision grilling. After grill, stop routine questions: auto-freeze the plan, use tests-alongside unless Strict TDD was explicitly requested, snapshot unrelated baseline failures, implement/repair/review until completion, leave changes unstaged unless the user explicitly asked for staging, and ask only true blockers such as destructive action, credentials, security/privacy risk, new scope/acceptance, unresolved schema/API/data decisions, or unrecoverable verification failure. Every response must start with `CRITICAL PHASE INDICATOR: full.phase=<phaseId> status=<status> next=<nextPhaseId-or-none>`.
