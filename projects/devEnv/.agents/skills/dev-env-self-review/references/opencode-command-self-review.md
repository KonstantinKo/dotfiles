---
description: Iteratively review and improve current branch changes with a read-only subagent
agent: build
---

# Self Review Loop

Review and improve current branch changes from `$ARGUMENTS`. Include committed branch changes, staged changes, unstaged changes, and untracked files. Do not commit.

## Goal

Repeatedly spawn a read-only reviewer subagent, fix real issues, then review again until no Critical, High, or Medium issues remain. Low-only issues may remain if not worth changing; report them clearly.

## Preflight

1. Run `git status --short --branch`.
2. Determine comparison base without changing branches:
   - Prefer `origin/main` when available.
   - Else use `main` when available.
   - Else use `master` when available.
   - Else review only `HEAD` plus index/worktree changes.
3. Inspect current change shape:
   - `git log --oneline <base>..HEAD` when a base exists.
   - `git diff --stat <base>...HEAD` when a base exists.
   - `git diff --stat HEAD` for tracked staged + unstaged changes.
   - `git diff --cached --stat` for staged changes.
   - `git diff --stat` for unstaged changes.
   - `git ls-files --others --exclude-standard` for untracked files.
4. If there are no branch, staged, unstaged, or untracked changes, say so and stop.
5. Create `todowrite` items for review loops, fixes, and verification.

## Loop

Run at most 5 iterations. Stop earlier when the reviewer reports no Critical, High, or Medium findings.

For each iteration:

1. Spawn `task` with `subagent_type: general` and this prompt:

```text
You are a read-only staff engineer reviewer for this repo. Review all current branch changes, including committed branch diff, staged changes, unstaged changes, and untracked files. Do not edit files. Do not stage, unstage, commit, stash, reset, checkout, or delete anything.

Scope from caller: $ARGUMENTS

Required checks:
- Run `git status --short --branch`.
- Identify comparison base: prefer `origin/main`, else `main`, else `master`; if none exists, say so.
- Inspect committed branch diff from base to HEAD when base exists.
- Inspect `git diff --cached` for staged changes.
- Inspect `git diff` for unstaged changes.
- Inspect untracked file names from `git ls-files --others --exclude-standard`; read relevant untracked files directly.
- Read `AGENTS.md`.
- Read `.project/AGENTS.md`.
- Read `.project/docs/repoConventions.md`.
- Read matching `.project/docs/feature/<feature>/README.md` and `.project/rules/*.md` for touched areas.
- Read `apps/router/docs/spec.md` for router/admin/env lifecycle, auth, DB, Fly, or workflow changes.
- Read `apps/router/docs/elysiaJs/research.md` for router/server/Elysia changes.
- Use Grep/Glob/Read for impacted code and tests.

Find only real issues: bugs, regressions, security/access problems, data-loss risks, spec violations, broken tooling, missing tests for changed behavior, or maintainability problems with concrete failure modes. Avoid style-only findings.

Also check that feature behavior/data/access/workflow/Opencode changes update `.project` docs and that no ADR files/folders were added.

Output:
- Findings first, ordered by severity: Critical, High, Medium, Low.
- Each finding: `Severity | file:line | problem | impact | suggested fix`.
- If no Critical/High/Medium findings, state `NO_BLOCKING_FINDINGS`.
- Include a short `Review coverage` list with diffs/files inspected.
- Include `Residual low issues` list; empty if none.
```

2. Read the reviewer report. Treat it as input, not truth. Verify any finding before changing code.
3. Fix all confirmed Critical, High, and Medium issues. Fix Low issues only when cheap and clearly correct.
4. Use the smallest correct edits. Preserve user changes and staging intent; do not stage or unstage files unless the user explicitly asked.
5. Run targeted checks for touched areas after fixes. Prefer repo commands from `justfile` when feasible.
6. Record fixes and checks in your notes.
7. Repeat with a fresh reviewer subagent unless there are no Critical/High/Medium findings.

## Hard Stops

- Never run destructive git commands such as `git reset --hard`, `git checkout --`, `git clean`, or branch deletion.
- Never commit unless the user explicitly asks.
- Never deploy.
- If reviewer asks for product/behavior decisions that cannot be answered from code/docs, ask the user one focused `question` and pause the loop.
- If a fix would require broad redesign outside `$ARGUMENTS`, leave it as remaining risk instead of expanding scope silently.

## Final Report

Return compact report:

```text
Self-review loops: <n>
Fixed:
- <issue> -> <files>

Checks run:
- <command> -> <result>

Remaining low issues:
- <issue or none>

Remaining risks:
- <risk or none>
```
