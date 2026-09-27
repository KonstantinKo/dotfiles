---
description: Safely preserve, revert, and redo a bad attempt with a cleaner devEnv approach
agent: build
---

# Scrap And Redo

Use when current implementation works poorly or fights repo patterns. Preserve lessons, revert safely, re-grill, redo cleanly. Do not commit.

## 1. Scope Scrap

Use `question` to choose scope:
- Working tree only: staged + unstaged edits, HEAD untouched
- Last N commits on this branch: ask N, backup branch first
- Specific file set: user names paths
- Worktree branch since divergence: leave old worktree intact, redo elsewhere

Do not touch unrelated user/agent changes. If scope includes changes you did not make and they conflict, stop and ask.

## 2. Capture Lessons

Before revert, inspect relevant diff/log/files. Summarize:
- What was tried
- Why it is wrong
- What is reusable
- Spec constraint missed
- Cleaner target shape

Keep this in conversation; do not create scrap docs unless user asks.

## 3. Preserve Safety

Before destructive ops, show exact commands and ask `question` for approval.

Recommended safety:
- Working tree: `git stash push -m "scrap-<short-desc>-<timestamp>"` or backup branch if user prefers
- Commits: `git branch scrap/<short-desc>-<timestamp>` before reset/revert
- File set: stash just those paths or copy to user-approved `scrap/` dir
- Worktree: leave old worktree, create/ask for new one

Never run `git reset --hard`, `git clean -f`, `git checkout --`, `git branch -D`, or force push without explicit approval for exact command and scope.

## 4. Revert

Execute approved safe revert. Verify with `git status`.

## 5. Regrill

Run `/grill` seeded with lessons. Focus:
- Elegant solution shape: 2-3 concrete approaches
- Reuse vs rebuild for each salvageable piece
- v1 cut list
- TDD or direct redo

Do not proceed until adversarial review clears.

## 6. Reimplement

Implement focused redo directly. If scope becomes broad/multi-slice, stop and recommend `/full` or `/tdd-full`.

If TDD chosen:
- Write failing tests first
- Confirm expected red
- Implement minimum code
- Confirm green

## 7. Stage Review

Stage specific files only if user wants review. Show cached stat/diff. Ask `question`: LGTM / Fix / Drop. Do not commit.

## 8. Cleanup

Offer to remove stash/backup/scrap dir only after user reviewed redo. Leave safety artifacts if unsure.
