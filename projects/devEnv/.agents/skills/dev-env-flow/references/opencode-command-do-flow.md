---
description: Launch doFlow agent for scan-dependent fit, risk, verdict, and handoff planning
agent: doFlow
---

# Do Flow

Evaluate fit, placement, risks, verdict, and handoff for this request and scan evidence:

```text
invocationMode: primary

$ARGUMENTS
```

Write the final `## Flow Result` to `.project/docs/work/YYYY-MM-DD-topic/flow/result.md` and return only the result path, recommended user action, and consuming-agent task. The `doFlow` agent must not perform scan work directly; missing scan evidence may only be obtained by invoking `/do:scan` through a subagent task.

Every `doFlow` response must start with `CRITICAL PHASE INDICATOR: doFlow.phase=<phaseId> status=<status> next=<nextPhaseId-or-none>`. Initial phases are normalization, scan, then competitor research when needed.
