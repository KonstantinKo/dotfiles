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

# --- shell & git ---
for f in .zshrc .bashrc .profile .npmrc .gitconfig; do
  safe_symlink "$DOTFILES/$f" "$HOME/$f"
done

# --- neovim ---
safe_symlink "$DOTFILES/dotconfig/nvim" "$HOME/.config/nvim"

# --- agent canonical store (~/.agents) ---
safe_symlink "$DOTFILES/agents" "$HOME/.agents"

# --- global instruction files ---
safe_symlink "$DOTFILES/agents/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
safe_symlink "$DOTFILES/agents/AGENTS.md" "$HOME/.codex/AGENTS.md"
safe_symlink "$DOTFILES/agents/AGENTS.md" "$HOME/.config/opencode/AGENTS.md"

# --- claude settings ---
safe_symlink "$DOTFILES/agents/claude/settings.json" "$HOME/.claude/settings.json"
safe_symlink "$DOTFILES/agents/claude/statusline.sh" "$HOME/.claude/statusline.sh"

# --- opencode settings ---
for f in opencode.jsonc opencode-notifier.json package.json; do
  safe_symlink "$DOTFILES/agents/opencode/$f" "$HOME/.config/opencode/$f"
done
safe_symlink "$DOTFILES/agents/opencode/plugins" "$HOME/.config/opencode/plugins"

# --- skills fan-out (per skills.manifest) ---
while IFS= read -r line; do
  case "$line" in ''|\#*) continue ;; esac
  name="${line%%:*}"
  tools="${line#*:}"
  for tool in ${tools//,/ }; do
    case "$tool" in
      claude)   dir="$HOME/.claude/skills" ;;
      opencode) dir="$HOME/.config/opencode/skills" ;;
      *) continue ;;
    esac
    safe_symlink "$DOTFILES/agents/skills/$name" "$dir/$name"
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
