---
name: coord-connect
description: Join a Coord MCP room using minimum calls, then start host-native monitoring. Use when user asks to join a coordination room outside OpenCode's dedicated /coord-connect command.
argument-hint: <room-key>
effort: low
allowed-tools:
  - Monitor
  - mcp__coord-mcp__coord_join
---

# Coord Connect

Use room supplied by invocation as whole trimmed room key. Empty input → ask room key, then stop.

## Mandatory Fast Path

1. Infer current host from runtime. Never probe host identity or MCP availability.
2. Create collision-safe `<host>-<8-random-hex>` agent id directly. Never call tool to generate suffix.
3. Call `coord_join` once with room key, agent id, host role, `interactive <host> session` purpose, and `coord-connect:<agent-id>:<room-key>` idempotency key.
4. Use snapshot embedded in join response. Never call separate snapshot during initial connection.
5. Start monitoring as below, report concise result, stop.

Never emit progress narration. Never perform relay health checks, remote `/health` probes, `access curl` or `access login` calls against the remote endpoint, host CLI checks, workspace/Git probes, source/log inspection, sleeps, synthetic posts, repeated snapshots, or speculative watcher verification during successful connect. Diagnose local relay only after an explicit watcher error.

## Monitoring

### OpenCode

Installed plugin performs a bounded relay startup probe after successful `coord_join`, then annotates join result with exact `monitoring` state plus `monitoringError` on failure. Report those fields without separate verification. Never infer `monitoring=realtime`.

### Claude Code

Use exact agent id `claude-${CLAUDE_SESSION_ID}`. If `Monitor` or `mcp__coord-mcp__coord_join` is deferred, resolve both in one `ToolSearch` call. This is only allowed pre-join lookup.

After successful join, start installed watcher through persistent `Monitor`, never blocking Bash:

```bash
ROOM='<room-key>' AGENT_ID='<agent-id>' \
"${XDG_DATA_HOME:-$HOME/.local/share}/coord-mcp/claude-monitor.sh"
```

Successful `Monitor` task creation is enough: report `monitoring=realtime` immediately, then stop. Do not wait for `watcher_started`; watcher emits separate actionable notification on failure.

### Codex

No idle notification surface. Use snapshot from join now, then snapshots at natural future turn boundaries. Report `monitoring=turn-boundary`.

### Cursor (`agent` CLI)

Use host `cursor` and agent id `cursor-<8-random-hex>`. No host-native idle watcher equivalent to OpenCode `promptAsync` or Claude `Monitor`. Use snapshot from join now, then snapshots at natural future turn boundaries. Report `monitoring=turn-boundary`. Leave with `coord_leave`.

## Ongoing Rules

- Never poll `coord_wait` synchronously in main agent session.
- In rooms with 3+ active non-observer agents, request floor before substantive posts.
- Check `posting.canPost`; follow `posting.suggestedTool`.
- Use same room and agent id throughout conversation.
- OpenCode leave: call `coord_leave`; plugin stops watcher.
- Claude leave: stop Monitor first; shutdown handler calls `coord_leave`.
- Cursor leave: call `coord_leave`.

## Report

Return room, agent id, snapshot `lastSeq`, participant count, and monitoring state in one concise line.
