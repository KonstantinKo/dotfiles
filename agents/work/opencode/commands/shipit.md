---
description: "MANUAL ONLY: Finish implementation, audit, open PR, run CodeRabbit loops, and merge to main"
agent: build
---

# Ship It

Finish current implementation from `$ARGUMENTS`, then get it merged to main unless truly blocked.

Use this when user has enough confidence in current direction and wants agent to keep running without close supervision.

## Completion Contract

You are not done until one of these is true:

- Code is merged to `main`.
- Truly blocking issue appears and cannot be resolved safely without user decision/access/secret/destructive approval.

Do not stop after local implementation, local verification, PR creation, or first review pass.

## Rules

- Manual-only command. Run only when user explicitly invokes `/shipit` or asks for this exact finish-to-merge pipeline. Do not choose this command autonomously.
- Preserve unrelated user/agent changes.
- Do not force-push.
- Do not use destructive git commands.
- Do not deploy.
- Use `env -u GITHUB_TOKEN -u GH_TOKEN gh ...` for every GitHub CLI command.
- Prefer squash merge.
- If branch deletion/local checkout fails because another worktree owns the branch, retry merge without local branch deletion.
- Ask user only for real blockers: missing credentials, ambiguous product/architecture decision, destructive action approval, or conflict with unrelated work.

## Finish Implementation

1. Continue current implementation until task is functionally complete.
2. Run relevant local verification. Prefer repo verify command such as `just verify`; add targeted tests/builds for touched areas.
3. Inspect `git status --short --branch` and `git diff --stat`.

## Audit Cycles

Run audit loops before PR:

1. Run `/quickreview` or equivalent independent read-only review.
2. Fix all verified issues.
3. Rerun `/quickreview` until no blocker/high-confidence issues remain.
4. Run `/coderabbitfix` or equivalent local `coderabbit review --agent` loop.
5. Fix all verified CodeRabbit CLI findings.
6. Rerun `/coderabbitfix` until clean or all actionable findings are verified invalid/stale.

Use generous CodeRabbit timeout, at least 15 minutes. CodeRabbit commonly takes a while; do not rush.

## Commit And PR

1. Inspect before commit:
   - `git status --short --branch`
   - `git diff --stat`
   - `git diff --check`
   - `git log --oneline -10`
2. Stage only intended files.
3. Commit with concise repo-style message.
4. Push branch.
5. Open PR to `main` with `gh pr create`.
6. Include summary and verification in PR body.

## PR CodeRabbit Loop

Run `/coderabbitfix-pr` or equivalent PR loop:

1. Trigger CodeRabbit PR review if needed: `@coderabbitai review`.
2. Watch PR checks with generous timeout, at least 15 minutes.
3. If CodeRabbit posts actionable comments:
   - Verify each finding.
   - Fix valid findings.
   - Skip invalid/stale findings with reason.
   - Verify locally.
   - Commit and push fixes.
   - Trigger CodeRabbit again.
4. Loop until latest CodeRabbit review has no actionable comments or all actionable comments are verified invalid/stale.

## Merge

When PR checks are green and CodeRabbit loop is clean:

1. Confirm readiness:
   - `env -u GITHUB_TOKEN -u GH_TOKEN gh pr view <pr> --json state,mergeStateStatus,mergeable,statusCheckRollup,reviewDecision`
2. Squash merge:
   - `env -u GITHUB_TOKEN -u GH_TOKEN gh pr merge <pr> --squash --delete-branch`
3. If local branch deletion fails due worktree conflict, retry without branch deletion:
   - `env -u GITHUB_TOKEN -u GH_TOKEN gh pr merge <pr> --squash`
4. Verify merged state:
   - `env -u GITHUB_TOKEN -u GH_TOKEN gh pr view <pr> --json state,mergedAt,mergeCommit,url`

## Final Report

Return compact report only after merge or true blocker:

```text
Result: <merged/blocked>
PR: <url if any>
Merge commit: <sha if merged>
Local audit: <quickreview result + coderabbitfix result>
PR audit: <coderabbitfix-pr result>
Checks:
- <command> -> <result>
Blocker:
- <none or exact blocker>
```

## Additional User information

$ARGUMENTS
