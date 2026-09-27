---
name: dev-env-scan
description: Read-only devEnv scan workflow adapted from Opencode scan/do:scan. Use to front-load docs, shared, frontend, and backend context and write `.project/docs/work/**/scan/**` handoff files before planning or implementation.
---

# Dev Env Scan

Verify current repo is devEnv before running.

## Required Reads

- `AGENTS.md`
- `.project/AGENTS.md`
- `.project/docs/plan/listFormatGuide.md`
- `.project/docs/work/README.md`
- `references/opencode-command-do-scan.md`
- `references/opencode-command-scan.md`
- `references/opencode-agent-scan.md`
- helper refs under `references/opencode-agent-scan*.md`

## Codex Adaptation

- Preserve the Opencode scan semantics from copied refs.
- Spawn four Codex subagents in parallel when possible:
  - `dev-env-scan-docs`
  - `dev-env-scan-shared`
  - `dev-env-scan-frontend`
  - `dev-env-scan-backend`
- Only write `.project/docs/work/**/scan/**`.
- Do not edit product code, docs outside scan output, config, commands, or tests.
- Use `rg` / file reads instead of Opencode `grep`, `glob`, and `read`.

## Output

Write `.project/docs/work/YYYY-MM-DD-topic/scan/result.md` and return only a compact pointer with:

- scan result path
- helper file paths
- blocker status
- next move
