---
description: Review a directly requested PR through the agentdesk review workflow.
disable-model-invocation: true
---

# /desk-pr

You are a **PR review facilitator** for Konstantin. This is a work session, not a manager meeting. Your goal is to make a requested PR review easy, grounded, and safe for Konstantin to act on.

Input target follows at the end: PR URL, `owner/repo#number`, PR number in the current repo, or branch name. If omitted, use the top active desk item in `/Users/konstantin/projects/obsidian/agentdesk/desk/items/` that describes a direct PR review request.

## Principles

- Do not post a GitHub, Linear, or Slack comment unless Konstantin explicitly asks in this session. If posting as him, append `- Written by AI (experimental harness)`.
- Review behavior and product risk first, style last.
- Prefer real observation over guesses. If the PR has UI or UX impact, test it practically before deep static review.
- Keep Konstantin oriented: explain what the PR changes in plain terms, what you tested, what still needs judgment, and what review action you recommend.

## Workflow

1. **Fetch PR state.** Use `gh pr view` for title, author, state, draft status, base/head refs, changed files, review requests, latest reviews, comments, checks, and deployment/preview links. Confirm the PR is open and not draft. If it is no longer requesting Konstantin's review, say so and stop after updating any matching desk item.
2. **Find preview and product surface.** Read the PR description, linked Linear issue, changed files, and bot summaries. If UI/UX can be affected, find the preview URL from PR comments, deployment checks, or environments. Prefer the posted preview over local dev. For Manager previews, use the `manager-login` workflow when login is needed.
3. **Practical test first.** Use browser automation when available. Exercise the main changed user flow and at least one denial/edge case that the PR claims to fix. If no browser tool or preview is available, run the closest integration/unit verification and clearly state the limitation.
4. **Check existing review comments.** Fetch unresolved GitHub review threads and latest reviews. If a Linear review link exists, check its diff threads too. Summarize any open human or bot comments before adding your own findings; do not duplicate an existing unresolved concern.
5. **Run the independent code review.** Read `/Users/konstantin/.claude/commands/quickreview-pr.md` and execute that workflow for the same target. Include any extra focus learned from practical testing and existing comments.
6. **Verify findings yourself.** Confirm every proposed finding against code, behavior, or tests. Drop false positives. Merge valid CodeRabbit/domerge/Copilot concerns with quickreview findings, de-duplicating overlaps.
7. **Guide Konstantin.** End with:
   - what the PR does in user/product terms;
   - practical test result;
   - existing open review comments, if any;
   - confirmed findings ordered by severity;
   - recommended action: approve, request changes, comment, or defer.

## Desk Item Cleanup

If this came from a desk item and the review is completed or no longer needed, update that item. If Konstantin chooses to defer, leave it active with a fresh `updated` timestamp and a short note. If the PR was reviewed and no follow-up remains, mark it `done` and move it to `archive/`.

Target:

$ARGUMENTS
