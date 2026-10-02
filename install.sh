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
#   creative/ Blender skills for game homes and video projects
#   video/    general video skills; video/backlot/ adds the optional Backlot workflow
set -euo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
A="$DOTFILES/agents"
BACKUP_ROOT="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)"

CLAUDE_HOMES=("$HOME/.claude" "$HOME/.claude-di")
CODEX_HOMES=("$HOME/.codex" "$HOME/.codex-di")
DI_HOMES=("$HOME/.claude-di" "$HOME/.codex-di")
CODEX_GAMES_HOME="$HOME/.codex-games"
CLAUDE_GAMES_HOME="$HOME/.claude-games"
VIDEO_ROOT="$HOME/projects/video"
BACKLOT_ROOT="$VIDEO_ROOT/backlot"
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
for f in .zshenv .zshrc .bashrc .profile .npmrc .gitconfig; do
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

# Codex loads a repository's .codex/config.toml only when that exact project
# is trusted. Trust video repositories in both Codex homes for their local MCP.
trust_video_project() {
  local project="${1%/}" home config heading
  heading="[projects.\"$project\"]"
  for home in "$HOME/.codex" "$CODEX_GAMES_HOME"; do
    config="$home/config.toml"
    [ -f "$config" ] || continue
    if ! rg -Fq "$heading" "$config"; then
      printf '\n%s\ntrust_level = "trusted"\n' "$heading" >> "$config"
      echo "trusted $project in $home"
    fi
  done
}

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
link_children "$A/creative/skills"      "$CODEX_GAMES_HOME/skills" "$CLAUDE_GAMES_HOME/skills"

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
COMMAND_DIRS=("${CLAUDE_HOMES[@]/%//commands}" "${CODEX_HOMES[@]/%//prompts}" "$OPENCODE/commands" "$CURSOR/commands" "$CODEX_GAMES_HOME/prompts" "$CLAUDE_GAMES_HOME/commands")
for d in "${COMMAND_DIRS[@]}"; do clean_stale_links "$d"; done

link_files "$A/work/commands"          "${CLAUDE_HOMES[@]/%//commands}" "$OPENCODE/commands"
link_files "$A/work/claude/commands"   "${CLAUDE_HOMES[@]/%//commands}"
link_files "$A/work/codex/prompts"     "${CODEX_HOMES[@]/%//prompts}"
link_files "$A/work/opencode/commands" "$OPENCODE/commands"
link_files "$A/work/cursor/commands"   "$CURSOR/commands"
link_files "$A/games/prompts"          "$CODEX_GAMES_HOME/prompts" "$CLAUDE_GAMES_HOME/commands"

# --- video projects: general tools at the root, Backlot tools only under backlot/ ---
safe_symlink "$A/video/AGENTS.md" "$VIDEO_ROOT/AGENTS.md"
safe_symlink "$A/video/backlot/AGENTS.md" "$BACKLOT_ROOT/AGENTS.md"
safe_symlink "$A/video/backlot/studio.yaml" "$BACKLOT_ROOT/studio.yaml"
safe_symlink "$A/video/backlot/bin/backlot" "$HOME/.local/bin/backlot"
for d in "$VIDEO_ROOT/.claude/skills" "$VIDEO_ROOT/.agents/skills" "$VIDEO_ROOT/.claude/commands" "$VIDEO_ROOT/.claude/agents"; do
  mkdir -p "$d"; clean_stale_links "$d"
done
link_children "$A/video/skills"        "$VIDEO_ROOT/.claude/skills" "$VIDEO_ROOT/.agents/skills"
link_children "$A/creative/skills"     "$VIDEO_ROOT/.claude/skills" "$VIDEO_ROOT/.agents/skills"
for d in "$BACKLOT_ROOT/.claude/skills" "$BACKLOT_ROOT/.agents/skills" "$BACKLOT_ROOT/.claude/commands" "$BACKLOT_ROOT/.claude/agents"; do
  mkdir -p "$d"; clean_stale_links "$d"
