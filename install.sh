#!/usr/bin/env bash
# Idempotent dotfiles installer. Re-runnable; never deletes content,
# moves conflicting real files to <target>.pre-dotfiles instead.
set -euo pipefail

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

safe_symlink() {
  local src="$1" dst="$2"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    echo "ok      $dst"
    return
  fi
  if [ -e "$dst" ] && [ ! -L "$dst" ]; then
    mv "$dst" "$dst.pre-dotfiles"
    echo "backed-up $dst -> $dst.pre-dotfiles"
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
      mv "$dir" "$dir.pre-dotfiles"
      echo "backed-up $dir -> $dir.pre-dotfiles"
    fi
  elif [ -e "$dir" ] && [ ! -d "$dir" ]; then
    mv "$dir" "$dir.pre-dotfiles"
    echo "backed-up $dir -> $dir.pre-dotfiles"
  fi
  mkdir -p "$dir"
}

clean_stale_skill_symlinks() {
  local dir="$1" link src
  [ -d "$dir" ] || return
  for link in "$dir"/*; do
    [ -L "$link" ] || continue
    src="$(readlink "$link")"
    case "$src" in
      "$DOTFILES/agents/skills/"*)
        if [ ! -e "$src" ]; then
          rm "$link"
          echo "unlinked $link (source removed)"
        fi
        ;;
    esac
  done
}

prune_archived_skills() {
  local manifest="$DOTFILES/agents/skills.manifest" tmp line name changed=0
  tmp="$(mktemp "$manifest.tmp.XXXXXX")"
  chmod 644 "$tmp"
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      ''|\#*) printf '%s\n' "$line" >> "$tmp"; continue ;;
    esac
    name="${line%%:*}"
    if [ ! -d "$DOTFILES/agents/skills/$name" ] && [ -d "$DOTFILES/agents/skills/_archive/$name" ]; then
      echo "archived $name (removed from skills.manifest)"
      changed=1
      continue
    fi
    printf '%s\n' "$line" >> "$tmp"
  done < "$manifest"
  if [ "$changed" -eq 1 ]; then
    mv "$tmp" "$manifest"
  else
    rm "$tmp"
  fi
}

# --- shell & git ---
for f in .zshrc .bashrc .profile .npmrc .gitconfig; do
  safe_symlink "$DOTFILES/$f" "$HOME/$f"
done

# --- neovim ---
safe_symlink "$DOTFILES/dotconfig/nvim" "$HOME/.config/nvim"

# --- agent shared store (~/.agents) ---
# Keep the discovered skills directory separate from the tracked source tree so
# agents/skills/_archive is never scanned by tools with recursive discovery.
prepare_directory "$HOME/.agents" "$DOTFILES/agents"
safe_symlink "$DOTFILES/agents/AGENTS.md" "$HOME/.agents/AGENTS.md"
safe_symlink "$DOTFILES/agents/commands" "$HOME/.agents/commands"
prepare_directory "$HOME/.agents/skills"

# --- global instruction files ---
safe_symlink "$DOTFILES/agents/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
safe_symlink "$DOTFILES/agents/AGENTS.md" "$HOME/.codex/AGENTS.md"
safe_symlink "$DOTFILES/agents/AGENTS.md" "$HOME/.config/opencode/AGENTS.md"
safe_symlink "$DOTFILES/agents/AGENTS.md" "$HOME/.cursor/AGENTS.md"

# --- claude settings ---
safe_symlink "$DOTFILES/agents/claude/settings.json" "$HOME/.claude/settings.json"
safe_symlink "$DOTFILES/agents/claude/statusline.sh" "$HOME/.claude/statusline.sh"

# --- opencode settings ---
for f in opencode.jsonc opencode-notifier.json package.json; do
  safe_symlink "$DOTFILES/agents/opencode/$f" "$HOME/.config/opencode/$f"
done
safe_symlink "$DOTFILES/agents/opencode/plugins" "$HOME/.config/opencode/plugins"

# --- cursor (agent CLI) settings ---
safe_symlink "$DOTFILES/agents/cursor/mcp.json" "$HOME/.cursor/mcp.json"

# --- skills fan-out (per skills.manifest) ---
prune_archived_skills

for dir in "$HOME/.agents/skills" "$HOME/.claude/skills" "$HOME/.config/opencode/skills" "$HOME/.cursor/skills"; do
  clean_stale_skill_symlinks "$dir"
done

while IFS= read -r line; do
  case "$line" in ''|\#*) continue ;; esac
  name="${line%%:*}"
  tools="${line#*:}"
  source="$DOTFILES/agents/skills/$name"
  if [ ! -d "$source" ]; then
    echo "warning skill '$name' is in skills.manifest but missing from agents/skills"
    continue
  fi
  safe_symlink "$source" "$HOME/.agents/skills/$name"
  for tool in ${tools//,/ }; do
    case "$tool" in
      claude)   dir="$HOME/.claude/skills" ;;
      opencode) dir="$HOME/.config/opencode/skills" ;;
      cursor)   dir="$HOME/.cursor/skills" ;;
      *) continue ;;
    esac
    safe_symlink "$source" "$dir/$name"
  done
done < "$DOTFILES/agents/skills.manifest"

# --- project-local instruction overrides ---
safe_symlink "$DOTFILES/projects/platform/CLAUDE.md"       "$HOME/projects/platform/CLAUDE.md"
safe_symlink "$DOTFILES/projects/platform/CLAUDE.local.md" "$HOME/projects/platform/CLAUDE.local.md"
safe_symlink "$DOTFILES/projects/obsidian/spse/AGENTS.md"  "$HOME/projects/obsidian/spse/AGENTS.md"
safe_symlink "$DOTFILES/projects/obsidian/spse/AGENTS.md"  "$HOME/projects/obsidian/spse/CLAUDE.md"
safe_symlink "$DOTFILES/projects/obsidian/apologetics-training/CLAUDE.md" "$HOME/projects/obsidian/apologetics-training/CLAUDE.md"
safe_symlink "$DOTFILES/projects/obsidian/apologetics-training/AGENTS.md" "$HOME/projects/obsidian/apologetics-training/AGENTS.md"

echo "done."
