#!/usr/bin/env bash
# Optional company profiles; no shell setup, packages, credentials, or MCP bootstrap.
set -euo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
A="$DOTFILES/agents"
launchers=false
case "${1:-}" in
  '') ;;
  --launchers) launchers=true; shift ;;
  --help) echo 'Usage: ./install-work-linux.sh [--launchers]'; exit 0 ;;
  *) echo "Unknown option: $1" >&2; exit 2 ;;
esac
[ "$#" -eq 0 ] || { echo 'Unexpected arguments' >&2; exit 2; }
: "${HOME:?HOME must be set}"
[[ "$HOME" = /* && "$HOME" != / ]] || { echo 'HOME must be an absolute non-root path' >&2; exit 2; }
umask 077
backup_root=''

backup() {
  local path="$1" destination
  if [ -z "$backup_root" ]; then
    mkdir -p "$HOME/.dotfiles-backup"
    backup_root="$(mktemp -d "$HOME/.dotfiles-backup/work-linux.XXXXXXXX")"
  fi
  destination="$backup_root/${path#"$HOME"/}"
  mkdir -p "$(dirname "$destination")"
  mv "$path" "$destination"
  echo "Preserved conflict: $destination"
}

# Never follow a managed directory symlink into another profile or the checkout.
directory() {
  local path="$1"
  if [ -L "$path" ] || { [ -e "$path" ] && [ ! -d "$path" ]; }; then
    echo "Expected a real directory: $path" >&2
    exit 1
  fi
  mkdir -p "$path"
}

link() {
  local source="$1" destination="$2" target
  if [ -L "$destination" ]; then
    target="$(readlink "$destination")"
    [ "$target" != "$source" ] || return 0
    case "$target" in
      "$A"/*) rm "$destination" ;;
      *) backup "$destination" ;;
    esac
  elif [ -e "$destination" ]; then
    backup "$destination"
  fi
  ln -s "$source" "$destination"
}

skills() {
  local source="$1" destination="$2" child
  for child in "$source"/*; do
    [ -d "$child" ] || continue
    [ "${child##*/}" != _archive ] || continue
    link "$child" "$destination/${child##*/}"
  done
}

files() {
  local source="$1" destination="$2" child
  for child in "$source"/*; do
    [ -f "$child" ] || continue
    link "$child" "$destination/${child##*/}"
  done
}

# Validate every container before linking anything.
for path in "$HOME/.agents" "$HOME/.claude-di" "$HOME/.codex-di" \
  "$HOME/.claude-di/skills" "$HOME/.claude-di/commands" \
  "$HOME/.codex-di/skills" "$HOME/.codex-di/prompts"; do
  directory "$path"
done
if "$launchers"; then
  directory "$HOME/.local"
  directory "$HOME/.local/bin"
fi
link "$A/AGENTS.md" "$HOME/.agents/AGENTS.md"
link "$A/work/commands" "$HOME/.agents/commands"
for profile in claude codex; do
  profile_home="$HOME/.$profile-di"
  link "$A/work/AGENTS.md" "$profile_home/AGENTS.md"
  for layer in "$A/shared" "$A/work" "$A/work/di" "$A/work/$profile"; do
    skills "$layer/skills" "$profile_home/skills"
  done
  # Retire only dangling links owned by this checkout.
  for item in "$profile_home/skills"/*; do
    [ -L "$item" ] && [ ! -e "$item" ] || continue
    case "$(readlink "$item")" in "$A"/*) rm "$item" ;; esac
  done
done
link "$A/work/CLAUDE.md" "$HOME/.claude-di/CLAUDE.md"
files "$A/work/commands" "$HOME/.claude-di/commands"
files "$A/work/claude/commands" "$HOME/.claude-di/commands"
files "$A/work/codex/prompts" "$HOME/.codex-di/prompts"

# Harness defaults are portable; existing files and even dangling symlinks stay intact.
if [ ! -e "$HOME/.claude-di/settings.json" ] && [ ! -L "$HOME/.claude-di/settings.json" ]; then
  printf '{}\n' > "$HOME/.claude-di/settings.json"
fi
if [ ! -e "$HOME/.codex-di/config.toml" ] && [ ! -L "$HOME/.codex-di/config.toml" ]; then
  printf '# Company profile: harness defaults; configure remote MCPs separately.\n' > "$HOME/.codex-di/config.toml"
fi

if "$launchers"; then
  for launcher in clax codx; do
    destination="$HOME/.local/bin/$launcher"
    if [ -e "$destination" ] || [ -L "$destination" ]; then
      echo "Kept existing launcher: $destination"
      continue
    fi
    if [ "$launcher" = clax ]; then
      cat > "$destination" <<'LAUNCHER'
#!/usr/bin/env bash
set -euo pipefail
export CLAUDE_CONFIG_DIR="$HOME/.claude-di"
exec claude "$@"
LAUNCHER
    else
      cat > "$destination" <<'LAUNCHER'
#!/usr/bin/env bash
set -euo pipefail
export CODEX_HOME="$HOME/.codex-di"
exec codex "$@"
LAUNCHER
    fi
    chmod 700 "$destination"
  done
fi
printf '%s\n' 'Company profiles installed. Existing authentication and configuration were preserved.' \
  'CLI login, MCP authentication, plugins, and skill-specific tools are separate readiness steps.'
