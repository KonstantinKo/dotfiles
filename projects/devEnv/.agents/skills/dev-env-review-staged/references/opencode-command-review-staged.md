---
description: Review staged changes using devEnv spec checklist
agent: plan
subtask: true
---

Review staged changes only. Run `git diff --cached --stat` and `git diff --cached` first. If nothing is staged, say so and stop.

## Research

Before findings, read only relevant docs:
- `AGENTS.md`
- `.project/AGENTS.md`
- `.project/docs/repoConventions.md`
- Relevant `.project/docs/feature/<feature>/README.md`
- Relevant `.project/rules/*.md`
- `apps/router/docs/spec.md` for router/admin/env lifecycle changes
- `apps/router/docs/elysiaJs/research.md` for router/server changes
- Relevant code via Grep/Glob

## Checklist

Report actual issues only: bugs, regressions, security/access problems, data-loss risks, spec violations, missing tests, or tooling breakage.

Docs checks:
- Feature behavior, data shape, access rules, workflow boundaries, or Opencode workflow changes update matching `.project/docs/feature/**` or `.project/docs/opencode/README.md`.
- No ADR folder/files are introduced.
- Docs do not contain secrets, raw tokens, raw JWTs, cookies, private keys, or sensitive user answers.

Spec checks:
- Entry route formats match `apps/router/docs/spec.md`.
- Empty repo sentinel `-` stores as `null` and preview creation rejects it.
- Branch routes resolve to latest commit before create/dedupe.
- Preview envs dedupe by resolved commit; dev envs do not dedupe.
- `sourceBranch` and `sourceCommit` remain separate.
- Generated prefix stays <= 63 chars.
- Environment ownership and access isolation are enforced.
- GC only deletes suspended envs and uses dev/preview retention.

Stack checks:
- Bun package manager only.
- TypeScript strictness preserved.
- Zod validates env, route params, query, request/response data.
- Drizzle SQLite schema/migrations match intent.
- Raw `drizzle-kit generate` avoided; use `just dbGenerate` from repo root.
- Biome/Lefthook config remains intact.

Security/data checks:
- No cross-user environment access.
- Cloudflare Zero Trust user data is treated as auth source for now.
- Generated migration SQL has no unintended destructive operation.
- Secrets stay out of tracked files.

## Output

Findings first, ordered by severity, with `file:line` refs. One line per issue. If no findings, state that and mention real residual test gaps only.
