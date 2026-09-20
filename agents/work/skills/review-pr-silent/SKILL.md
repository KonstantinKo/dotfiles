---
name: review-pr-silent
description: Use when asked to review a colleague's PR ("review this PR", "what do you think of X's PR", "X sent a PR on Slack") and report findings to me directly WITHOUT posting anything on GitHub.
user_invocable: true
---

# review-pr-silent

Review a teammate's PR thoroughly and report to me in chat. Investigate the codebase, not just the diff.

## Absolute rule

NEVER post a review, inline comment, or reaction on GitHub. No `gh pr review`, no `gh pr comment`, no reactions. Report to me in chat only. This is non-negotiable.

## Environment

- `gh` CLI fails on this machine when `GITHUB_TOKEN` is set. Prefix EVERY gh call: `GITHUB_TOKEN= gh ...`
- Repos cloned under `~/projects/<repo>` (platform, app, backend, …). Default branch `main`.
- Slack connected via MCP (`mcp__claude_ai_Slack__*`), workspace `doinstructworkspace`.
- Linear connected via MCP (`mcp__claude_ai_Linear__*`).
- GitHub user: KonstantinKo.

## Workflow

1. **Find the PR.** If I only say "X sent it on Slack", search my Slack DMs / channels for the link first (`slack_search_public_and_private`, then `slack_read_thread`). Extract the PR URL.
2. **Fetch metadata + diff** (read-only):
   - `GITHUB_TOKEN= gh pr view <pr> --json title,body,state,reviewDecision,additions,deletions,files,headRefName,url`
   - `GITHUB_TOKEN= gh pr diff <pr>`
3. **Investigate beyond the diff:**
   - grep all callers of changed functions/exports in the repo — are call sites still correct?
   - check whether behavior changes are reflected in tests (changed logic, no test delta = flag it).
   - check whether the PR description matches what the diff actually does.
4. **CI:** `GITHUB_TOKEN= gh pr checks <pr>` — surface failing or newly-introduced warning checks.
5. **Ticket:** pull the Linear ticket from the branch name or PR body via `mcp__claude_ai_Linear__get_issue` for acceptance-criteria context.
6. **Report to me in chat:**
   - one-line header: PR #, ticket id, file/line counts, CI status.
   - 1–2 sentences: what it does.
   - each concern: short paragraph.
   - if there's a concern: the exact one-sentence question I should send the author.
   - if clean: say so plainly so I can approve confidently.
   - ALWAYS end every message about the PR with the PR URL on its own line.
