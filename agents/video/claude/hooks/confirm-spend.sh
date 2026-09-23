#!/usr/bin/env bash
# PreToolUse hook (matcher: Bash). Turns any backlot spend command carrying --yes/--force
# into a Claude Code permission prompt that shows the estimate, so the user confirms spend.
PY=$(cat <<'EOF'
import json, re, shlex, subprocess, sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
cmd = (data.get("tool_input") or {}).get("command") or ""
spend = re.compile(r"(?<![\w/.-])backlot\s+(gen|tts|captions|batch|recover)\b")
if not spend.search(cmd) or not re.search(r"(^|\s)--(yes|force)(=\S+)?(\s|$)", cmd):
    sys.exit(0)

estimate = ""
segment = next((s for s in re.split(r"&&|\|\||;|\|", cmd) if spend.search(s)), cmd).strip()
try:
    toks = shlex.split(segment)
    i = toks.index("backlot")
    toks = [t for t in toks[i:] if t not in ("--yes", "--force")]
    if "--dry-run" not in toks:
        toks.append("--dry-run")
    r = subprocess.run(toks, capture_output=True, text=True, timeout=45, cwd=data.get("cwd") or None)
    estimate = (r.stdout + r.stderr).strip()
except Exception as e:
    estimate = f"estimate unavailable: {e}"

reason = f"backlot spend: this bills the account.\n{segment}\n{estimate}".strip()
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": reason}}))
EOF
)
exec python3 -c "$PY"
