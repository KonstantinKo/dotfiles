---
name: PR or branch review
description: Subagent-verify workflow for reviews.
disable-model-invocation: true
---

Critically review a PR or branch vs its merge base, optionally cross-checked against CodeRabbit.

## Input

The arguments below are the target followed by optional extra instructions:

$ARGUMENTS

Parse them as: first token = PR URL, PR number, or branch name to review; anything after = extra review instructions to fold into the subagent prompt and your own verification. If no target is given, review the current branch.

## 1. Prepare a clean worktree

The review must run against an isolated, clean checkout of the target head — never the main checkout, and never a dirty tree.

- If the current working directory is already a worktree checked out to the target head AND `git status --short` is clean, use it as-is.
- Otherwise, set up a dedicated worktree for the target by invoking the `worktree-setup` skill when a full setup is needed. Put it under `.slim/worktrees/<target-slug>` to match existing convention. If the target is a PR, fetch its head and base refs first. If the branch exists only on the remote, create the worktree tracking `origin/<branch>`.
- Do all subsequent steps inside that worktree path.

## 2. Determine the diff scope

Only review the diff caused by commits on this target vs the commit it was last branched from — not differences due to local pull-state. There may be merge-commits on the target; diffing against the merge base nets those out.

```
git merge-base origin/<base-ref> HEAD   # = BASE
git diff BASE..HEAD
```

Use this exact range for both the subagent and CodeRabbit.

## 3. Run reviewers

- **Subagent:** Task an Opus subagent with critically reviewing `BASE..HEAD`. It must hunt for real correctness/behavior issues (not cosmetics) and order its findings by priority. Pass along any extra instructions parsed from the input.
- **CodeRabbit:** For GitHub PR targets, first check whether `coderabbitai[bot]` already reviewed or commented on the PR for the current head. Use GitHub review/comment data; if bot output exists, read and include that instead of running local CLI. If no bot output exists and the local `coderabbit` CLI is installed/authenticated, optionally run in the worktree:
  ```
  coderabbit review --plain --type committed --base-commit BASE
  ```
  If the CLI is missing, unauthenticated, slow, or times out, continue without it and report that limitation briefly. Never block the review on local CodeRabbit when the GitHub bot has already run.

## 4. Verify and merge

Once you have the subagent report and any available CodeRabbit findings:

- Verify every finding yourself against the actual code — confirm it checks out or that further context clarifies/invalidates it. Discard false positives (note them briefly).
- Merge the valid CodeRabbit findings into the subagent's, de-duplicating overlaps.

## 5. Output

Give me only the findings that check out, ordered by local path (alphabetically) then line number, so I can cross-reference against the changed-files view of the GitHub PR. For each: path:line, severity, the issue, and the suggested fix. Note the source (subagent / CodeRabbit / both).
