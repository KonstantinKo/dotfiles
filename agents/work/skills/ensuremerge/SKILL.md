---
name: ensuremerge
description: "MANUAL ONLY: Drive a human-approved PR through merge, sync main, and clean its worktree."
disable-model-invocation: true
---

# /ensuremerge

Run only on explicit human invocation of `/ensuremerge`. If reached indirectly, stop without acting.

Target (may be empty → PR of current branch): PR URL, `owner/repo#number`, PR number in current repo, or branch name.

Helper scripts (host-agnostic path): `~/.agents/skills/ensuremerge/scripts/`. Use them — they exist to keep token usage low.

## Token-Efficiency Rules

- NEVER poll PR/check state in model turns. All waiting goes through `pr-wait.sh` run in the background (Claude: Bash `run_in_background`; other hosts: `nohup ... > /tmp/ensuremerge-wait.log &` then check the log when returning). While it runs, do nothing on this task.
- NEVER read raw CI logs into the main context. Delegate triage to a cheap-model subagent (Claude: Agent tool, `model: haiku`). No subagent support on the host → extract with `gh run view --log-failed | grep -B5 -A30 <pattern> | head -80`, never the full log.
- PR state comes from `pr-status.sh`, local git state from `local-state.sh`. Ad-hoc `gh ... --json` calls only for data those scripts lack, always with a minimal field list and `--jq`.
- Keep the running task list terse.

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
- Use `env -u GITHUB_TOKEN -u GH_TOKEN gh ...` for every ad-hoc GitHub CLI command (scripts already do this).
- Prefer squash merge unless repository policy or the PR explicitly requires another allowed method. When the base branch has a **merge queue** (`pr-status.sh` prints `merge_queue=yes`), the queue owns the method: enqueue with `gh pr merge <n> --auto` and **no method flag** (`--squash`/`--merge`/`--rebase` are rejected with "The merge strategy for main is set by the merge queue"), never merge directly, and do not ask the human which strategy to use.
- Destructive git operations (worktree remove, branch delete, checkout switches) stay in the main session — never delegate them to subagents.

## Preflight

1. `pr-status.sh <target>` — records repo, PR number, state, draft, fork, mergeability, merge state, review decision, auto-merge, whether the base branch runs a merge queue (`merge_queue=yes method=…`) and the PR's queue entry (`queue_entry=…`), failing/pending checks, unresolved thread count.
2. `git fetch origin` in the repo, then `local-state.sh <head-branch>` — worktree map, dirty counts, unpushed work, default-branch position.
3. Already `MERGED` → skip to Verify Main. Closed without merge or draft → stop, report blocker.

## Get It Merge-Ready

1. Required approvals missing → do not circumvent. Enable auto-merge if allowed and useful (merge queue → `gh pr merge <n> --auto`, no method flag), then stop and ask the human to obtain the approval.
2. Pending checks → enable auto-merge (squash where the repo lets you choose; no method flag on a merge-queue base), go to Merge And Monitor.
3. Failing checks → triage via cheap-model subagent per Token-Efficiency Rules. Subagent prompt: repo, PR number, failing check names; task: fetch failed-job logs via `env -u GITHUB_TOKEN -u GH_TOKEN gh run view --log-failed`, classify PR-caused vs flaky/infra, return failing test names + ≤30-line relevant excerpt + suspected cause. Then:
   - Deterministic PR-caused failure → fix on the PR branch with the smallest correct change, run relevant verification, commit, push normally.
   - Clearly flaky/infra → retry via normal GitHub controls only; never mark successful or bypass.
   - Broad, ambiguous, security-sensitive, or architectural → escalate before editing.
4. Unresolved human change requests → stop and ask. Bot findings → verify against current code, fix only what checks out.

## Merge And Monitor

1. Merge queue on the base (`merge_queue=yes`) → enqueue with `gh pr merge <n> --auto` (no method flag; `queue_entry=` confirms it took) and go straight to monitoring — the queue merges when its own checks pass. No merge queue: immediately mergeable + policy allows direct merge → squash merge now; otherwise enable squash auto-merge.
2. Start `pr-wait.sh <owner/repo> <number>` in the background. Do not touch this task until it returns. Act on its `RESULT=` line:
   - `merged` → Verify Main.
   - `checks-failed` → back to Get It Merge-Ready step 3.
   - `conflicts` → merge latest remote base into the PR branch in its existing worktree (create a temporary one only if none exists), resolve only clear in-scope conflicts, run targeted + repo-required verification, commit, push, re-enable auto-merge/re-enqueue, restart `pr-wait.sh`. Unclear intent, out-of-scope spread, or materially changed behavior → stop and ask.
   - `automerge-dropped` / `queue-dropped` → run `pr-status.sh`, diagnose (queue runs its own checks; a failure there removes the entry without failing the PR's checks), fix or re-enqueue, restart `pr-wait.sh`.
   - `closed-without-merge` → stop, report blocker.
   - `timeout` / `gh-error` → run `pr-status.sh` once, reassess, restart wait or escalate.
3. Repeat until merged or genuinely blocked.

## Verify Main

1. From `pr-status.sh`: record `merged_at` and `merge_commit`.
2. `git fetch origin`, then verify `git merge-base --is-ancestor <merge_commit> origin/<default>`.
3. `local-state.sh` → default-branch worktree clean → fast-forward it. Dirty → do not stash/reset; report exactly what blocks pulling main and ask (remote merge complete, local cleanup not).

## Clean Up

Only after remote merge verification. Use `local-state.sh` facts; run the destructive commands yourself:

0. Get out of the PR worktree first. A shell cannot remove its own directory, and a Claude Code session that was switched into the worktree (EnterWorktree, or launched inside it) is sandboxed to that worktree: git commands aimed at the primary checkout or other worktrees are refused. Claude: call `ExitWorktree` with `action: "keep"` (a manually added worktree cannot be removed by the tool) to return to the primary checkout, then run every step below from there. Other hosts: `cd` to the primary checkout.

1. PR worktree must be clean with no unique unpushed work.
2. Dedicated PR worktree → remove it normally, then delete the local branch. Forced local branch deletion only when the verified squash merge makes the original commits non-ancestors and no unique/unpushed work remains.
3. PR branch on the primary checkout → switch to default branch, fast-forward, delete local PR branch; never remove the primary worktree.
4. Delete the remote head branch only if same-repo, unprotected, and not already deleted by GitHub. Never delete a contributor fork branch.
5. Do not touch unrelated worktrees or branches.
6. Finish with `local-state.sh` + `pr-status.sh` to confirm final state.

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
