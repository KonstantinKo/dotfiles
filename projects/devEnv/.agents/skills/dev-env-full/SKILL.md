---
name: dev-env-full
description: Slow full devEnv workflow adapted from Opencode full. Use for substantial feature or cross-surface work needing scan evidence, flow placement, grill decisions, persisted planBehaviorTree.md, build/review packets, verification, and docs checks.
---

# Dev Env Full

Use this in `/Users/konstantin/projects/devEnv` for substantial changes. Do not use for quick narrow edits; use `dev-env-fast-full` instead.

Before work, verify the repo root has `AGENTS.md`, `.project/AGENTS.md`, and `apps/router/docs/spec.md`. If not, stop.

## Required Reads

Read these first:

- `AGENTS.md`
- `.project/AGENTS.md`
- `.project/docs/repoConventions.md`
- `.project/docs/opencode/README.md`
- `.project/rules/opencode.md`
- `.project/docs/plan/listFormatGuide.md`
- `.project/docs/work/README.md`
- `apps/router/docs/spec.md`
- `apps/router/docs/elysiaJs/research.md`

Read copied source refs as phase detail:

- `references/opencode-agent-full.md`
- `references/opencode-command-full.md`
- `references/opencode-command-do-full.md`
- `references/opencode-command-tdd-full.md`
- `references/opencode-command-grill.md`
- `references/opencode-agent-scan.md`
- `references/opencode-agent-doFlow.md`
- `references/opencode-agent-competitorResearch.md`
- `references/opencode-agent-buildTask.md`
- `references/opencode-agent-reviewTask.md`
- `references/opencode-agent-playwright.md`

## Codex Adaptation

- Preserve the referenced Opencode workflow semantics unless this file says otherwise.
- Treat Opencode `task` as explicit Codex subagent spawning.
- Use custom agents `dev-env-scan-*`, `dev-env-build-task`, `dev-env-review-task`, and `dev-env-playwright` where the Opencode refs name scan/build/review/playwright subagents.
- Use web search only when current external evidence is required; cite URLs in persisted work docs.
- Replace Opencode restart notes with: start a new Codex session after editing personal skills, prompts, custom agents, MCP, hooks, or rules.
- Keep every durable handoff file-backed under `.project/docs/work/YYYY-MM-DD-topic/`.

## Phase Contract

Start every user-facing response during this workflow with:

```text
CRITICAL PHASE INDICATOR: full.phase=<phaseId> status=<not-started|in-progress|blocked|complete> next=<nextPhaseId-or-none>
```

Use only these phase IDs:

- `0-intake`
- `1-scan`
- `2-flow`
- `3-grill-decisions`
- `4-plan-behavior-tree`
- `5-baseline`
- `6-tests-red-gate`
- `7-implementation`
- `8-verify-review`
- `9-completion`

## Workflow

Follow the full workflow from `references/opencode-agent-full.md` with Codex tool names. Key invariants:

- derive one `YYYY-MM-DD-topic` session slug
- write scan, flow, optional research, and plan artifacts under that folder
- maintain `.project/docs/work/YYYY-MM-DD-topic/plan/planBehaviorTree.md`
- freeze the plan after Phase 4 unless user-approved scope changes are required
- delegate implementation packets to `dev-env-build-task`
- delegate packet review to `dev-env-review-task`
- use functional tests through public interfaces
- leave changes unstaged unless explicitly asked

Never commit unless explicitly asked.
