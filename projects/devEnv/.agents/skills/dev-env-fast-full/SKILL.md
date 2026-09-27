---
name: dev-env-fast-full
description: Quick devEnv implementation workflow adapted from Opencode fastFull. Use for current-worktree code, config, docs, command, agent, tooling, or UI changes when the user wants direct implementation with one brief discovery pass, optional browser validation, and tests after implementation.
---

# Dev Env Fast Full

Use this for quick interactive implementation in `/Users/konstantin/projects/devEnv`.

Before work, verify the repo root has `AGENTS.md`, `.project/AGENTS.md`, and `apps/router/docs/spec.md`. If not, stop and say this skill is only for devEnv.

## Required Reads

Read these repo files before edits when relevant:

- `AGENTS.md`
- `.project/AGENTS.md`
- `.project/docs/repoConventions.md`
- `apps/router/docs/spec.md`
- scoped `.project/rules/*.md` and feature docs named by the task

Read copied source refs as needed:

- `references/opencode-command-do-fastFull.md`
- `references/opencode-agent-fastFull.md`
- `references/opencode-agent-briefSearch.md`
- `references/opencode-agent-playwright.md`

## Codex Adaptation

- Preserve the referenced Opencode workflow semantics unless this file says otherwise.
- Treat Opencode `task` delegation as Codex custom subagent spawning.
- Use `dev-env-brief-search` for the one read-only discovery pass.
- Use `dev-env-playwright` for browser checks.
- Do not call Playwright MCP directly from the main workflow.
- Replace Opencode restart notes with: start a new Codex session after editing personal skills, prompts, custom agents, MCP, hooks, or rules.
- Do not persist `.project/docs/work/**` artifacts unless the task itself is workflow/docs work or the user asks.

## Workflow

1. Run exactly one brief search before edits unless the user explicitly forbids subagents.
2. Read target files yourself after the brief search.
3. Ask only blocking product/security/data-shape questions.
4. Implement directly in the main agent.
5. Add or update functional tests when meaningful.
6. Run targeted checks first; run broader checks when risk warrants.
7. Self-review the diff before final.

Never stage or commit unless explicitly asked.
