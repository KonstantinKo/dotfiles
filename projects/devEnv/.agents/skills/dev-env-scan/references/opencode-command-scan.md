---
description: Front-load devEnv context before implementation
agent: build
---

Front-load context for work about to happen. Discover dynamically; do not trust hardcoded assumptions.

## Scope

If `$ARGUMENTS` is empty, scan current devEnv repo. If non-empty, restrict to paths or concepts matching the argument.

Known router app shape:
- `apps/router/src/app.ts`: Elysia app composition
- `apps/router/src/index.ts`: Bun entrypoint
- `apps/router/src/entry/entry.routes.ts`: entry routes
- `apps/router/src/common/common.config.ts`: env config via Zod
- `apps/shared/common/src/db/db.sqlite.schema.ts`: Drizzle SQLite schema
- `apps/router/src/db/db.client.ts`: Bun SQLite client
- `apps/router/drizzle/`: generated migrations
- `apps/router/docs/spec.md`: product acceptance criteria
- `.project/docs/feature/`: feature-first docs
- `.project/rules/`: scoped rules

## Discovery

Glob relevant files:
- Router features: `apps/router/src/**/*.routes.ts`, `apps/router/src/**/*.service.ts`, `apps/router/src/**/*.helper.ts`
- App/bootstrap: `apps/router/src/app.ts`, `apps/router/src/index.ts`, `apps/router/src/http.ts`
- DB: `apps/router/src/db/**/*.ts`, `apps/router/drizzle/**/*.sql`, `apps/router/drizzle/meta/*.json`
- Admin: `apps/admin/src/routes/**/*`, `apps/admin/src/lib/**/*`
- Shared contracts: `apps/shared/common/src/**/*.ts`
- Templates/runners: `apps/templates/**/*`
- Opencode: `opencode.json`, `.opencode/commands/**/*.md`, `.opencode/agents/**/*.md`
- Config: `package.json`, `tsconfig.json`, `apps/router/drizzle.config.ts`, `biome.json`, `lefthook.yml`
- Docs: `apps/router/docs/**/*.md`, `.project/docs/**/*.md`, `.project/rules/**/*.md`, `AGENTS.md`, `.project/AGENTS.md`

Always read:
- `AGENTS.md`
- `.project/AGENTS.md`
- `.project/docs/repoConventions.md`
- Relevant `.project/docs/feature/<feature>/README.md` when available
- Relevant `.project/rules/*.md`
- `apps/router/docs/spec.md`
- Relevant source files
- `apps/router/docs/elysiaJs/research.md` for router route/app work

## Parallelism

For broad scans, use 2-3 `task` explore agents by layer. Each returns summary, not raw dumps. For narrow scope, direct Glob/Grep/Read is enough.

## Output

### Shape

| Layer | Count | Key items |
|---|---:|---|
| Routes | n | groups |
| DB | n | tables/migrations |
| Config | n | scripts/tooling |
| Docs | n | relevant sections |

### Conventions Detected

List naming, validation, route, DB, migration, UI, docs, Opencode, and test patterns. Flag divergence from `AGENTS.md`, `.project` docs/rules, or `apps/router/docs/spec.md`.

### Risks

List stale docs, duplicate route semantics, missing auth isolation, migration risk, env/secret risk, and test gaps.
