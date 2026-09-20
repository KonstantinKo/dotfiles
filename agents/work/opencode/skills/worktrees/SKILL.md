---
name: worktrees
description: Manage Git worktrees as safe isolated lanes for risky, long-running, or parallel work. Use when isolation materially reduces conflict or protects active checkout.
---

# Worktrees

Use worktrees for parallel branches, risky changes, long-running work, disposable
spikes, or when user explicitly asks. Skip them for small bounded edits.

## Source Of Truth

Use `git worktree list --porcelain`. Do not create a parallel manifest. Manifests
drift and duplicate Git state.

Follow repository-specific location/branch conventions first. Otherwise prefer a
sibling or dedicated external worktree path so searches from main checkout cannot
walk duplicate repository copies. Do not expose nested worktrees through `.ignore`.

## Preflight

Before mutation:

1. Confirm Git root, current branch, dirty state, and intended base.
2. Inspect `git worktree list --porcelain`.
3. Check candidate branch/path does not already exist.
4. Check remote/base freshness appropriate to task.
5. Preserve unrelated local changes.

If user explicitly requested worktree or active workflow requires one, creation is
already approved. Otherwise ask before creating branch/worktree when intent is
ambiguous.

## Create

Typical command:

```bash
git worktree add -b <branch> <path> <base>
```

Then follow repository worktree setup guidance. Copy local environment files only
when required and never overwrite destination. Install dependencies or generate
artifacts only inside new worktree.

## Execute

- Keep edits, builds, tests, and worker cwd inside assigned lane.
- Give parallel lanes non-overlapping ownership where possible.
- Re-check shared/base assumptions before integration.
- Commit only when user requested or workflow explicitly requires commits.
- For long work, keep disposable task journal inside lane via `deepwork` skill.

## Validate

Before delivery/integration:

1. Run relevant formatting, lint, typecheck, tests, and builds in lane.
2. Inspect status and diff against intended base.
3. Check for accidental generated files, secrets, or unrelated changes.
4. Reconcile independent review when risk warrants it.

## Integrate And Clean Up

Do not merge, rebase, cherry-pick, push, delete branches, or remove worktrees unless
user requested that action or active workflow explicitly includes it.

Before removing worktree:

1. Confirm lane is clean or every change is intentionally preserved.
2. Confirm branch/commit/PR state is recoverable.
3. Promote cross-task facts from disposable journal into durable project/user
   source when needed.
4. Run `git worktree remove <path>` only after cleanup is approved.
5. Prune only stale administrative entries; never use prune to discard work.

Never use `git reset --hard`, `git clean`, force-push, or forced dirty-worktree
removal without explicit approval for exact operation.
