---
name: pr-linear-refresh
description: Background loop (run via /loop) that keeps the cockpit note in the agentdesk vault in sync with my open authored GitHub PRs and my active Linear issues. Daytime only (07:00–22:00 Europe/Berlin). Fetches, diffs against the note, and writes ONLY when something changed — no-op runs write nothing.
user_invocable: true
---

# pr-linear-refresh

Keep one living status note in sync with my open PRs + active Linear issues. Write only on change.

## Environment

- `gh` fails when `GITHUB_TOKEN` set. Prefix EVERY gh call: `GITHUB_TOKEN= gh ...`
- GitHub user: KonstantinKo. Repos: `~/projects/platform`, `~/projects/backend`. Default branch `main`.
- Linear via MCP (`mcp__claude_ai_Linear__*`). Fetch strategy and filtering rules: step 2 + Known quirks.
- Vault: `/Users/konstantin/projects/obsidian/agentdesk` (work brain, git — follow its root `CLAUDE.md` contract).
  - **Target note:** `00 Dashboard/Cockpit.md` — read/write via plain filesystem tools (the Obsidian REST MCP is bound to a different vault; don't use it here). Quote the path (space in `00 Dashboard`).

## Steps

0. **Quiet-hours guard.** `TZ=Europe/Berlin date +%H` — if before 07 or 22+, stop immediately: no fetches, no writes. When self-pacing the loop overnight, schedule the next wake-up for ~07:00 rather than polling through the night.
1. **Resolve the note.** Read `00 Dashboard/Cockpit.md` from the vault. If missing, create from the skeleton below.
2. **Fetch in parallel:**
   - PRs — one `GITHUB_TOKEN= gh pr list --author KonstantinKo --state open --json number,title,url,reviewDecision` call per repo.
   - Linear issues — one `mcp__claude_ai_Linear__list_issues(assignee: "me", state: <type>, limit: 250, includeArchived: false)` call per open state type: `started`, `unstarted`, `backlog`, `triage`. Follow `cursor` until `hasNextPage` is false on each (rare); merge and dedup by `id`. Completed/canceled/archived issues are never fetched. Fallback only if the state-type filter stops working: paginate a single `list_issues(assignee: "me", limit: 250, includeArchived: false)` via `cursor` until exhausted, then filter client-side. Consider offloading this whole fetch to a cheap subagent that returns just the normalized open-issue list — keeps the loop's context clean.
3. **Render tables:**
   - PRs: number, status icon (✅ approved / 🔴 changes requested / ⏳ review pending), title, **Posted** — grouped by repo.
   - Issues: id, status, priority, title — ordered by priority.
   - **Posted column** (was the PR announced on Slack?): sticky — a PR already marked 📣 in the note stays 📣, never re-search. For unmarked PRs only, search Slack for the PR URL (`mcp__claude_ai_Slack__slack_search_public_and_private`); found → 📣, not found → `—`. If Slack MCP is unavailable this run, carry over the existing values unchanged.
4. **Diff** against the tables currently in the note. **If identical, STOP and write nothing.**
5. **On change:** update both tables in place, append a timestamped log line describing what changed. Mirror any "changes requested" PR into a **Blockers** section.
6. **Commit** (change runs only): `git -C /Users/konstantin/projects/obsidian/agentdesk add -A && git ... commit -m "dashboard: cockpit refresh"`. Push if a remote exists (merge, never rebase); no remote → local commit is enough.

## Skeleton (if note missing)

```markdown
# Cockpit

## PRs
_(none)_

## Linear Issues
_(none)_

## Blockers
_(none)_

## Log
```

## Known quirks

- Filter active/closed on the **top-level `statusType`** field (`completed`/`canceled`/`started`/`unstarted`/`backlog`); `statusType: "duplicate"` counts as closed. Never filter on the nested `state.name` — top-level `status` is just the display name.
- Linear priority can be an int or an object — normalize before sorting, or the sort throws.
- Stability criterion: two consecutive refreshes with no real Linear change must produce byte-identical Cockpit tables — any phantom add/drop means the fetch or filter is wrong.
- Large Linear responses: parse from a temp file, don't read inline, if a call returns huge payloads.
- `00 Dashboard` contains a space — quote paths in shell operations.
- Historical: this note previously lived in the personal Fortress vault (`Work/PR & Linear Status.md`, OneDrive). That copy is abandoned in place — never write to it.
