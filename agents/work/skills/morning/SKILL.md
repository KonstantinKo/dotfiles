---
name: morning
description: Use at the start of a work day ("/morning", "plan my day", "morning standup prep") to seed today's daily note in the agentdesk vault — PR/Linear cockpit, Slack recap, calendar, desk triage counts, proposed directions and focus blocks.
user_invocable: true
---

# morning

Seed today's work-day note. Work scope only — this writes to the agentdesk vault, never the personal one.

## Environment

- Vault: `/Users/konstantin/projects/obsidian/agentdesk` (git — commit per vault CLAUDE.md).
- Today's note: `01 Daily/YYYY-MM-DD.md`. If it already exists, update sections in place — never blow away Log/Reflection content.
- `gh` fails when `GITHUB_TOKEN` set — prefix every call: `GITHUB_TOKEN= gh ...`. GitHub user KonstantinKo, repos `~/projects/platform`, `~/projects/backend`.
- Linear via MCP (`mcp__claude_ai_Linear__*`), Slack via MCP (`mcp__claude_ai_Slack__*`), Calendar via MCP (`mcp__claude_ai_Google_Calendar__*`). Any of them unavailable → render the section as `_unavailable_` and move on; never block the whole note on one source.

## Steps

1. **Gather in parallel** (subagents for the slow ones; keep it snappy):
   - Open authored PRs: `GITHUB_TOKEN= gh pr list --author KonstantinKo --state open --json number,title,url,reviewDecision` per repo.
   - Active Linear issues assigned to me — one `mcp__claude_ai_Linear__list_issues(assignee: "me", state: <type>, limit: 250, includeArchived: false)` call per open state type (`started`, `unstarted`, `backlog`, `triage`); follow `cursor` while `hasNextPage` (rare); merge, dedup by `id`, order by priority. Completed/canceled/archived issues are never fetched.
     - Fallback only if the state-type filter stops working: paginate a single `list_issues(assignee: "me", limit: 250, includeArchived: false)` via `cursor` until exhausted, then filter client-side.
     - Filter active/closed on the top-level `statusType` (`completed`/`canceled`/`duplicate` = closed), never the nested `state.name` — top-level `status` is just the display name. `priority` can be an int or an object — normalize before sorting, or the sort throws.
     - Stability: two fetches with no real Linear change must yield identical issue sets; when opportunistically refreshing Cockpit.md, that means byte-identical tables (no phantom add/drop).
   - Slack recap since yesterday ~17:00: DMs + mentions addressed to me; 1 line each, only things needing action or awareness.
   - Today's calendar events (Google Calendar, primary calendar).
   - Desk triage: glob `desk/items/*.md`, read headers only. Count by status; list `needs-input` items (title + priority).
   - Yesterday's daily note (most recent `01 Daily/*.md` before today): unfinished Directions, last Log lines.
   - `00 Dashboard/Upcoming.md` — This Week section; plus grep vault for `remind-on: <today or earlier>`.
2. **Write the note** (template below). Directions: propose 3, derived from blockers, desk needs-input, review-requested PRs, and yesterday's unfinished — mark each with its source so I can veto fast. The Cockpit section is just an embed of `00 Dashboard/Cockpit.md` (kept fresh by /pr-linear-refresh) — still fetch PRs/Linear yourself for deriving Directions, but don't render duplicate tables; opportunistically refresh Cockpit.md itself if it's stale.
3. **Propose 1–2 focus blocks** (execution work only, not meetings) fitted around today's calendar.
4. **Commit** (`daily: seed YYYY-MM-DD`).
5. **Chat summary — max ~6 lines**: directions, blockers, desk needs-input count, first meeting, proposed focus blocks. No walls of text; the note holds the detail.

## Template

```markdown
---
type: daily
date: YYYY-MM-DD
---

# Mon, DD MMM YYYY

## Directions
- [ ] …

## Blockers

## Desk
_N items: X needs-input, Y active, Z done. Top: [[desk/items/<file>|<plain title>]]_

## Cockpit
![[00 Dashboard/Cockpit]]

## Meetings
- HH:MM <name> — <one-line prep>

## Upcoming (pulled)

## Log

## Reflection
```

## Iterate

After each run, tell me what was noise and what was missing — update this file immediately. Sections earn their place by being read.
