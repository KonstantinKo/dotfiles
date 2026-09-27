---
description: Debug devEnv issue by tracing root cause and presenting fix options
agent: build
---

Debug `$ARGUMENTS` for devEnv. Parse charitably; user often dictates.

## 1. Restate

Restate issue in one sentence. If truly ambiguous, ask one clarifying `question` before proceeding.

## 2. Locate

Use Grep/Glob first. Map likely scope:
- Router entry routes: `apps/router/src/entry/entry.routes.ts`, `apps/router/src/app.ts`, `apps/router/src/http.ts`
- Router config/env: `apps/router/src/common/common.config.ts`, `apps/router/drizzle.config.ts`
- Router DB/schema: `apps/router/src/db/**/*.ts`, `apps/router/drizzle/**`
- Admin UI: `apps/admin/src/routes/**/*`, `apps/admin/src/lib/**/*`
- Shared contracts: `apps/shared/common/src/**/*.ts`
- Tooling: `package.json`, `tsconfig.json`, `biome.json`, `lefthook.yml`
- Product/spec: `apps/router/docs/spec.md`

Before touching scoped code, read `AGENTS.md`, `apps/router/docs/spec.md`, and relevant files.

For broad or feature-level bugs, also read `.project/AGENTS.md`, `.project/docs/repoConventions.md`, matching feature docs, and matching `.project/rules/*.md`.

## 3. Trace

Start from exact file:line, stack frame, failing command, or error string. Trace upstream caller and downstream dependency. Identify root cause, not symptom.

Check constraints:
- Bun runtime/package manager only.
- Elysia route composition remains coherent.
- Zod validation covers env/route/query/request data.
- Drizzle SQLite schema and migrations match intent.
- Owner isolation remains enforced for environment access.
- No raw `drizzle-kit generate`; use `just dbGenerate` from repo root.
- Secrets stay out of tracked files.

## 4. Fix Options

Unless user explicitly asked for direct repair, use `question` with:
- Root cause
- Option A (Recommended): smallest correct fix, tradeoff
- Option B: alternative, why weaker
- Optional Option C: defer/investigate if evidence incomplete

After choice, implement smallest correct fix, then run narrow check and `just verify` when feasible.
