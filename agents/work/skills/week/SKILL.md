---
name: week
description: Use at the end of a work week ("/week", "weekly review") to synthesize the week's daily notes in the agentdesk vault — wins, lessons, friction → concrete process fixes, next week's focus + one experiment.
user_invocable: true
---

# week

Weekly work review over the agentdesk vault. The highest-leverage step is turning the friction log into process fixes — don't skip it.

## Environment

Same as /morning (vault path, gh prefix quirk, MCP, graceful degradation).

## Steps

1. **Gather**: this week's `01 Daily/*.md` notes; `desk/archive/` items archived this week; merged PRs for the week (`GITHUB_TOKEN= gh search prs`).
2. **Synthesize** into `01 Daily/YYYY-Www.md`:
   - **Wins** — shipped and unblocked things, 1 line each.
   - **Challenges / lessons** — from Reflection lines + what carried over repeatedly.
   - **Friction → fixes** — collect every `friction:` line; cluster; for each cluster propose ONE concrete fix. When the fix is a skill/workflow change, name the exact file (e.g. `~/.claude/skills/morning/SKILL.md`) and the exact edit — offer to apply it right now. This is how the system self-improves.
   - **Direction hit-rate** — how many morning Directions actually finished (rough %, trend vs last week if one exists).
   - **Next week** — proposed focus (max 3) + **one experiment** (a single process change to try, with how we'll know it helped).
3. **Confirm the experiment with me** before writing it as decided.
4. **Commit** (`daily: week YYYY-Www`).
5. **Chat summary — 5 lines max.**

## Iterate

Tune by telling me after a run. If a section was skipped two weeks running, delete it from this file.
