. "$HOME/.cargo/env"
export CLAUDE_PLUGIN_DATA="$HOME/.local/state/dsa"
alias cla='claude --dangerously-load-development-channels=plugin:dsa@dsa-local'
# company-account twins: separate config homes, same DSA channel
alias clax='CLAUDE_CONFIG_DIR=$HOME/.claude-di claude --dangerously-load-development-channels=plugin:dsa@dsa-local'
alias codx='CODEX_HOME=$HOME/.codex-di codex'
# game-dev home: Blender, Godot and Unity MCPs, no day-job MCPs/skills.
# `codg unity-ab [args]` swaps the Unity MCP to AnkleBreaker for A/B testing.
codg() {
  local -a extra
  if [[ "$1" == unity-ab ]]; then
    extra=(-c mcp_servers.unity_anklebreaker.enabled=true -c mcp_servers.unity_coplay.enabled=false)
    shift
  fi
  CODEX_HOME=$HOME/.codex-games codex "${extra[@]}" "$@"
}

# game-dev Claude home: Blender, Godot, Unity and fal MCPs, no day-job MCPs/skills/plugins.
# `clag unity-ab [args]` swaps the Unity MCP to AnkleBreaker for A/B testing.
# Video projects add the closest .mcp.json from the current project or its parents.
clag() {
  local mcp=$HOME/.claude-games/mcp unity=unity-coplay
  local dir=$PWD video_root=$HOME/projects/video
  local -a mcp_configs
  if [[ "$1" == unity-ab ]]; then unity=unity-anklebreaker; shift; fi
  mcp_configs=("$mcp/base.json" "$mcp/$unity.json")
  if [[ "$dir" == "$video_root" || "$dir" == "$video_root"/* ]]; then
    while [[ "$dir" == "$video_root" || "$dir" == "$video_root"/* ]]; do
      if [[ -f "$dir/.mcp.json" ]]; then
        mcp_configs+=("$dir/.mcp.json")
        break
      fi
      dir=${dir:h}
    done
  fi
  CLAUDE_CONFIG_DIR=$HOME/.claude-games claude \
    --mcp-config "${mcp_configs[@]}" --strict-mcp-config "$@"
}
