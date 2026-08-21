---
name: feature-ship
description: Use to build a feature end to end, from idea to a merge-ready PR. Invoked with a description, an existing Linear ticket ID, or nothing (then ask). Parallel exploration + architecture proposals, two cross-vendor cold-critic gates (plan, then diff), worktree, implementation, parallel review, fresh-context verify, PR.
user_invocable: true
---

# feature-ship

End-to-end feature development. Do not skip phases.

## Environment

- `gh` fails when `GITHUB_TOKEN` set. Prefix EVERY gh call: `GITHUB_TOKEN= gh ...`
- Repos under `~/projects/<repo>` (platform = bun, backend = npm). Default branch `main`. GitHub user KonstantinKo.
- Linear via MCP (`mcp__claude_ai_Linear__*`).

## Hard constraints

Conventional commits, atomic, no AI attribution, never `--no-verify`, no force-push, work in a git **worktree**, branch `feat/<ticket>-<kebab-title>`, all ticket/PR text in English.

## Verify commands (per repo)

| Repo | Verify |
|---|---|
| platform | `bun run verify` (or light: `bun run check && bun run lint && bun run test:unit`) |
| backend | `npm run verify` (skip integration — needs `sst bind`/AWS; use `npm run typecheck && npm run lint && npm run prettier && npm run test:unit`) |

## Cold critic (used at two gates)

Cross-vendor by default: pipe the material into `codex exec --sandbox read-only -` (prompt + material via stdin; read-only — it must never write; run it from the repo/worktree so it can read real code). codex only runs inside a trusted git directory — if the worktree isn't trusted ("Not inside a trusted directory"), run from the main checkout instead and pipe the diff in. If codex is unavailable or errors, fall back to `claude -p --permission-mode plan --model claude-sonnet-5` (different model than the Opus/Fable default). Always prompt adversarially, and require "no substantive objections" when there are none — no invented findings.

## Orient (graphify — optional, only if a graph already exists)

If `graphify-out/graph.json` exists in the repo, orient with the graph BEFORE grepping — it's a fast symbol map. Prefer precise commands; they're high-signal:
- `graphify explain "<Symbol>"` — exact file + typed import/call edges for a known symbol (best signal).
- `graphify path "<A>" "<B>"` — how two symbols/files connect.
- `graphify query "<question>"` — good at picking on-topic *anchor* symbols for a fuzzy question, but the top of the node list is hub-noise (i18n, Button.svelte, logger). Scan for the named start-nodes/symbols, then `explain` those.

Map, not truth: confirm hot files by reading them (edges tagged `EXTRACTED` = read from source, `INFERRED` = derived). If no graph exists, **skip — do not build one mid-task** (build takes minutes). One-time build is code-only: `graphify <repo> --no-viz` after adding a `.graphifyignore` excluding non-code (`*.md *.json *.yaml *.svg *.png …`), else it errors demanding an LLM key. Output lands in gitignored `graphify-out/`; `graphify hook install` keeps it fresh on commit.

## Phases (in order)

1. **Discovery** — understand the request; ask problem / success criteria / non-goals if unclear; confirm understanding.
2. **Codebase exploration** — orient with graphify first (Orient section) if a graph exists, then launch 2–3 explorer subagents in parallel on different angles (similar existing features, architecture of the area, extension/test patterns), seeding them with the anchor files/symbols the graph surfaced. Each returns 5–10 key files; read them.
3. **Clarifying questions** — one batch covering edge cases, integration points, backward compat, design prefs. Wait for answers.
4. **Architecture** — launch 2–3 architect subagents in parallel with different lenses (minimal / clean / pragmatic). Present side by side, recommend, let me pick.
5. **Plan critic (gate 1)** — before ticket and code: feed the chosen architecture + draft acceptance criteria to the cold critic (section above). It challenges the approach: overbuilt? existing pattern in the codebase unused? integration/backward-compat risk missed? Fold real objections in; if the pick changes, re-present briefly.
6. **Ticket** — ask team/priority/labels/assignee/state in one batch; Linear description with Goal / Acceptance criteria (each a testable assertion) / Approach / Out-of-scope. Skip if a detailed ticket was passed in.
7. **Worktree** off `main`; confirm clean status before editing.
8. **Implementation** — atomic commits, body explains why not what, reference the ticket.
9. **Code review + diff critic (gate 2)** — 3 reviewer subagents in parallel (simplicity / correctness / conventions), plus the cold critic seeing only the diff + ACs. Consolidate, ask me what to fix.
10. **Verify** — fresh-context subagent given only the ACs + the repo's verify commands (table above); reports pass/fail with evidence.
11. **Push, open a ready PR** — `GITHUB_TOKEN= gh pr create`, body Summary / Ticket link / Approach / Test plan. Hand off to `/babysit-prs current`.

## Failure modes

`needs input:` / `failed:` on their own lines.
