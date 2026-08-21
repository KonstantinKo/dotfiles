---
description: "MANUAL ONLY: Drive a human-approved PR through merge, sync main, and clean its worktree"
disable-model-invocation: true
---

# /ensuremerge

Run this command only when the human explicitly invokes `/ensuremerge`. Never select, suggest, or invoke it autonomously. If this prompt was reached indirectly, stop without acting.

The target is appended at the end. It may be a PR URL, `owner/repo#number`, PR number in the current repository, or branch name. If omitted, use the PR for the current branch.

## Completion Contract

The human considers the PR approved from their side. Continue until one of these is true:

- The PR is verifiably merged into the remote default branch, that branch is pulled into its clean local worktree, and the PR worktree/branch is cleaned up.
- A real blocker requires another person's approval, access, a product/architecture decision, or risky conflict resolution. Stop and ask the human with the exact blocker and recommended next action.

Being queued, having auto-merge enabled, or having green checks is not completion. Monitor until the PR actually reaches `MERGED` and the merge commit is present on the remote default branch.

## Safety Rules

- Human approval from this invocation does not satisfy GitHub-required reviews. Never approve the PR yourself, dismiss reviews, impersonate another reviewer, use admin merge, bypass branch protections, weaken required checks, or circumvent CODEOWNERS/required approvals.
- Never force-push. For a published branch that needs the latest base, merge the base into the PR branch instead of rebasing it.
- Preserve unrelated changes. Never reset, discard, overwrite, or stash another person's work.
- Never remove a dirty worktree or a branch with unique unpushed work.
- Do not deploy.
- Do not post GitHub comments unless the human explicitly asks in this session.
- Use `env -u GITHUB_TOKEN -u GH_TOKEN gh ...` for every GitHub CLI command.
- Prefer squash merge unless repository policy or the PR explicitly requires another allowed method.
- Use a task list and keep it current through merge monitoring and cleanup.

## Preflight

1. Resolve the repository and PR from the target. Record PR number, URL, state, draft status, author, base/head repositories and refs, head SHA, mergeability, merge state, review decision, required checks, auto-merge state, and merge queue state.
2. Inspect local Git state with `git status --short --branch`, `git remote -v`, `git worktree list --porcelain`, and recent log. Locate any worktree that owns the PR head branch and the worktree that owns the local default branch.
3. Fetch remotes without changing user files.
4. If already merged, skip directly to post-merge verification and cleanup. If closed without merge or still a draft, stop and report the blocker.

## Get It Merge-Ready

1. Confirm all approvals required by GitHub are present. If another reviewer/CODEOWNER must approve, do not circumvent it. Enable auto-merge if allowed and useful, then stop and ask the human to obtain that approval.
2. Inspect all required checks and unresolved review threads.
3. For pending checks, enable auto-merge when available and monitor them.
4. For failures, inspect logs and classify them:
   - Fix deterministic, PR-caused failures on the PR branch using the smallest correct change, then run relevant verification, commit, and push normally.
   - Retry clearly flaky/infra failures only through normal GitHub controls; never mark them successful or bypass them.
   - Escalate broad, ambiguous, security-sensitive, or architectural fixes before editing.
5. For unresolved human change requests, stop and ask. For bot findings, verify them against current code and fix only findings that check out.

## Merge And Monitor

1. If immediately mergeable and repository policy allows direct merge, run the normal squash merge command.
2. Otherwise enable squash auto-merge or enqueue through the repository's merge queue.
3. Poll PR state and required checks until `MERGED`. Do not stop merely because GitHub reports queued or auto-merge enabled.
4. If the PR leaves the queue, auto-merge disables, checks rerun, or mergeability changes, diagnose and recover:
   - If the base advanced and caused conflicts, work in the existing PR worktree. If none exists, create a temporary dedicated worktree for the head branch.
   - Merge the latest remote base into the PR branch without force-pushing.
   - Resolve only clear, in-scope conflicts. Run targeted and repository-required verification, commit the merge/conflict resolution, push, and re-enable auto-merge or re-enqueue.
   - If conflict intent is unclear, the resolution spreads beyond the PR's scope, or required behavior changed materially, stop and ask the human.
5. Repeat until merged or genuinely blocked.

## Verify Main

1. Read the merged PR state and record `mergedAt` and `mergeCommit`.
2. Fetch the remote default branch and verify the merge commit is reachable from it.
3. Locate the local default-branch worktree. If clean, fast-forward it to the remote default branch.
4. If that worktree is dirty, do not stash/reset it. Report exactly what prevents pulling main and ask the human; the remote merge remains complete, but local cleanup is not.

## Clean Up

Cleanup is authorized only after remote merge verification:

1. Confirm the PR worktree is clean and has no unique unpushed work.
2. If the PR used a dedicated worktree, remove that worktree normally, then delete its local branch. A forced local branch deletion is allowed only when the verified squash merge makes the original commits non-ancestors and no unique/unpushed work remains.
3. If the PR branch occupied the primary checkout, switch that checkout to the default branch, fast-forward it, then delete the local PR branch; never remove the primary worktree itself.
4. Delete the remote head branch only when it belongs to the same repository, is not protected, and was not already deleted by GitHub. Never delete a contributor fork branch.
5. Do not touch unrelated worktrees or branches.
6. Finish by checking `git worktree list --porcelain`, local/remote branch presence, default-branch status, and PR merged state.

## Final Report

Return only after merge and cleanup, or a real blocker:

```text
Result: <merged and cleaned / blocked>
PR: <url>
Merge commit: <sha or none>
Checks/reviews: <summary>
Queue recovery: <none or actions taken>
Local main: <updated path/status>
Cleanup: <worktree/local branch/remote branch status>
Blocker: <none or exact human action needed>
```

Target:

$ARGUMENTS
