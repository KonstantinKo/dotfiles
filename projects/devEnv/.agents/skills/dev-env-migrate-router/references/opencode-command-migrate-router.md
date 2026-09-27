---
description: Handle router app Drizzle SQLite migration lifecycle through package wrappers
agent: build
---

Handle router app Drizzle migration for `$ARGUMENTS` in devEnv.

## 1. Determine Target

Current migration setup:
- Schema: `apps/shared/common/src/db/db.sqlite.schema.ts`
- Drizzle config: `apps/router/drizzle.config.ts`
- Migration dir: `apps/router/drizzle/`
- Generate wrapper: `just dbGenerate` from repo root
- Apply wrapper: `just dbMigrate` from repo root

Never run raw `drizzle-kit generate`. Use root wrappers.

## 2. Check Scope

Read `AGENTS.md`, `.project/AGENTS.md`, `.project/rules/router.md`, `.project/docs/architecture/router.md`, `.project/docs/architecture/shared.md`, matching feature docs, `apps/router/docs/spec.md`, `apps/shared/common/src/db/db.sqlite.schema.ts`, and `apps/router/drizzle.config.ts`.

Hard constraints:
- SQLite storage on Fly.io Volume.
- Every environment has one owner.
- Preview dedupe needs owner/repo/sourceCommit uniqueness.
- Empty repo stores `repo` as `null`.
- GC uses environment type and suspended state.

If `$ARGUMENTS` implies auth, owner, dedupe, or GC behavior, map affected spec criteria before editing schema.

## 3. Edit Schema

Make smallest table/index changes. Keep persisted fields explicit and match spec terms: `ownerId`, `type`, `repo`, `sourceBranch`, `sourceCommit`, `machineId`, `status`, `deleteAfter`.

## 4. Generate

Run:

```bash
just dbGenerate
```

## 5. Review SQL

Read generated `apps/router/drizzle/**/*.sql`. Check:
- `DROP TABLE`, `DROP COLUMN`, destructive table rebuild
- Data loss risk
- Index/unique constraint correctness
- SQL matches intended schema
- Spec invariants still hold

Use `question` before applying:
- Approve apply
- Edit schema and regenerate
- Abort and remove generated migration

For destructive SQL, use normal prose warning, not caveman compression.

## 6. Apply Dev Migration

After approval:

```bash
just dbMigrate
```

## 7. Validate

Run:

```bash
just verify
```

Report generated migration path and risks.
