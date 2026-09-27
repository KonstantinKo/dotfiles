#!/usr/bin/env bash
set -euo pipefail

python3 -c '
import json, sys
data = json.load(sys.stdin)
tool = data.get("tool_name", "")
if not tool.startswith("mcp__higgsfield__"):
    sys.exit(0)
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": (
        "Higgsfield cloud MCP call. Review the exact operation. "
        "Paid calls require a CLI cost estimate, current balance, and explicit approval for this call."
    ),
}}))
'
