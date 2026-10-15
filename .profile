if [ -n "${BASH_VERSION:-}${ZSH_VERSION:-}" ]; then
  [ ! -r "$HOME/.config/dotfiles/shell.sh" ] || . "$HOME/.config/dotfiles/shell.sh"
fi
