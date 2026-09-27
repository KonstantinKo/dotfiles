---
description: Evaluate devEnv feature fit, risks, and handoff phases
agent: plan
---

Evaluate how `$ARGUMENTS` should fit into devEnv. Cover product placement, technical fit, risks, and handoff.

## 0. Skip Detect

Use multi-select `question` to ask which sections are already done:
- Feature restated
- Feature doc placement
- Spec fit
- Route/API placement
- Data model
- Technical fit/RICE
- Pros/cons/risks
- Grill specifics
- Verdict

Skip checked sections. If skipped output is needed but not provided, ask for that output instead of rerunning.

## 1. Understand

Parse input charitably. Extract what, who, why, constraints. Restate in 2-3 sentences.

Research:
- `AGENTS.md`
- `.project/AGENTS.md`
- `.project/docs/repoConventions.md`
- `.project/docs/feature/README.md`
- Matching `.project/docs/feature/<feature>/README.md` when present
- Matching `.project/rules/*.md`
- `apps/router/docs/spec.md` for router/admin/env lifecycle work
- Relevant source files via Grep/Glob
- External official docs if touching Fly.io, Cloudflare Zero Trust, Elysia, Drizzle, Bun, or MCP behavior

## 2. Feature Doc Placement

Identify the feature doc that owns the change:
- `environment-entry-routing`
- `admin-surface`
- `workflow-runs`
- `prompt-runs-mcp`
- `secrets-and-ssh`
- `machine-lifecycle`
- new `.project/docs/feature/<feature>/README.md` if none fits

List docs that should be updated. Do not create ADRs.

## 3. Spec Fit

Map feature to one or more spec areas:
- Entry routes and redirects
- Ownership/access isolation
- Router storage and stack
- Dev VM image/tools
- Preview VM image
- Lifecycle/GC
- Workflows/MCP/Slack/webhooks/timers

List exact acceptance criteria affected.

## 4. Route/API Placement

Decide primary code surface:
- `apps/router/src/entry/entry.routes.ts` for entry route behavior
- `apps/router/src/app.ts` for router app composition
- `apps/shared/common/src/db/db.sqlite.schema.ts` and `apps/router/src/db/db.client.ts` for router persistence
- `apps/router/src/common/common.config.ts` for router env
- `apps/admin/src/routes` and `apps/admin/src/lib` for admin UI behavior
- `apps/shared/common/src` for FE/BE shared schemas
- `apps/templates` for VM image/runner behavior
- `.opencode` and `.project/docs/opencode/README.md` for Opencode workflow/config behavior
- New focused module only when logic is reused or too large for route file

Check invariant: no duplicate route semantics between `apps/router/src/entry/entry.routes.ts` and any legacy `apps/router/src/http.ts`.

## 5. Data Model

Cover tables, columns, indexes, nullable rules, branch/commit semantics, owner isolation, retention fields, and migration need.

## 6. Technical Fit

Cover impacted files, new schemas/endpoints, data flow, external deps, env vars, migration need, test strategy, and deploy risk.

Use lightweight RICE:

| Factor | Rating |
|---|---|
| Reach | most / many / some / few |
| Impact | massive / high / medium / low |
| Confidence | high / medium / low |
| Effort | hours / days / weeks |

## 7. Pros, Cons, Risks

List user value, complexity, access/security risks, data risks, integration risks, test gaps, and mitigations.

## 8. Grill

Run `/grill` rules for unresolved specifics. One `question` at a time.

## 9. Verdict

Use `question` with Strong Fit / Good Fit / Conditional Fit / Poor Fit. Include recommended approach, top risks, and next action.

## 10. Handoff

Output implementation blocks:

```yaml
task: short phase description
scope:
  - path: change summary
decisions:
  - key: choice
docs:
  - path: feature doc/rule doc update
acceptance:
  - [ ] verifiable criterion
```
