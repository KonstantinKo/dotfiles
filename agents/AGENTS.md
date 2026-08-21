# Global preferences

## Delegation & verification

- Never invoke Claude Code in programmatic/non-interactive mode (`claude -p`, Claude SDK, or Anthropic API) because this incurs metered API usage. For programmatic reviews, critics, or delegated runs, use `opencode run` with a deliberately chosen capable model and reasoning variant.
- For substantial coding sessions, orchestrate via subagents (implementation, verification, review) and keep the main context clean. Prefer short bounded reasoning; checkpoint through tool calls.
- Before spawning an external CLI coding agent (Codex etc.), ask Konstantin which engine and service tier to use — never assume a priority/paid tier.
- On repos with remotes, always code in a dedicated worktree, prepared with the repo's full worktree-setup checklist (env files, context mirror, deps, sync). Local-only repos may be edited directly.
- Prove behavioral/visual claims with a real repro; for design fidelity compare matched rendered screenshots, never markup alone. Playwright screenshots always go to temp dirs, never into git.
- For wording/template-only diffs, skip broad local test investigation — focused validation, then CI.

## PRs & GitHub

- Never enable auto-merge unless explicitly asked.
- No dev-diary comments anywhere (code, PRs, issues): don't narrate changes, cite prior bugs, or reference PR/spec line numbers.
- Don't reply to accepted/actioned review comments (just fix); reply briefly only to ones you skip.
- Posting anything in Konstantin's name (GitHub/Linear/Slack) requires an explicit request and the footer "- Written by AI (experimental harness)".
- Keep diffs scoped to the task; no incidental fixes buried in unrelated PRs.
- When pre-commit hooks rewrite staged files, include those changes; never bypass hooks.
- Run a CodeRabbit CLI review/fix cycle before pushing PR changes when available; skip it when the coderabbitai bot already reviewed the current head.

## Misc

- Don't prefix bash commands with `cd` to the current working directory.
- Team secret store is Bitwarden (not 1Password); devcontainers get secrets via env vars.
- Personal CLI tools live in standalone repos under ~/projects, not in dotfiles/settings repos.

## agentdesk — log loose ends

When you finish a work session, before you stop: if you are **blocked** on Konstantin, **finished but with loose ends**, or **found follow-ups** that don't fit the main task, write a work item following the producer contract at `/Users/konstantin/projects/obsidian/agentdesk/desk/PRODUCER.md`. Read that file for the exact location, filename, and header shape.

If your work is fully done and verified with nothing to flag, write nothing — silence means clean.
