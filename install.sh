#!/usr/bin/env bash
# Idempotent dotfiles installer. Re-runnable; never deletes content.
# Conflicting real files/dirs are moved to ~/.dotfiles-backup/<timestamp>/<path>.
#
# Layout under agents/: the folder tells you where something ends up.
#   shared/   every agent home (work and games)
#   work/     day-job homes: ~/.claude, ~/.claude-di, ~/.codex, ~/.codex-di, Cursor
#   work/di/  company-account homes only (~/.claude-di, ~/.codex-di)
#   work/<tool>/  one harness only (claude | codex | cursor)
#   games/    game-dev homes: ~/.codex-games, ~/.claude-games, OpenCode
#   creative/ Blender skills for game homes and video projects
#   video/    general video skills; video/backlot/ adds the optional Backlot workflow
set -euo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
A="$DOTFILES/agents"
BACKUP_ROOT="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)-$$"
CONFIG_DIR="$HOME/.config/dotfiles"
env_workspaces_set="${DOTFILES_WORKSPACES+x}"
env_workspaces="${DOTFILES_WORKSPACES-}"
env_projects_root_set="${DOTFILES_PROJECTS_ROOT+x}"
env_projects_root="${DOTFILES_PROJECTS_ROOT-}"
env_exclude_skills_set="${DOTFILES_EXCLUDE_SKILLS+x}"
env_exclude_skills="${DOTFILES_EXCLUDE_SKILLS-}"
DOTFILES_WORKSPACES="${DOTFILES_WORKSPACES:-}"
DOTFILES_PROJECTS_ROOT="${DOTFILES_PROJECTS_ROOT:-}"
DOTFILES_EXCLUDE_SKILLS="${DOTFILES_EXCLUDE_SKILLS:-}"
DOTFILES_OFFLINE="${DOTFILES_OFFLINE:-0}"
# Choices: CLI options > explicitly supplied environment > saved machine choices > defaults.
[ ! -f "$CONFIG_DIR/machine.sh" ] || . "$CONFIG_DIR/machine.sh"
[ "$env_workspaces_set" != x ] || DOTFILES_WORKSPACES="$env_workspaces"
[ "$env_projects_root_set" != x ] || DOTFILES_PROJECTS_ROOT="$env_projects_root"
[ "$env_exclude_skills_set" != x ] || DOTFILES_EXCLUDE_SKILLS="$env_exclude_skills"
while [ $# -gt 0 ]; do
  case "$1" in
    --workspaces|--projects-root|--exclude-skills)
      [ $# -ge 2 ] || { echo "missing value for $1" >&2; exit 2; }
      case "$1" in
        --workspaces) DOTFILES_WORKSPACES="$2" ;;
        --projects-root) DOTFILES_PROJECTS_ROOT="$2" ;;
        --exclude-skills) DOTFILES_EXCLUDE_SKILLS="$2" ;;
      esac
      shift 2 ;;
    --offline) DOTFILES_OFFLINE=1; shift ;;
    --help)
      echo 'Usage: ./install.sh [--workspaces work,games,creative,video,personal] [--projects-root PATH] [--exclude-skills name,...] [--offline]'
      exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
if [ -z "$DOTFILES_WORKSPACES" ]; then
  if [ "$(uname -s)" = Darwin ]; then DOTFILES_WORKSPACES=work,games,creative,video,personal
  else DOTFILES_WORKSPACES=games,creative,video,personal; fi
fi
for workspace in ${DOTFILES_WORKSPACES//,/ }; do
  case "$workspace" in work|games|creative|video|personal) ;;
    *) echo "unknown workspace: $workspace" >&2; exit 2 ;;
  esac
