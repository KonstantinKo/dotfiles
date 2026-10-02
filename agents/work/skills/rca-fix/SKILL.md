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

Conventional commits, atomic (one logical change per commit), no AI attribution in commits, never `--no-verify`, never force-push, work in a git **worktree** (never the main checkout), branch `fix/<ticket-id>-<kebab-title>`, all ticket/PR text in English.

## Verification and publication

Before verification or publication, read [the shared PR workflow](../feature-ship/references/pr-workflow.md). Apply repository checks, templates, existing authorization, attribution, and latest-head review requirements from that reference.

## Cold critic (used at two gates)

At both plan and diff gates, read [cold-critic selection](../feature-ship/references/cold-critic.md). Select by the vendor of the material’s actual authors and report whether the review was cross-vendor or an independent fallback.

## Orient (graphify — optional, only if a graph already exists)

If `graphify-out/graph.json` exists in the repo, orient with the graph BEFORE grepping — it's a fast symbol map. Prefer precise commands; they're high-signal:
- `graphify explain "<Symbol>"` — exact file + typed import/call edges for a known symbol (best signal).
- `graphify path "<A>" "<B>"` — how two symbols/files connect.
- `graphify query "<question>"` — good at picking on-topic *anchor* symbols for a fuzzy question, but the top of the node list is hub-noise (i18n, Button.svelte, logger). Scan for the named start-nodes/symbols, then `explain` those.

Map, not truth: confirm hot files by reading them (edges tagged `EXTRACTED` = read from source, `INFERRED` = derived). If no graph exists, **skip — do not build one mid-incident** (build takes minutes). One-time build is code-only: `graphify <repo> --no-viz` after adding a `.graphifyignore` excluding non-code (`*.md *.json *.yaml *.svg *.png …`), else it errors demanding an LLM key. Output lands in gitignored `graphify-out/`; `graphify hook install` keeps it fresh on commit.

## Phases (in order)

1. **Root-cause analysis.** Orient first (Orient section) if a graph exists, then search local code in the repo, git history/blame on the suspect file, and prior Linear tickets for the same error. Write a one-paragraph hypothesis (file:line, triggering input, why now). Estimate confidence. **If <90%, gather more evidence independently: reproduce, inspect callers/history, and test competing hypotheses. Proceed to a fix only at ≥90% confidence backed by evidence; ask for genuinely unavailable required information when it blocks further investigation.**
2. **Draft a ticket** via Linear under the publication rules above. Use existing metadata and project/team conventions; ask only for missing required metadata. Write a description including a **Validation contract** — a checklist of testable assertions the fix must satisfy. Skip if invoked with an existing detailed ticket.
3. **Worktree** — prepare a dedicated worktree off the synchronized base using the repository’s full setup checklist (env files, context mirror, dependencies, sync). Preserve unrelated/main-checkout state and inspect status before editing.
4. **Fix proposals** — dispatch 1 subagent if single-file/unambiguous, 2 if multi-file/multiple approaches, 3 if architectural. Each returns what-to-change / files / test strategy / risks in <400 words, no code. Choose and proceed when one approach clearly wins; ask only about close or product-level choices.
5. **Plan critic (gate 1)** — before writing any code: feed the chosen proposal + root-cause hypothesis + validation contract to the cold critic (section above). It challenges the approach itself: wrong root cause? simpler fix available? blast radius / callers missed? Fold real objections into the plan; if it credibly undermines the root cause, confidence drops below 90% — go back to phase 1.
6. **Apply** the chosen fix as atomic conventional commits referencing the ticket.
7. **Code review + diff critic (gate 2)** — after the implementation agent reports done, run `code-review` under the global review contract with the root cause/validation contract, project instructions, comparison base, and exact task scope including uncommitted changes. Use fresh read-only Standards/Spec reviewers separate from implementation. Then pipe the diff + root cause + validation contract into the cold critic, prompted adversarially to find what was rationalised away. Verify findings against current code, fix confirmed issues, and repeat affected review/checks.
8. **Verify** — dispatch a fresh-context subagent given the validation contract, exact scope/head, project instructions, and required repository checks. It reports pass/fail with evidence; claim verified only after a green fresh run.
9. **Publish and complete** — push and create/update the PR under the publication rules above, with a conventional title. Monitor repository gates and review feedback on the latest head, using `/babysit-prs current` for follow-up. Call it ready only after the required gates pass and feedback is handled; identify any waiting human review.

## Failure modes

Write `needs input:` on its own line when one piece of info unblocks you. Write `failed:` when structurally impossible.
