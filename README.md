# dotfiles

Managed via symlinks. Edit files here, changes are live. New machine: clone + `./install.sh`.

## Layout

- `.zshrc` `.bashrc` `.profile` `.gitconfig` — shell & git (`.npmrc` stays machine-local, token only)
- `dotconfig/nvim` → `~/.config/nvim`
- `agents/` (= `~/.agents`) — canonical agent config
  - `AGENTS.md` — global instructions; `CLAUDE.md` is a one-line shim importing it
  - `skills/` + `skills.manifest` — skill pool, manifest controls which tool gets which skill
  - `commands/` — cross-harness slash commands
  - `claude/`, `opencode/` — per-tool settings, statusline, plugins
- `projects/` — local (untracked-in-repo) instruction overrides per project, symlinked into place
- `iterm2_profile/Default.json` — iTerm2 default profile export

## Usage

```sh
./install.sh   # idempotent; backs up conflicts to <file>.pre-dotfiles
```

Secrets never go in this repo.
