---
name: babysit-prs
description: Use to sweep my open authored GitHub PRs — auto-fix safe bot-reviewer findings (lint/format/typecheck) with full pre-push verification, resolve stale threads, digest CI/review status. Run with no arg (all open non-draft PRs) or scoped to one PR (number, repo#number, or "current").
user_invocable: true
---

# babysit-prs

Cleanup pass over my open authored PRs across `~/projects/platform` and `~/projects/backend`. Auto-fix only SAFE bot findings. Never touch human comments.

## Environment

- `gh` CLI fails when `GITHUB_TOKEN` is set. Prefix EVERY gh call: `GITHUB_TOKEN= gh ...`
- GitHub user: KonstantinKo. Default branch: `main`. Repos under `~/projects/<repo>`.
- Bot reviewers: CodeRabbit, Copilot.
- Linear via MCP (`mcp__claude_ai_Linear__*`), Slack via MCP (`mcp__claude_ai_Slack__*`).

## Verify commands (per repo)

| Repo | Pre-push verify (auto-fix gate) |
|---|---|
| platform | `bun run check && bun run lint && bun run test:unit` |
| backend | `npm run typecheck && npm run lint && npm run prettier && npm run test:unit` |

- platform = **bun**, backend = **npm**. Don't cross them.
- NEVER run backend integration tests in auto-fix — they need `sst bind` / live AWS session. Unit only.
- Detect repo from the PR's repo / branch checkout path; pick the matching row.

## Safety rails (absolute)

- Never auto-fix or reply to HUMAN review comments — forward them to me in the digest.
- Never `--no-verify`. Never force-push. Never push to `main`. One logical fix per commit, conventional, no AI attribution.

## Per-PR steps

1. **CI** — `GITHUB_TOKEN= gh pr checks <pr>`. Pending → skip auto-fix this round. Failed → triage: only lint/format/typecheck/coverage-gate issues are auto-fixable; infra/flaky → record as blocker.
2. **Fetch findings** — open review threads via GraphQL AND bot review bodies (CodeRabbit/Copilot post findings in collapsible review-body sections, not just inline threads — fetch both).
3. **Score** each thread/finding 1–10 on correctness, security, convention adherence, specificity. HARD RULE: human comments never auto-fixed, never replied to — forward to me. Only BOT findings scoring 7+ are auto-fixed.
4. **Auto-fix path** — in the repo dir, checkout the branch, apply the change, run the repo's pre-push verify (table above), commit (conventional, no AI attribution, one logical fix), push. Never `--no-verify`, never force-push, never push to `main`. React 👍 and resolve the bot thread. If the fix exceeds scope (>5 files, architectural, or verify keeps failing) → abort, add to "needs attention".
5. **Stale threads** — resolve ones pointing at already-fixed code, silently, no reply.

When 3+ PRs: fan out one subagent per PR in parallel, each scoped to its PR, then merge into one digest.

## Digest

End with a plain-text digest in chat: per-PR CI / open threads / merge state, what was auto-fixed, what needs my attention, blockers.

When scoped to a single PR and CI isn't green yet: self-reschedule via `/loop` to keep watching until green or merged.
