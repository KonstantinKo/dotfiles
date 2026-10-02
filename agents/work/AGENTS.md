# Work instructions

Read `~/.agents/AGENTS.md` for shared global preferences if it is not already loaded, then apply these work-only rules.

## Delegation & verification

- After a feature or fix implementation agent reports done, automatically run `code-review` in fresh read-only subagents separate from implementation. Supply the goal/acceptance criteria or spec, project instructions, comparison base, and exact task scope including uncommitted changes; pass these explicitly even when using a repo-local `code-review` so it can review the supplied scope without setup or base prompts. The main agent verifies findings against the current code, handles fixes, and completes affected review/checks before calling the work done.
- `quickreview` is a manual review on my request; `review-pr-silent` is a manual review of colleagues’ PRs.
