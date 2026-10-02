---
name: babysit-prs
description: Use to sweep my open authored GitHub PRs — auto-fix safe bot-reviewer findings (lint/format/typecheck) with full pre-push verification, resolve addressed bot threads, digest CI/review status. Run with no arg (all open non-draft PRs) or scoped to one PR (number, repo#number, or "current").
user_invocable: true
---

# babysit-prs

Sweep my open authored PRs across `~/projects/platform` and `~/projects/backend`. Auto-fix safe bot findings; also handle human requests within the scope already authorized by the user. Leave human threads for humans to resolve.

## Environment

- `gh` fails when `GITHUB_TOKEN` is set. Prefix every gh call: `GITHUB_TOKEN= gh ...`.
- GitHub user: KonstantinKo. Default branch: `main`. Repos under `~/projects/<repo>`.
- Bot reviewers: CodeRabbit, Copilot.

## Authorization and scope

Explicit invocation authorizes the normal safe fixes, pushes, and review handling described here. Scheduled runs retain their established authorization. Use existing session authorization; prepare concrete fixes/drafts and checks before requesting any missing authorization. Unrelated Slack/Linear announcements require a separate explicit request.

Keep fixes scoped to verified findings. Auto-fix bot lint/format/typecheck/coverage-gate issues only when safe and supported by evidence. Architectural changes, fixes over five files, or persistently failing verification need attention rather than expanding the sweep. Assess human requests against the user-authorized scope; report requests outside it for a decision.

Use conventional atomic commits with no AI attribution. Include hook rewrites; never bypass hooks, force-push, or push to `main`. Accepted/actioned findings are handled silently. Any authorized skipped-finding reply needs a brief reason, file:line evidence, and `(Written by {model name & version} for Konstantin)`. Post no automatic reactions.

## Per-PR steps

1. **Inspect the exact head** — refresh PR metadata and SHA, CI, all unresolved threads, and review bodies (including collapsible bot sections). Pending CI may defer edits this sweep, but still read and assess feedback. Triage infra/flaky failures as blockers.
2. **Verify each finding** — inspect the current head and reproduce or substantiate the claim before accepting or dismissing it. Bot scores are not evidence. Read every unresolved thread; handle authorized human requests too.
3. **Prepare a worktree** — use an existing dedicated PR worktree or create one for the exact PR branch/head. Follow the repository’s full setup checklist: env files, context mirror, dependencies, sync. Preserve primary-checkout and unrelated work; never switch branches in the primary checkout. Verify the PR SHA matches before editing and refresh if it changes.
4. **Fix and review** — apply the verified scoped fix. After an implementation agent reports done, automatically run `code-review` in fresh read-only reviewers separate from implementation, explicitly supplying goal/spec, project instructions, comparison base, and exact scope including uncommitted changes. The primary agent verifies findings, handles fixes, and repeats affected review/checks.
5. **Verify and push** — follow current repository checks, which override the defaults below. Run a CodeRabbit CLI review/fix cycle when available unless its bot already reviewed the current head; read and handle its findings either way. Commit verified changes and push without bypassing hooks. If scope or verification fails, preserve the work and report the blocker.
6. **Refresh after every push** — fetch the exact new PR head, reread every unresolved thread and review body, and verify new or stale findings against it. Resolve addressed bot threads silently, including already-fixed findings whose current code you verified. Reply briefly only to skipped findings under the authorization/footer rules above, then resolve bot threads. Leave human threads for human resolution. Never resolve unread or unaddressed threads.
7. **Assess readiness** — check latest-head repository CI, reviews, and decision gates, and handle newly arriving findings before calling done. Green CI or approval alone is insufficient. An end-to-end ready workflow monitors until its required gates pass; a sweep may report pending checks or waiting human review without claiming readiness.

When three or more PRs need work, fan out one subagent per PR with its exact scope and authorization, then merge the digests.

## Verification defaults

Repository instructions take precedence. Platform uses bun and requires full `bun run verify` plus its architecture/decision gate on the latest head before readiness. Backend uses npm: `npm run typecheck && npm run lint && npm run prettier && npm run test:unit`; integration requires `sst bind`/live AWS and follows repository instructions.

## Digest and monitoring

Report briefly in chat: per-PR CI/head, unresolved threads, review/merge state, fixes, and blockers or waiting humans. For a scoped end-to-end readiness task, continue monitoring through the required gates. Use `/loop` only when supported and recurring monitoring is authorized; a scheduled sweep reports current status and relies on its existing schedule.
