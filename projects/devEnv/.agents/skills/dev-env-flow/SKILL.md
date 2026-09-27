---
name: dev-env-flow
description: devEnv flow/planning gate adapted from Opencode doFlow. Use after scan evidence to evaluate product fit, placement, risks, verdict, grill seeds, and implementation handoff, writing `.project/docs/work/**/flow/result.md`.
---

# Dev Env Flow

Verify current repo is devEnv before running.

## Required Reads

- `AGENTS.md`
- `.project/AGENTS.md`
- `.project/docs/plan/listFormatGuide.md`
- `.project/docs/work/README.md`
- `.project/docs/repoConventions.md`
- `.project/docs/feature/README.md`
- `apps/router/docs/spec.md`
- `references/opencode-command-do-flow.md`
- `references/opencode-command-flow.md`
- `references/opencode-agent-doFlow.md`

## Codex Adaptation

- Preserve the Opencode `doFlow` semantics from copied refs.
- Use `dev-env-scan` when scan evidence is absent and the user allows scan.
- Use `dev-env-competitor-research` when research is required.
- Only edit `.project/docs/work/**/flow/**`.
- Cite material claims with scan evidence, exact file paths, exact docs/rules, explicit user input, or cited external URLs.

## Phase Contract

Start every user-facing response during this workflow with:

```text
CRITICAL PHASE INDICATOR: doFlow.phase=<phaseId> status=<not-started|in-progress|blocked|complete> next=<nextPhaseId-or-none>
```

Use phase IDs from `references/opencode-agent-doFlow.md`.

## Output

Write `.project/docs/work/YYYY-MM-DD-topic/flow/result.md`. Chat response should be a compact pointer, not the full result.
