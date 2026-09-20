---
name: evening
description: Use at the end of a work day ("/evening", "close out my day", "evening review") to close today's daily note in the agentdesk vault — reconcile what actually happened, log friction, short reflection.
user_invocable: true
---

# evening

Close today's work-day note. Work scope only — agentdesk vault, never the personal one.

## Environment

Same as /morning (vault path, gh prefix quirk, MCP servers, graceful degradation).

## Steps

1. **Read today's note** (`01 Daily/YYYY-MM-DD.md`). Missing → offer to run a minimal /morning retroactively instead.
2. **Gather what actually happened**, in parallel:
   - PRs merged/opened/reviewed today (`GITHUB_TOKEN= gh search prs --author KonstantinKo --merged-at YYYY-MM-DD` + review activity).
   - Linear issues that changed state today.
   - Desk: items added/answered/archived today (file mtimes + `updated` headers).
3. **Reconcile the Log** — append a compact end-of-day block: shipped / reviewed / decided / desk movements. Tick Directions that actually finished; carry unfinished ones forward verbatim (they seed tomorrow's /morning).
4. **Friction line** — ask me one question: "What dragged today?" One line into `## Log` prefixed `friction:`. These accumulate for /week. If nothing dragged, `friction: none` is a fine answer.
5. **Reflection** — ask me exactly two things in one message: energy (1–5) and one lesson. Write both under `## Reflection`. Don't interrogate; blank answers are allowed.
6. **Commit** (`daily: close YYYY-MM-DD`).
7. **Chat summary — 3 lines max**: shipped, carried over, desk state.

## Iterate

Same rule as /morning — tune sections by telling me after a run.
