---
description: "MANUAL ONLY: Run CodeRabbit PR review/fix loop, then squash-merge when clean"
agent: build
---

# CodeRabbit PR Fix Loop

Monitor current PR or PR from `$ARGUMENTS`. Fix valid CodeRabbit findings, verify, push, repeat, then merge when clean. If actionable CodeRabbit comments exist but none verify against current code, no fix commit is needed; still merge when checks are green and PR is clean.

## Rules

- Manual-only command. Run only when user explicitly invokes `/coderabbitfix-pr` or asks for this exact PR CodeRabbit merge loop. Do not choose this command autonomously.
- Use `env -u GITHUB_TOKEN -u GH_TOKEN gh ...` for every GitHub CLI command.
- Do not force-push.
- Do not use destructive git commands.
- Verify findings against current code before editing.
- Fix only valid actionable findings.
- Loop as long as needed to fix all verified findings. Stop only when clean or blocked. Apply a max loop count only if user specifies one in `$ARGUMENTS`.
- If none of the actionable findings verify, do not invent fixes; proceed to merge when PR is clean.
- Keep changes minimal.
- Prefer squash merge.
- If branch deletion/local checkout fails because another worktree owns the branch, retry merge without local branch deletion.

## Preflight

1. Run `git status --short --branch`.
2. Determine PR:
   - If `$ARGUMENTS` includes PR number or URL, use it.
   - Otherwise run `env -u GITHUB_TOKEN -u GH_TOKEN gh pr view --json number,url,state,headRefName,baseRefName`.
3. Read PR state:
   - `env -u GITHUB_TOKEN -u GH_TOKEN gh pr view <pr> --json state,mergeStateStatus,mergeable,isDraft,reviewDecision,statusCheckRollup,comments,reviews,url,headRefName,baseRefName`
   - `env -u GITHUB_TOKEN -u GH_TOKEN gh pr checks <pr>`
4. Create `todowrite` items for monitoring, fixes, review reruns, and merge.

## CodeRabbit Trigger

If latest CodeRabbit review is missing, skipped, stale, or before latest pushed commit:

1. Comment `@coderabbitai review`:
   - `env -u GITHUB_TOKEN -u GH_TOKEN gh pr comment <pr> --body "@coderabbitai review"`
2. Watch checks:
   - `env -u GITHUB_TOKEN -u GH_TOKEN gh pr checks <pr> --watch --interval 30`
   - Use generous command timeout, at least 15 minutes. CodeRabbit commonly takes a while; do not rush.
3. Re-read comments and reviews.

## Finding Extraction

Read CodeRabbit output via:

```sh
env -u GITHUB_TOKEN -u GH_TOKEN gh pr view <pr> --json reviews --jq '.reviews[] | select(.author.login=="coderabbitai") | {state,submittedAt,body}'
env -u GITHUB_TOKEN -u GH_TOKEN gh pr view <pr> --json comments --jq '.comments[] | select(.author.login=="coderabbitai") | {createdAt,body}'
```

Treat latest CodeRabbit review/comment as authoritative for current loop.

No-actionable-comment signals include:

- `No actionable comments were generated in the recent review.`
- CodeRabbit check success with no new actionable review body after latest commit.

## Fix Loop

Loop as long as needed to fix all verified issues. Use a maximum iteration count only when user explicitly provides one in `$ARGUMENTS`.

For each iteration:

1. List actionable CodeRabbit comments.
2. Verify each finding in code.
3. Fix confirmed issues with smallest correct edit.
4. Skip invalid/stale findings; record reason.
5. Run verification:
   - Prefer repo verify command such as `just verify`.
   - Also run targeted tests/builds for touched areas.
6. Inspect `git status --short` and `git diff --stat`.
7. Commit fixes with concise message, e.g. `fix: address coderabbit comments`.
8. Push.
9. Trigger CodeRabbit again with `@coderabbitai review`.
10. Watch until complete with generous timeout, at least 15 minutes.

## Merge

When latest CodeRabbit review has no actionable comments, or actionable comments were all verified as invalid/stale, and checks pass:

1. Confirm merge readiness:
   - `env -u GITHUB_TOKEN -u GH_TOKEN gh pr view <pr> --json state,mergeStateStatus,mergeable,statusCheckRollup,reviewDecision`
2. If mergeable and clean, squash merge:
   - `env -u GITHUB_TOKEN -u GH_TOKEN gh pr merge <pr> --squash --delete-branch`
3. If local worktree branch deletion causes failure, retry:
   - `env -u GITHUB_TOKEN -u GH_TOKEN gh pr merge <pr> --squash`
4. Verify merged state:
   - `env -u GITHUB_TOKEN -u GH_TOKEN gh pr view <pr> --json state,mergedAt,mergeCommit,url`

## Final Report

Return compact report:

```text
PR: <url>
CodeRabbit: <clean/fixed/skipped>
Fix commits:
- <sha> <message>
Checks:
- <command> -> <result>
Merge: <merged/not merged + reason>
```

## Additional User information

$ARGUMENTS
