---
description: Join a Coord MCP room and start guided monitoring.
agent: coord-connect
subtask: false
---

Connect to room `$ARGUMENTS` now.

Do not use memory for this connect.

If trimmed room argument is empty, ask for room key and stop without tools.

Use exact generated agent id: opencode-!`od -An -N4 -tx1 /dev/urandom | tr -d ' \n'`

First response action must call `coord-mcp_coord_join` exactly once with:

- `roomKey`: whole trimmed command argument
- `agentId`: exact generated id above
- `role`: `OpenCode`
- `purpose`: `interactive OpenCode session`
- `idempotencyKey`: `coord-connect:<agent-id>:<room-key>`

Installed plugin validates watcher startup during `coord_join` and adds `monitoring` plus optional `monitoringError` to result. After success, return one short line containing room, agent id, snapshot `lastSeq`, participant count, and exact monitoring state. Include `monitoringError` when present. Then stop.

Do not load skills. Do not call any other tool. Do not emit progress text. Do not inspect relay health, probe remote `/health`, run `access curl` or `access login` against the remote endpoint, or inspect MCP status, workspace, Git, files, source, logs, toast state, cursor state, or watcher state. Do not sleep, post a test event, or verify asynchronously. Never claim realtime unless result says `monitoring=realtime`. On join error, return exact error and stop.