done
link_children "$A/video/skills"         "$BACKLOT_ROOT/.claude/skills" "$BACKLOT_ROOT/.agents/skills"
link_children "$A/creative/skills"      "$BACKLOT_ROOT/.claude/skills" "$BACKLOT_ROOT/.agents/skills"
link_children "$A/video/backlot/skills" "$BACKLOT_ROOT/.claude/skills" "$BACKLOT_ROOT/.agents/skills"
link_files "$A/video/backlot/commands" "$BACKLOT_ROOT/.claude/commands"
link_files "$A/video/backlot/claude/agents" "$BACKLOT_ROOT/.claude/agents"
# Claude Code does not read settings from a parent dir, so each project gets a link.
safe_symlink "$A/video/claude/settings.json" "$VIDEO_ROOT/.claude/settings.json"
safe_symlink "$A/video/claude/settings.json" "$BACKLOT_ROOT/.claude/settings.json"
safe_symlink "$A/video/mcp/claude-mcp.json" "$VIDEO_ROOT/.mcp.json"
safe_symlink "$A/video/mcp/claude-mcp.json" "$BACKLOT_ROOT/.mcp.json"
safe_symlink "$A/video/mcp/codex-config.toml" "$VIDEO_ROOT/.codex/config.toml"
safe_symlink "$A/video/mcp/codex-config.toml" "$BACKLOT_ROOT/.codex/config.toml"
trust_video_project "$VIDEO_ROOT"
trust_video_project "$BACKLOT_ROOT"

# Git-backed child projects need local skill links so Codex can discover them
# even when it stops scanning at the child repository root.
for project in "$BACKLOT_ROOT"/*/ "$VIDEO_ROOT"/labs/*/; do
  [ -d "$project/.git" ] || continue
  for d in "$project/.agents/skills" "$project/.claude/skills"; do
    mkdir -p "$d"; clean_stale_links "$d"
  done
  link_children "$A/video/skills" "$project/.agents/skills" "$project/.claude/skills"
  link_children "$A/creative/skills" "$project/.agents/skills" "$project/.claude/skills"
  case "$project" in
    "$BACKLOT_ROOT"/*)
      link_children "$A/video/backlot/skills" "$project/.agents/skills" "$project/.claude/skills"
      safe_symlink "$A/video/backlot/AGENTS.md" "$project/AGENTS.md" ;;
  esac
  safe_symlink "$A/video/claude/settings.json" "$project/.claude/settings.json"
  safe_symlink "$A/video/mcp/claude-mcp.json" "$project/.mcp.json"
  safe_symlink "$A/video/mcp/codex-config.toml" "$project/.codex/config.toml"
  trust_video_project "$project"
done

if [ -d "$VIDEO_ROOT/labs" ]; then
  safe_symlink "$A/video/labs/AGENTS.md" "$VIDEO_ROOT/labs/AGENTS.md"
  for project in "$VIDEO_ROOT"/labs/*/; do
    [ -d "$project/.git" ] || continue
    safe_symlink "$A/video/labs/AGENTS.md" "$project/AGENTS.md"
  done
fi

# Retire old instruction shims and the old Backlot config link when managed by dotfiles.
for link in "$VIDEO_ROOT/CLAUDE.md" "$VIDEO_ROOT/labs/CLAUDE.md" "$VIDEO_ROOT"/labs/*/CLAUDE.md "$VIDEO_ROOT/studio.yaml"; do
  [ -L "$link" ] || continue
  case "$(readlink "$link")" in
    "$A/video/CLAUDE.md"|"$A/video/labs/CLAUDE.md"|"$A/video/studio.yaml")
      rm "$link"; echo "retired $link" ;;
  esac
done

# --- project-local instruction overrides ---
if [ -f "$HOME/projects/platform/CLAUDE.global.md" ]; then
  safe_symlink "$HOME/projects/platform/CLAUDE.global.md" "$HOME/projects/platform/CLAUDE.md"
fi
safe_symlink "$DOTFILES/projects/platform/CLAUDE.local.md" "$HOME/projects/platform/CLAUDE.local.md"
safe_symlink "$DOTFILES/projects/obsidian/spse/AGENTS.md"  "$HOME/projects/obsidian/spse/AGENTS.md"
safe_symlink "$DOTFILES/projects/obsidian/spse/AGENTS.md"  "$HOME/projects/obsidian/spse/CLAUDE.md"
safe_symlink "$DOTFILES/projects/obsidian/apologetics-training/CLAUDE.md" "$HOME/projects/obsidian/apologetics-training/CLAUDE.md"
safe_symlink "$DOTFILES/projects/obsidian/apologetics-training/AGENTS.md" "$HOME/projects/obsidian/apologetics-training/AGENTS.md"

echo "done."