done
DOTFILES_PROJECTS_ROOT="${DOTFILES_PROJECTS_ROOT:-$HOME/projects}"
case "$DOTFILES_PROJECTS_ROOT" in /*) ;; *) echo 'projects root must be absolute' >&2; exit 2 ;; esac
mkdir -p "$CONFIG_DIR"
{
  printf 'DOTFILES_WORKSPACES=%q\n' "$DOTFILES_WORKSPACES"
  printf 'DOTFILES_PROJECTS_ROOT=%q\n' "$DOTFILES_PROJECTS_ROOT"
  printf 'DOTFILES_EXCLUDE_SKILLS=%q\n' "$DOTFILES_EXCLUDE_SKILLS"
} > "$CONFIG_DIR/machine.sh"
selected() { case ",$DOTFILES_WORKSPACES," in *",$1,"*) return 0 ;; *) return 1 ;; esac; }
NEW_LINKS="$(mktemp)"
trap 'dotfiles_exit_status=$?; rm -f "$NEW_LINKS"; exit "$dotfiles_exit_status"' EXIT

excluded_skill() { case ",$DOTFILES_EXCLUDE_SKILLS," in *",$1,"*) return 0 ;; *) return 1 ;; esac; }

CLAUDE_HOMES=("$HOME/.claude" "$HOME/.claude-di")
CODEX_HOMES=("$HOME/.codex" "$HOME/.codex-di")
DI_HOMES=("$HOME/.claude-di" "$HOME/.codex-di")
CODEX_GAMES_HOME="$HOME/.codex-games"
CLAUDE_GAMES_HOME="$HOME/.claude-games"
VIDEO_ROOT="$DOTFILES_PROJECTS_ROOT/video"
BACKLOT_ROOT="$VIDEO_ROOT/backlot"
OPENCODE="$HOME/.config/opencode"
CURSOR="$HOME/.cursor"
VENDOR_CACHE="$HOME/.cache/dotfiles/vendor"

backup() {
  local path="$1" rel="${1#$HOME/}" dst base suffix=1
  base="$BACKUP_ROOT/$rel"
  dst="$base"
  while [ -e "$dst" ] || [ -L "$dst" ]; do
    dst="$base.$suffix"
    suffix=$((suffix + 1))
  done
  mkdir -p "$(dirname "$dst")"
  mv "$path" "$dst"
  echo "backed-up $path -> $dst"
}

safe_symlink() {
  local src="$1" dst="$2"
  printf '%s\t%s\n' "$dst" "$src" >> "$NEW_LINKS"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    echo "ok      $dst"
    return
  fi
  if [ -L "$dst" ]; then backup "$dst"; fi
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
    excluded_skill "$(basename "$child")" && continue
    for dst in "$@"; do safe_symlink "$child" "$dst/$(basename "$child")"; done
  done
}

link_creative() { if selected creative; then link_children "$@"; fi; }

# link_files <src-dir> <dst-dir>...   every regular file of src (commands, prompts)
link_files() {
  local src="$1" f dst; shift
  for f in "$src"/*; do
    [ -f "$f" ] || continue
    for dst in "$@"; do safe_symlink "$f" "$dst/$(basename "$f")"; done
  done
}

seed_once() {
  local src="$1" dst="$2"
  [ -e "$dst" ] && return 0
  mkdir -p "$(dirname "$dst")"; cp "$src" "$dst"; chmod 600 "$dst"; echo "seeded  $dst"
}

# --- shell & git ---
# Preserve distribution startup files (including Omarchy's Bash setup).
# Existing symlinks to this repo remain live; other files get one source line.
for f in .zshenv .bashrc .profile; do
  if [ -L "$HOME/$f" ] && [ "$(readlink "$HOME/$f")" = "$DOTFILES/$f" ]; then continue; fi
  if [ -L "$HOME/$f" ]; then
    shell_copy="$(mktemp)"
    cat "$HOME/$f" > "$shell_copy"
    backup "$HOME/$f"
    mv "$shell_copy" "$HOME/$f"
  fi
  touch "$HOME/$f"
  loader='if [ -n "${BASH_VERSION:-}${ZSH_VERSION:-}" ]; then [ ! -r "$HOME/.config/dotfiles/shell.sh" ] || . "$HOME/.config/dotfiles/shell.sh"; fi'
  if ! grep -Fq "$loader" "$HOME/$f"; then printf '\n%s\n' "$loader" >> "$HOME/$f"; fi
done
safe_symlink "$DOTFILES/shell/common.sh" "$CONFIG_DIR/shell.sh"
safe_symlink "$DOTFILES/.gitconfig" "$HOME/.gitconfig"
if selected work; then
  [ -e "$CONFIG_DIR/git.local" ] || cp "$DOTFILES/shell/git-work.config" "$CONFIG_DIR/git.local"
fi
safe_symlink "$DOTFILES/dotconfig/nvim" "$HOME/.config/nvim"
prepare_directory "$HOME/.agents" "$A"
safe_symlink "$A/AGENTS.md" "$HOME/.agents/AGENTS.md"
if selected work; then safe_symlink "$A/work/commands" "$HOME/.agents/commands"; fi
for tool in "$DOTFILES"/bin/*; do safe_symlink "$tool" "$HOME/.local/bin/$(basename "$tool")"; done

if selected work; then
# --- instruction files ---
for work_home in "${CLAUDE_HOMES[@]}"; do
  safe_symlink "$A/work/AGENTS.md" "$work_home/AGENTS.md"
  safe_symlink "$A/work/CLAUDE.md" "$work_home/CLAUDE.md"
done
for work_home in "${CODEX_HOMES[@]}"; do safe_symlink "$A/work/AGENTS.md" "$work_home/AGENTS.md"; done
safe_symlink "$A/work/AGENTS.md" "$CURSOR/AGENTS.md"
fi

if selected games; then
safe_symlink "$A/games/AGENTS.md" "$CODEX_GAMES_HOME/AGENTS.md"
safe_symlink "$A/games/AGENTS.md" "$CLAUDE_GAMES_HOME/AGENTS.md"
safe_symlink "$A/games/CLAUDE.md" "$CLAUDE_GAMES_HOME/CLAUDE.md"
# OpenCode gets games/AGENTS.md with its closing "## Models" section (Codex model
# tiers) replaced by games/opencode/MODELS.md.
mkdir -p "$OPENCODE"
{ sed '/^## Models$/,$d' "$A/games/AGENTS.md"; cat "$A/games/opencode/MODELS.md"; } > "$OPENCODE/AGENTS.md.new"
if [ -e "$OPENCODE/AGENTS.md" ] || [ -L "$OPENCODE/AGENTS.md" ]; then
  if cmp -s "$OPENCODE/AGENTS.md.new" "$OPENCODE/AGENTS.md"; then rm "$OPENCODE/AGENTS.md.new"
  else backup "$OPENCODE/AGENTS.md"; mv "$OPENCODE/AGENTS.md.new" "$OPENCODE/AGENTS.md"; fi
else mv "$OPENCODE/AGENTS.md.new" "$OPENCODE/AGENTS.md"; fi
echo "wrote   $OPENCODE/AGENTS.md"

fi

if selected work; then
# --- claude (all homes share settings; auth/plugins/sessions stay per home) ---
for home in "${CLAUDE_HOMES[@]}"; do
  safe_symlink "$A/work/claude/settings.json" "$home/settings.json"
  safe_symlink "$A/shared/claude/statusline.sh" "$home/statusline.sh"
done

fi

if selected work; then seed_once "$A/work/codex/config.di.toml" "$HOME/.codex-di/config.toml"; fi

if selected games; then
# --- claude games home: own settings, own MCP set (loaded via clag --mcp-config) ---
safe_symlink "$A/games/claude/settings.json" "$CLAUDE_GAMES_HOME/settings.json"
safe_symlink "$A/shared/claude/statusline.sh"  "$CLAUDE_GAMES_HOME/statusline.sh"
safe_symlink "$A/games/claude/mcp"           "$CLAUDE_GAMES_HOME/mcp"

# --- codex: seed per-home config.toml once (Codex rewrites it afterwards) ---

seed_once "$A/games/codex/config.toml"   "$CODEX_GAMES_HOME/config.toml"
safe_symlink "$A/games/bin/fal-mcp-codg" "$HOME/.local/bin/fal-mcp-codg"
safe_symlink "$A/games/skills/godot-quiet/godot-quiet" "$HOME/.local/bin/godot-quiet"

fi

# Codex loads a repository's .codex/config.toml only when that exact project
# is trusted. Trust video repositories in both Codex homes for their local MCP.
trust_video_project() {
  local project="${1%/}" home config heading
  heading="[projects.\"$project\"]"
  local homes=("$CODEX_GAMES_HOME")
  selected work && homes+=("$HOME/.codex")
  for home in "${homes[@]}"; do
    config="$home/config.toml"
    [ -f "$config" ] || continue
    if ! grep -Fq "$heading" "$config"; then
      printf '\n%s\ntrust_level = "trusted"\n' "$heading" >> "$config"
      echo "trusted $project in $home"
    fi
  done
}

# --- opencode: games home on the OpenCode Go subscription ---
if selected games; then
safe_symlink "$A/games/opencode/opencode.jsonc" "$OPENCODE/opencode.jsonc"
[ -x "$HOME/.opencode/bin/opencode" ] && safe_symlink "$HOME/.opencode/bin/opencode" "$HOME/.local/bin/opencode"
# Retire links from the former work setup.
for link in "$OPENCODE"/* "$OPENCODE"/skills/* "$OPENCODE"/commands/*; do
  [ -L "$link" ] || continue
  case "$(readlink "$link")" in "$A/work"/*) rm "$link"; echo "retired $link" ;; esac
done

# --- cursor ---
fi
if selected work; then
safe_symlink "$A/work/cursor/mcp.json" "$CURSOR/mcp.json"

fi

# --- skills ---
# Claude reads only <home>/skills. Codex reads <home>/skills. Cursor reads its own
# dir plus ~/.claude/skills and ~/.codex/skills, so work skills reach it without
# extra links.
SKILL_DIRS=()
WORK_SKILL_DIRS=()
GAMES_SKILL_DIRS=()
if selected work; then
  WORK_SKILL_DIRS=("${CLAUDE_HOMES[@]/%//skills}" "${CODEX_HOMES[@]/%//skills}" "$CURSOR/skills")
  SKILL_DIRS+=("${WORK_SKILL_DIRS[@]}")
fi
if selected games; then
  GAMES_SKILL_DIRS=("$CODEX_GAMES_HOME/skills" "$CLAUDE_GAMES_HOME/skills" "$OPENCODE/skills")
  SKILL_DIRS+=("${GAMES_SKILL_DIRS[@]}")
fi
if selected work || selected games; then
  for d in "${SKILL_DIRS[@]}"; do clean_stale_links "$d"; done
  link_children "$A/shared/skills" "${SKILL_DIRS[@]}"
fi
if selected work; then
  link_children "$A/work/skills" "${WORK_SKILL_DIRS[@]}"
  link_children "$A/work/di/skills" "${DI_HOMES[@]/%//skills}"
  [ ! -d "$A/work/cursor/skills" ] || link_children "$A/work/cursor/skills" "$CURSOR/skills"
fi
if selected games; then
  link_children "$A/games/skills" "${GAMES_SKILL_DIRS[@]}"
  if selected creative; then link_creative "$A/creative/skills" "${GAMES_SKILL_DIRS[@]}"; fi

# third-party skills for the games homes (agents/games/vendor.txt: "<owner/repo> <path>")
while read -r repo path; do
  case "$repo" in ''|\#*) continue ;; esac
  excluded_skill "$(basename "$path")" && continue
  cache="$VENDOR_CACHE/${repo//\//-}"
  if [ ! -d "$cache/.git" ]; then
    [ "$DOTFILES_OFFLINE" != 1 ] || { echo "offline: skip uncached $repo"; continue; }
    mkdir -p "$VENDOR_CACHE"
    git clone -q --depth 1 "https://github.com/$repo.git" "$cache" || { echo "warning could not clone $repo (offline?)"; continue; }
  fi
  [ -d "$cache/$path" ] || { echo "warning $repo has no $path"; continue; }
  for d in "${GAMES_SKILL_DIRS[@]}"; do safe_symlink "$cache/$path" "$d/$(basename "$path")"; done
done < "$A/games/vendor.txt"


fi

# --- commands / prompts ---
if selected work; then
  link_files "$A/work/commands" "${CLAUDE_HOMES[@]/%//commands}"
  link_files "$A/work/claude/commands" "${CLAUDE_HOMES[@]/%//commands}"
  link_files "$A/work/codex/prompts" "${CODEX_HOMES[@]/%//prompts}"
  link_files "$A/work/cursor/commands" "$CURSOR/commands"
fi
if selected games; then
  link_files "$A/games/prompts" "$CODEX_GAMES_HOME/prompts" "$CLAUDE_GAMES_HOME/commands" "$OPENCODE/commands"
fi

if selected video; then
# --- video projects: general tools at the root, Backlot tools only under backlot/ ---
safe_symlink "$A/video/AGENTS.md" "$VIDEO_ROOT/AGENTS.md"
safe_symlink "$A/video/backlot/AGENTS.md" "$BACKLOT_ROOT/AGENTS.md"
safe_symlink "$A/video/backlot/studio.yaml" "$BACKLOT_ROOT/studio.yaml"
safe_symlink "$A/video/backlot/bin/backlot" "$HOME/.local/bin/backlot"
for d in "$VIDEO_ROOT/.claude/skills" "$VIDEO_ROOT/.agents/skills" "$VIDEO_ROOT/.claude/commands" "$VIDEO_ROOT/.claude/agents"; do
  mkdir -p "$d"; clean_stale_links "$d"
done
link_children "$A/video/skills"        "$VIDEO_ROOT/.claude/skills" "$VIDEO_ROOT/.agents/skills"
link_creative "$A/creative/skills"     "$VIDEO_ROOT/.claude/skills" "$VIDEO_ROOT/.agents/skills"
for d in "$BACKLOT_ROOT/.claude/skills" "$BACKLOT_ROOT/.agents/skills" "$BACKLOT_ROOT/.claude/commands" "$BACKLOT_ROOT/.claude/agents"; do
  mkdir -p "$d"; clean_stale_links "$d"
done
link_children "$A/video/skills"         "$BACKLOT_ROOT/.claude/skills" "$BACKLOT_ROOT/.agents/skills"
link_creative "$A/creative/skills"      "$BACKLOT_ROOT/.claude/skills" "$BACKLOT_ROOT/.agents/skills"
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
  link_creative "$A/creative/skills" "$project/.agents/skills" "$project/.claude/skills"
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

fi

# --- project-local instruction overrides ---
if selected work; then
if [ -f "$DOTFILES_PROJECTS_ROOT/platform/CLAUDE.global.md" ]; then
  safe_symlink "$DOTFILES_PROJECTS_ROOT/platform/CLAUDE.global.md" "$DOTFILES_PROJECTS_ROOT/platform/CLAUDE.md"
fi
safe_symlink "$DOTFILES/projects/platform/CLAUDE.local.md" "$DOTFILES_PROJECTS_ROOT/platform/CLAUDE.local.md"
fi
if selected personal; then
safe_symlink "$DOTFILES/projects/obsidian/spse/AGENTS.md"  "$DOTFILES_PROJECTS_ROOT/obsidian/spse/AGENTS.md"
safe_symlink "$DOTFILES/projects/obsidian/spse/AGENTS.md"  "$DOTFILES_PROJECTS_ROOT/obsidian/spse/CLAUDE.md"
safe_symlink "$DOTFILES/projects/obsidian/apologetics-training/CLAUDE.md" "$DOTFILES_PROJECTS_ROOT/obsidian/apologetics-training/CLAUDE.md"
safe_symlink "$DOTFILES/projects/obsidian/apologetics-training/AGENTS.md" "$DOTFILES_PROJECTS_ROOT/obsidian/apologetics-training/AGENTS.md"

fi
# Retire only links installed by a previous run. User files and auth are retained.
if [ -f "$CONFIG_DIR/links.tsv" ]; then
  while IFS=$'\t' read -r dst src; do
    [ -L "$dst" ] || continue
    [ "$(readlink "$dst")" = "$src" ] || continue
    if ! grep -Fqx "$(printf '%s\t%s' "$dst" "$src")" "$NEW_LINKS"; then
      rm "$dst"
      echo "retired $dst"
    fi
  done < "$CONFIG_DIR/links.tsv"
fi
if selected games; then
# OpenCode always scans ~/.claude/skills too, which holds the work skills. Deny
# every skill except the ones linked into its own dir.
{
  printf '{\n  "$schema": "https://opencode.ai/config.json",\n  "permission": {\n    "skill": {\n'
  printf '      "*": "deny"'
  for skill in "$OPENCODE/skills"/*/; do
    [ "$(basename "$skill")" = "*" ] && continue
    excluded_skill "$(basename "$skill")" && continue
    printf ',\n      "%s": "allow"' "$(basename "$skill")"
  done
  printf '\n    }\n  }\n}\n'
} > "$OPENCODE/opencode.json.new"
if [ -e "$OPENCODE/opencode.json" ] || [ -L "$OPENCODE/opencode.json" ]; then
  if cmp -s "$OPENCODE/opencode.json.new" "$OPENCODE/opencode.json"; then rm "$OPENCODE/opencode.json.new"
  else backup "$OPENCODE/opencode.json"; mv "$OPENCODE/opencode.json.new" "$OPENCODE/opencode.json"; fi
else mv "$OPENCODE/opencode.json.new" "$OPENCODE/opencode.json"; fi
echo "wrote   $OPENCODE/opencode.json"

fi
cp "$NEW_LINKS" "$CONFIG_DIR/links.tsv"
echo "done. Workspaces: $DOTFILES_WORKSPACES"
