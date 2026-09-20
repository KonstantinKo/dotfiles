#!/usr/bin/env bash
# Idempotent dotfiles installer. Re-runnable; never deletes content.
# Conflicting real files/dirs are moved to ~/.dotfiles-backup/<timestamp>/<path>.
#
# Layout under agents/: the folder tells you where something ends up.
#   shared/   every agent home (work and games)
#   work/     day-job homes: ~/.claude, ~/.claude-di, ~/.codex, ~/.codex-di, OpenCode, Cursor
#   work/di/  company-account homes only (~/.claude-di, ~/.codex-di)
#   work/<tool>/  one harness only (claude | codex | opencode | cursor)
#   games/    game-dev homes: ~/.codex-games, ~/.claude-games
set -euo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
A="$DOTFILES/agents"
BACKUP_ROOT="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)"

CLAUDE_HOMES=("$HOME/.claude" "$HOME/.claude-di")
CODEX_HOMES=("$HOME/.codex" "$HOME/.codex-di")
DI_HOMES=("$HOME/.claude-di" "$HOME/.codex-di")
CODEX_GAMES_HOME="$HOME/.codex-games"
CLAUDE_GAMES_HOME="$HOME/.claude-games"
OPENCODE="$HOME/.config/opencode"
CURSOR="$HOME/.cursor"
VENDOR_CACHE="$HOME/.cache/dotfiles/vendor"

backup() {
  local path="$1" rel="${1#$HOME/}" dst
  dst="$BACKUP_ROOT/$rel"
  mkdir -p "$(dirname "$dst")"
  mv "$path" "$dst"
  echo "backed-up $path -> $dst"
}

safe_symlink() {
  local src="$1" dst="$2"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    echo "ok      $dst"
    return
  fi
  if [ -e "$dst" ] && [ ! -L "$dst" ]; then
    if [ -d "$dst" ] && [ -z "$(ls -A "$dst")" ]; then rmdir "$dst"; else backup "$dst"; fi
  fi
  mkdir -p "$(dirname "$dst")"
  ln -sfn "$src" "$dst"
  echo "linked  $dst -> $src"
}

prepare_directory() {
  local dir="$1" managed_link="${2:-}"
  if [ -L "$dir" ]; then
    if [ -n "$managed_link" ] && [ "$(readlink "$dir")" = "$managed_link" ]; then
      rm "$dir"
    else
      backup "$dir"
    fi
  elif [ -e "$dir" ] && [ ! -d "$dir" ]; then
    backup "$dir"
  fi
  mkdir -p "$dir"
}

# Drop symlinks in a managed dir that dangle, or that point into this repo at a
# path that no longer exists (skill moved to another area, archived, deleted).
clean_stale_links() {
  local dir="$1" link src
  [ -d "$dir" ] || return 0
  for link in "$dir"/* "$dir"/.[!.]*; do
    [ -L "$link" ] || continue
    src="$(readlink "$link")"
    if [ ! -e "$link" ]; then
      rm "$link"; echo "unlinked $link (dangling -> $src)"
    fi
  done
}

# link_children <src-dir> <dst-dir>...   every subdirectory of src (skills)
link_children() {
  local src="$1" child dst; shift
  for child in "$src"/*/; do
    child="${child%/}"
    [ -d "$child" ] || continue
    [ "$(basename "$child")" = "_archive" ] && continue
    for dst in "$@"; do safe_symlink "$child" "$dst/$(basename "$child")"; done
  done
}

