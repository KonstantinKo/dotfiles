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

Conventional commits, atomic, no AI attribution in commits, never `--no-verify`, no force-push, work in a git **worktree**, branch `feat/<ticket>-<kebab-title>`, all ticket/PR text in English.

## Verification and publication

Before verification or publication, read [the shared PR workflow](references/pr-workflow.md). Apply repository checks, templates, existing authorization, attribution, and latest-head review requirements from that reference.

## Cold critic (used at two gates)

At both plan and diff gates, read [cold-critic selection](references/cold-critic.md). Select by the vendor of the material’s actual authors and report whether the review was cross-vendor or an independent fallback.

## Orient (graphify — optional, only if a graph already exists)

If `graphify-out/graph.json` exists in the repo, orient with the graph BEFORE grepping — it's a fast symbol map. Prefer precise commands; they're high-signal:
- `graphify explain "<Symbol>"` — exact file + typed import/call edges for a known symbol (best signal).
- `graphify path "<A>" "<B>"` — how two symbols/files connect.
- `graphify query "<question>"` — good at picking on-topic *anchor* symbols for a fuzzy question, but the top of the node list is hub-noise (i18n, Button.svelte, logger). Scan for the named start-nodes/symbols, then `explain` those.

Map, not truth: confirm hot files by reading them (edges tagged `EXTRACTED` = read from source, `INFERRED` = derived). If no graph exists, **skip — do not build one mid-task** (build takes minutes). One-time build is code-only: `graphify <repo> --no-viz` after adding a `.graphifyignore` excluding non-code (`*.md *.json *.yaml *.svg *.png …`), else it errors demanding an LLM key. Output lands in gitignored `graphify-out/`; `graphify hook install` keeps it fresh on commit.

## Phases (in order)

1. **Discovery** — establish the problem, success criteria, and non-goals from the request and available context. Carry existing answers forward; ask only for required information that cannot be determined independently.
2. **Codebase exploration** — orient with graphify first (Orient section) if a graph exists, then launch 2–3 explorer subagents in parallel on different angles (similar existing features, architecture of the area, extension/test patterns), seeding them with the anchor files/symbols the graph surfaced. Each returns 5–10 key files; read them.
3. **Clarify** — investigate edge cases, integration points, and backward compatibility. Proceed on clear choices; ask one focused batch only about close or product-level decisions or genuinely missing required information. Wait only for answers that block dependent work.
4. **Architecture** — launch 2–3 architect subagents in parallel with different lenses (minimal / clean / pragmatic). Choose and proceed when one approach clearly wins; present close or product-level choices for the user.
5. **Plan critic (gate 1)** — before ticket and code: feed the chosen architecture + draft acceptance criteria to the cold critic (section above). It challenges the approach: overbuilt? existing pattern in the codebase unused? integration/backward-compat risk missed? Fold real objections in; proceed on clear improvements and ask only if objections create a close or product-level decision.
6. **Ticket** — use existing ticket metadata and repository/team conventions; ask only for missing required metadata. Publish under the authorization rules above, with a Linear description containing Goal / Acceptance criteria (each a testable assertion) / Approach / Out-of-scope. Skip if a detailed ticket was passed in.
7. **Worktree** — prepare a dedicated worktree off the synchronized base using the repository’s full setup checklist (env files, context mirror, dependencies, sync). Preserve unrelated/main-checkout state and inspect status before editing.
8. **Implementation** — atomic commits, body explains why not what, reference the ticket.
9. **Code review + diff critic (gate 2)** — after the implementation agent reports done, run `code-review` under the global review contract with the goal/ACs, project instructions, comparison base, and exact task scope including uncommitted changes. Use its fresh read-only Standards/Spec reviewers as this stage’s reviewers. Also run the cold critic with the bounded diff/ACs packet and relevant project constraints from the shared reference. Verify findings against current code, fix confirmed issues, and repeat affected review/checks; ask me only about unresolved product-level choices.
10. **Verify** — fresh-context subagent given the ACs, exact scope/head, project instructions, and required repository checks; reports pass/fail with evidence.
11. **Publish and complete** — push and create/update the PR under the publication rules above. Monitor repository gates and review feedback on the latest head, using `/babysit-prs current` for follow-up. Call it ready only after the required gates pass and feedback is handled; identify any waiting human review.

## Failure modes

`needs input:` / `failed:` on their own lines.
