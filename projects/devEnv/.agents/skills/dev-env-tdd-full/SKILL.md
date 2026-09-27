---
name: dev-env-tdd-full
description: Strict TDD devEnv workflow adapted from Opencode tdd-full. Use only when the user explicitly requests tests-first/full TDD with behavior tree, RED gate, implementation, verification, and review.
---

# Dev Env TDD Full

Verify current repo is devEnv before running.

Read `references/opencode-command-tdd-full.md` and follow it with Codex tool names.

Key constraints:

- use functional tests through public interfaces
- create behavior tree and task slices before implementation
- require RED evidence before GREEN work when manual gate is requested
- do not weaken tests, skip tests, or mock own modules to bypass logic
- never stage or commit unless explicitly asked
