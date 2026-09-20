---
name: rca-fix
description: Use for an end-to-end production incident — root-cause, fix, and PR. Invoked with a pasted error log, a monitoring URL, or an existing Linear ticket ID. Root-causes behind a 90% confidence gate, fixes in a worktree, two cross-vendor cold-critic gates (plan, then diff) + fresh-context verify, opens PR.
user_invocable: true
---

# rca-fix

End-to-end production-incident handler. Do not skip phases.

## Environment

- `gh` fails when `GITHUB_TOKEN` set. Prefix EVERY gh call: `GITHUB_TOKEN= gh ...`
- Repos under `~/projects/<repo>` (platform = bun, backend = npm). Default branch `main`. GitHub user KonstantinKo.
- Linear via MCP (`mcp__claude_ai_Linear__*`).

## Hard constraints (every phase)

Conventional commits, atomic (one logical change per commit), no AI attribution in commits or PR bodies, never `--no-verify`, never force-push, work in a git **worktree** (never the main checkout), branch `fix/<ticket-id>-<kebab-title>`, all ticket/PR text in English.

## Verify commands (per repo)

| Repo | Verify |
|---|---|
| platform | `bun run verify` (or light: `bun run check && bun run lint && bun run test:unit`) |
| backend | `npm run verify` (skip integration — needs `sst bind`/AWS; use `npm run typecheck && npm run lint && npm run prettier && npm run test:unit`) |

## Cold critic (used at two gates)

Cross-vendor by default: from the worktree, pipe the material into `codex exec --sandbox read-only -` (prompt + material via stdin; read-only — it must never write). codex only runs inside a trusted git directory — if the worktree isn't trusted ("Not inside a trusted directory"), run from the main checkout instead and pipe the diff in. If codex is unavailable or errors, fall back to `claude -p --permission-mode plan --model claude-sonnet-5` (different model than the Opus/Fable default that wrote the fix). Always prompt adversarially: find what was rationalised away, attack the weakest assumption, and say "no substantive objections" if there are none — do not invent findings.

## Orient (graphify — optional, only if a graph already exists)

If `graphify-out/graph.json` exists in the repo, orient with the graph BEFORE grepping — it's a fast symbol map. Prefer precise commands; they're high-signal:
- `graphify explain "<Symbol>"` — exact file + typed import/call edges for a known symbol (best signal).
- `graphify path "<A>" "<B>"` — how two symbols/files connect.
- `graphify query "<question>"` — good at picking on-topic *anchor* symbols for a fuzzy question, but the top of the node list is hub-noise (i18n, Button.svelte, logger). Scan for the named start-nodes/symbols, then `explain` those.

Map, not truth: confirm hot files by reading them (edges tagged `EXTRACTED` = read from source, `INFERRED` = derived). If no graph exists, **skip — do not build one mid-incident** (build takes minutes). One-time build is code-only: `graphify <repo> --no-viz` after adding a `.graphifyignore` excluding non-code (`*.md *.json *.yaml *.svg *.png …`), else it errors demanding an LLM key. Output lands in gitignored `graphify-out/`; `graphify hook install` keeps it fresh on commit.

## Phases (in order)

1. **Root-cause analysis.** Orient first (Orient section) if a graph exists, then search local code in the repo, git history/blame on the suspect file, and prior Linear tickets for the same error. Write a one-paragraph hypothesis (file:line, triggering input, why now). Estimate confidence. **If <90%, STOP and ask for the missing info — never proceed on a guess.**
2. **Draft a ticket** (ask me team/priority/labels/assignee/state in one batch) via Linear, with a description template including a **Validation contract** — a checklist of testable assertions the fix must satisfy. Skip if invoked with an existing detailed ticket.
3. **Worktree** off `main` (`git worktree add`).
4. **Fix proposals** — dispatch 1 subagent if single-file/unambiguous, 2 if multi-file/multiple approaches, 3 if architectural. Each returns what-to-change / files / test strategy / risks in <400 words, no code. Present and let me pick.
5. **Plan critic (gate 1)** — before writing any code: feed the chosen proposal + root-cause hypothesis + validation contract to the cold critic (section above). It challenges the approach itself: wrong root cause? simpler fix available? blast radius / callers missed? Fold real objections into the plan; if it credibly undermines the root cause, confidence drops below 90% — go back to phase 1.
6. **Apply** the chosen fix as atomic conventional commits referencing the ticket.
7. **Diff critic (gate 2)** — pipe the diff + root cause + validation contract into the cold critic, prompted adversarially to find what was rationalised away. Fold in real findings.
8. **Verify** — dispatch a fresh-context subagent given ONLY the validation contract + the repo's verify commands (table above). It runs them and reports pass/fail with evidence. Don't claim "verified" without a green fresh run.
9. **Push, open a ready PR** — `GITHUB_TOKEN= gh pr create`, conventional title, body with Summary / Root cause / Test plan, no AI attribution. Then hand off to `/babysit-prs current` to watch CI.

## Failure modes

Write `needs input:` on its own line when one piece of info unblocks you. Write `failed:` when structurally impossible.