# link_files <src-dir> <dst-dir>...   every regular file of src (commands, prompts)
link_files() {
  local src="$1" f dst; shift
  for f in "$src"/*; do
    [ -f "$f" ] || continue
    for dst in "$@"; do safe_symlink "$f" "$dst/$(basename "$f")"; done
  done
}

# --- shell & git ---
for f in .zshrc .bashrc .profile .npmrc .gitconfig; do
  safe_symlink "$DOTFILES/$f" "$HOME/$f"
done

# --- neovim ---
safe_symlink "$DOTFILES/dotconfig/nvim" "$HOME/.config/nvim"

# --- ~/.agents: harness-neutral instructions + commands ---
# (~/.agents/skills is intentionally NOT used: Codex, OpenCode and Cursor all scan it,
#  which made every work skill leak into the games home. Skills go per home instead.)
prepare_directory "$HOME/.agents" "$A"
safe_symlink "$A/AGENTS.md" "$HOME/.agents/AGENTS.md"
safe_symlink "$A/work/commands" "$HOME/.agents/commands"
if [ -d "$HOME/.agents/skills" ]; then
  for link in "$HOME/.agents/skills"/*; do
    [ -L "$link" ] || continue
    case "$(readlink "$link")" in "$DOTFILES"/*) rm "$link"; echo "retired $link" ;; esac
  done
  rmdir "$HOME/.agents/skills" 2>/dev/null && echo "removed $HOME/.agents/skills (now per home)" || true
fi

# --- instruction files ---
for home in "${CLAUDE_HOMES[@]}"; do safe_symlink "$A/CLAUDE.md" "$home/CLAUDE.md"; done
for home in "${CODEX_HOMES[@]}"; do safe_symlink "$A/AGENTS.md" "$home/AGENTS.md"; done
safe_symlink "$A/AGENTS.md" "$OPENCODE/AGENTS.md"
safe_symlink "$A/AGENTS.md" "$CURSOR/AGENTS.md"
safe_symlink "$A/games/AGENTS.md" "$CODEX_GAMES_HOME/AGENTS.md"
safe_symlink "$A/games/AGENTS.md" "$CLAUDE_GAMES_HOME/AGENTS.md"
safe_symlink "$A/games/CLAUDE.md" "$CLAUDE_GAMES_HOME/CLAUDE.md"

# --- claude (all homes share settings; auth/plugins/sessions stay per home) ---
for home in "${CLAUDE_HOMES[@]}"; do
  safe_symlink "$A/work/claude/settings.json" "$home/settings.json"
  safe_symlink "$A/work/claude/statusline.sh" "$home/statusline.sh"
done

# --- claude games home: own settings, own MCP set (loaded via clag --mcp-config) ---
safe_symlink "$A/games/claude/settings.json" "$CLAUDE_GAMES_HOME/settings.json"
safe_symlink "$A/work/claude/statusline.sh"  "$CLAUDE_GAMES_HOME/statusline.sh"
safe_symlink "$A/games/claude/mcp"           "$CLAUDE_GAMES_HOME/mcp"

# --- codex: seed per-home config.toml once (Codex rewrites it afterwards) ---
seed_once() {
  local src="$1" dst="$2"
  [ -e "$dst" ] && return 0
  mkdir -p "$(dirname "$dst")"; cp "$src" "$dst"; chmod 600 "$dst"; echo "seeded  $dst"
}
seed_once "$A/work/codex/config.di.toml" "$HOME/.codex-di/config.toml"
seed_once "$A/games/codex/config.toml"   "$CODEX_GAMES_HOME/config.toml"
safe_symlink "$A/games/bin/fal-mcp-codg" "$HOME/.local/bin/fal-mcp-codg"

# --- opencode ---
for f in opencode.jsonc opencode-notifier.json package.json; do
  safe_symlink "$A/work/opencode/$f" "$OPENCODE/$f"
done
safe_symlink "$A/work/opencode/plugins" "$OPENCODE/plugins"
safe_symlink "$A/work/opencode/agents"  "$OPENCODE/agents"

# --- cursor ---
safe_symlink "$A/work/cursor/mcp.json" "$CURSOR/mcp.json"

# --- skills ---
# Claude reads only <home>/skills. Codex reads <home>/skills. OpenCode and Cursor
# read their own dir plus ~/.claude/skills and ~/.codex/skills, so work skills
# reach them without extra links.
SKILL_DIRS=("${CLAUDE_HOMES[@]/%//skills}" "${CODEX_HOMES[@]/%//skills}" "$CODEX_GAMES_HOME/skills" "$CLAUDE_GAMES_HOME/skills" "$OPENCODE/skills" "$CURSOR/skills")
for d in "${SKILL_DIRS[@]}"; do clean_stale_links "$d"; done

link_children "$A/shared/skills"        "${SKILL_DIRS[@]}"
link_children "$A/work/skills"          "${CLAUDE_HOMES[@]/%//skills}" "${CODEX_HOMES[@]/%//skills}"
link_children "$A/work/di/skills"       "${DI_HOMES[@]/%//skills}"
link_children "$A/work/opencode/skills" "$OPENCODE/skills"
[ -d "$A/work/cursor/skills" ] && link_children "$A/work/cursor/skills" "$CURSOR/skills"
link_children "$A/games/skills"         "$CODEX_GAMES_HOME/skills" "$CLAUDE_GAMES_HOME/skills"

# third-party skills for the games home (agents/games/vendor.txt: "<owner/repo> <path>")
while read -r repo path; do
  case "$repo" in ''|\#*) continue ;; esac
  cache="$VENDOR_CACHE/${repo//\//-}"
  if [ ! -d "$cache/.git" ]; then
    mkdir -p "$VENDOR_CACHE"
    git clone -q --depth 1 "https://github.com/$repo.git" "$cache" || { echo "warning could not clone $repo (offline?)"; continue; }
  fi
  [ -d "$cache/$path" ] || { echo "warning $repo has no $path"; continue; }
  safe_symlink "$cache/$path" "$CODEX_GAMES_HOME/skills/$(basename "$path")"
  safe_symlink "$cache/$path" "$CLAUDE_GAMES_HOME/skills/$(basename "$path")"
done < "$A/games/vendor.txt"

# --- commands / prompts ---
COMMAND_DIRS=("${CLAUDE_HOMES[@]/%//commands}" "$OPENCODE/commands" "$CURSOR/commands" "$CODEX_GAMES_HOME/prompts" "$CLAUDE_GAMES_HOME/commands")
for d in "${COMMAND_DIRS[@]}"; do clean_stale_links "$d"; done

link_files "$A/work/commands"          "${CLAUDE_HOMES[@]/%//commands}" "$OPENCODE/commands"
link_files "$A/work/claude/commands"   "${CLAUDE_HOMES[@]/%//commands}"
link_files "$A/work/opencode/commands" "$OPENCODE/commands"
link_files "$A/work/cursor/commands"   "$CURSOR/commands"
link_files "$A/games/prompts"          "$CODEX_GAMES_HOME/prompts" "$CLAUDE_GAMES_HOME/commands"

# --- project-local instruction overrides ---
safe_symlink "$DOTFILES/projects/platform/CLAUDE.md"       "$HOME/projects/platform/CLAUDE.md"
safe_symlink "$DOTFILES/projects/platform/CLAUDE.local.md" "$HOME/projects/platform/CLAUDE.local.md"
safe_symlink "$DOTFILES/projects/obsidian/spse/AGENTS.md"  "$HOME/projects/obsidian/spse/AGENTS.md"
safe_symlink "$DOTFILES/projects/obsidian/spse/AGENTS.md"  "$HOME/projects/obsidian/spse/CLAUDE.md"
safe_symlink "$DOTFILES/projects/obsidian/apologetics-training/CLAUDE.md" "$HOME/projects/obsidian/apologetics-training/CLAUDE.md"
safe_symlink "$DOTFILES/projects/obsidian/apologetics-training/AGENTS.md" "$HOME/projects/obsidian/apologetics-training/AGENTS.md"

echo "done."
