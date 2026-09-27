---
description: Resolve a devEnv feature idea through an adversarial requirements interview
agent: plan
---

Interview user about `$ARGUMENTS` until every material decision is resolved. Adversarial: find gaps before code.

## Research First

Before asking:
- Read `AGENTS.md`
- Read `.project/AGENTS.md`
- Read `.project/docs/repoConventions.md`
- Read relevant `.project/docs/feature/<feature>/README.md`
- Read matching `.project/rules/*.md`
- Read `apps/router/docs/spec.md` for router/admin/env lifecycle work
- Read relevant source files via Grep/Glob
- Read `apps/router/docs/elysiaJs/research.md` for router/server choices

If a question is answerable from code/docs within a few minutes, answer it yourself.

## Rules

- One `question` at a time.
- 2-4 concrete options per decision.
- Never ask vague/open-ended decision prompts unless custom answer is essential.
- Use exact project terms and paths.
- Print compact running decision tree before each new question.
- Do not advance to next branch until current branch is resolved.
- Assume the user isn't intimately familiar with the code base and your preexisting thoughts about the feature. Give a rundown explanation about the context and background of the decision.
- Give a reasoned recommendation for one of the answer options.
- Give an estimation how many questions remain in the current cycle.

## Coverage

Cover relevant areas:
- Feature doc owner and docs to update
- Repo area: router app, admin app, shared contracts, templates, workflows
- Entry flow: dev/preview, branch/commit, empty repo sentinel, optional title.
- Redirect/generation: prefix format, 63-char limit, generated subdomain.
- Repo/ref resolution: branch to commit, partial commit, missing refs.
- Dedupe: preview by resolved commit, dev uniqueness.
- Auth/access: Cloudflare Zero Trust user data, owner isolation.
- DB: Drizzle schema, indexes, migrations, SQLite constraints.
- Fly.io: app/machine lifecycle, volume, backups, deploy risk.
- Dev VM tools: code-server, Opencode, tmux, Docker, status app, SSH.
- Preview VM tools: minimal Docker/Docker Compose image.
- Lifecycle: suspended status, retention, GC.
- Webhooks/timers/Slack/MCP/custom workflows where relevant.
- Error/empty/loading states and observability.
- Tests and verification commands.
- v1 cut list: explicitly defer nonessential scope.
- Decision log entries for the feature doc; no ADRs.

Hard stops:
- No cross-user access.
- No tracked secrets.
- No raw `drizzle-kit generate`.
- No deploy/destructive migration without explicit approval.
- No ADR folder/files; feature docs own decisions.

## Adversarial Review

After branches resolve, spawn `task` with `subagent_type: general`:

```text
You are a staff engineer reviewing this devEnv feature spec adversarially. Find missed edge cases, conflicting decisions, hidden dependencies, security/access gaps, data-loss risks, testing gaps, and spec violations. Return numbered follow-up questions with why each matters. Return empty list if complete.

Spec: <decision tree>
Context: <relevant docs/code summary>
```

If questions return, ask them one by one with `question`, fold answers into tree, and repeat adversarial review up to 2 times.

## Handoff

When complete:

```yaml
task: one-line description
scope:
  - path: change summary
decisions:
  - key: chosen option
docs:
  - path: feature doc/rule doc update
acceptance:
  - [ ] verifiable criterion
open_questions: []
```
