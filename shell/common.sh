# Shared environment for Bash and Zsh. Machine choices and secrets stay local.
[ -n "${BASH_VERSION:-}${ZSH_VERSION:-}" ] || return 0
[ -z "${DOTFILES_SHELL_LOADED:-}" ] || return 0
DOTFILES_SHELL_LOADED=1
[ ! -r "$HOME/.config/dotfiles/machine.sh" ] || . "$HOME/.config/dotfiles/machine.sh"
DOTFILES_PROJECTS_ROOT="${DOTFILES_PROJECTS_ROOT:-$HOME/projects}"
export DOTFILES_PROJECTS_ROOT
export PATH="$HOME/.local/bin:$HOME/.bun/bin:$HOME/.cargo/bin:$PATH"
[ ! -r "$HOME/.cargo/env" ] || . "$HOME/.cargo/env"
[ ! -r "$HOME/.atuin/bin/env" ] || . "$HOME/.atuin/bin/env"
dotfiles_workspace() { case ",${DOTFILES_WORKSPACES:-}," in *",$1,"*) return 0 ;; *) return 1 ;; esac; }
if [ -n "${BASH_VERSION:-}${ZSH_VERSION:-}" ]; then
  codg() {
    if ! dotfiles_workspace games; then echo 'games workspace is not installed' >&2; return 1; fi
    if [ "${1:-}" = unity-ab ]; then
      shift
      CODEX_HOME="$HOME/.codex-games" codex -c mcp_servers.unity_anklebreaker.enabled=true -c mcp_servers.unity_coplay.enabled=false "$@"
    else CODEX_HOME="$HOME/.codex-games" codex "$@"; fi
  }
  clag() {
    if ! dotfiles_workspace games; then echo 'games workspace is not installed' >&2; return 1; fi
    local mcp="$HOME/.claude-games/mcp" unity=unity-coplay dir="$PWD"
    local video_root="$DOTFILES_PROJECTS_ROOT/video"
    local -a mcp_configs
    if [ "${1:-}" = unity-ab ]; then unity=unity-anklebreaker; shift; fi
    mcp_configs=("$mcp/base.json" "$mcp/$unity.json")
    while [ "$dir" = "$video_root" ] || [[ "$dir" == "$video_root"/* ]]; do
      if [ -f "$dir/.mcp.json" ]; then mcp_configs+=("$dir/.mcp.json"); break; fi
      dir="$(dirname "$dir")"
    done
    CLAUDE_CONFIG_DIR="$HOME/.claude-games" claude --mcp-config "${mcp_configs[@]}" --strict-mcp-config "$@"
  }
fi
if dotfiles_workspace work; then
  export CLAUDE_PLUGIN_DATA="$HOME/.local/state/dsa"
  alias cla='claude --dangerously-load-development-channels=plugin:dsa@dsa-local'
  alias clax='CLAUDE_CONFIG_DIR=$HOME/.claude-di claude --dangerously-load-development-channels=plugin:dsa@dsa-local'
  alias codx='CODEX_HOME=$HOME/.codex-di codex'
fi
