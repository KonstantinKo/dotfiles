#!/usr/bin/env bash
# Bring a secondary Claude Code config home up to parity with ~/.claude.
# Run AFTER logging in once:  CLAUDE_CONFIG_DIR=~/.claude-di claude  →  /login
# Usage: bootstrap-home.sh ~/.claude-di
#        bootstrap-home.sh ~/.claude-games --settings ../../games/claude/settings.json --plugins-only
#   --settings <file>  drive the plugin set from another settings.json
#   --plugins-only     skip copying user-scope MCP servers from ~/.claude (games home:
#                      its MCPs come from agents/games/claude/mcp via clag --mcp-config)
set -euo pipefail

HOME_DIR="${1:?usage: bootstrap-home.sh <claude-config-dir> [--settings <file>] [--plugins-only]}"
HOME_DIR="${HOME_DIR/#\~/$HOME}"
shift
export CLAUDE_CONFIG_DIR="$HOME_DIR"
SETTINGS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/settings.json"
PLUGINS_ONLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --settings) SETTINGS="$2"; shift 2 ;;
    --plugins-only) PLUGINS_ONLY=1; shift ;;
    *) echo "unknown argument: $1"; exit 2 ;;
  esac
done

[ -f "$HOME_DIR/.claude.json" ] || { echo "no $HOME_DIR/.claude.json yet — launch claude there and log in first"; exit 1; }

# 1. marketplaces + plugins, driven by the shared settings.json.
#    Marketplace names are derived by Claude from the source, so match by source, not name.
python3 - "$SETTINGS" "$HOME_DIR/plugins/known_marketplaces.json" <<'PY' | while read -r kind name src; do
import json,sys
s=json.load(open(sys.argv[1]))
try: known=json.load(open(sys.argv[2]))
except Exception: known={}
def key(src): return src.get("repo") or src.get("path") or ""
have={key(v.get("source",{})) for v in known.values()}
for name,m in s.get("extraKnownMarketplaces",{}).items():
    if key(m["source"]) not in have: print("marketplace",name,key(m["source"]))
for p,on in s.get("enabledPlugins",{}).items():
    if on: print("plugin",p,"-")
PY
  case "$kind" in
    marketplace) claude plugin marketplace add "$src" || true ;;
    plugin)
      claude plugin list 2>/dev/null | grep -q "$name" \
        || claude plugin install "$name" --scope user || true ;;
  esac
done

[ "$PLUGINS_ONLY" = 1 ] && { echo "done (plugins only)."; exit 0; }

# 2. user-scope MCP servers: copy from ~/.claude, then add the company-only ones
python3 - "$HOME/.claude.json" "$HOME_DIR/.claude.json" <<'PY'
import json,sys
src=json.load(open(sys.argv[1])); dstp=sys.argv[2]; dst=json.load(open(dstp))
mcp=dict(dst.get("mcpServers",{}))
for k,v in src.get("mcpServers",{}).items(): mcp.setdefault(k,v)
mcp.setdefault("linear",{"type":"http","url":"https://mcp.linear.app/mcp"})
dst["mcpServers"]=mcp
json.dump(dst,open(dstp,"w"),indent=2)
print("mcpServers:",", ".join(sorted(mcp)))
PY

echo "done. Next: start claude there once, run /mcp to OAuth Linear (and Slack if it shows up as a claude.ai connector)."
