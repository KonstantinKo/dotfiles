---
name: dev-env-migrate-router
description: Router Drizzle SQLite migration lifecycle adapted from Opencode migrate-router. Use for devEnv DB schema changes, migration generation/review/apply flow, and router/shared schema verification.
---

# Dev Env Migrate Router

Verify current repo is devEnv before running.

Read `references/opencode-command-migrate-router.md` and follow it exactly where it is not Opencode-specific.

Hard rules:

- schema source is `apps/shared/common/src/db/db.sqlite.schema.ts`
- use `just dbGenerate`; never run raw `drizzle-kit generate`
- review generated SQL before apply
- look for drops, destructive alters, unintended uniqueness changes, and data-loss risk
- use `just dbMigrate` only after SQL review
- run targeted tests/typecheck and broader verification when feasible
