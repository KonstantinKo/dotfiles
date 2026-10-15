[ ! -r "$HOME/.config/dotfiles/shell.sh" ] || . "$HOME/.config/dotfiles/shell.sh"
[ ! -r "$HOME/.bash-preexec.sh" ] || . "$HOME/.bash-preexec.sh"
if command -v atuin >/dev/null 2>&1; then eval "$(atuin init bash)"; fi
