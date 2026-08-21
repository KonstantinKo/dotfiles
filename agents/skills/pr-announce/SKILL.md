---
name: pr-announce
description: Use when I want a ready-to-paste Slack announcement for one of my PRs ("announce this PR", "slack message for this PR"). Given a PR (current branch by default, or a number / repo#number). Outputs text only — never posts.
user_invocable: true
---

# pr-announce

Produce a ready-to-paste Slack announcement for a PR. CRITICAL: output the message text only, NEVER post it anywhere (no Slack send, no gh comment).

## Environment

- `gh` CLI fails on this machine when `GITHUB_TOKEN` is set. Prefix EVERY gh call: `GITHUB_TOKEN= gh ...`
- Repos under `~/projects/<repo>`, default branch `main`. GitHub user: KonstantinKo.
- Linear connected via MCP (`mcp__claude_ai_Linear__*`).

## Gather (read-only)

- Default to the current branch's PR. Accept a PR number or `repo#number` argument.
- `GITHUB_TOKEN= gh pr view <pr> --json title,url,state,reviewDecision,additions,deletions,files,body,headRefName`
- Find the Linear ticket URL in this order: (1) PR body link, (2) the bot linkback comment, (3) extract the ticket id from the branch name and resolve via `mcp__claude_ai_Linear__get_issue`.

## Complexity coins

Emoji coins scaled by file count: **1** = single file · **2** = 2–7 files · **3** = 8–15 · **4** = 16+.

## Output format

Raw Slack mrkdwn, NOT inside a code fence (so it renders on paste):

```
<coins on their own first line>
*<bold title, conventional-commit prefix stripped>*
*PR:* <raw URL>
<N> files · <✅ merged | ✅ all checks passed | ⏳ checks running | ❌ checks failing>
*Ticket:* <raw ticket URL>
```

Rules:
- Status line picks ONE state from CI (`GITHUB_TOKEN= gh pr checks <pr>`) + merge state.
- Omit the `*Ticket:*` line entirely if no ticket found.
- No divider lines. No trailing "N coins" explanation.
