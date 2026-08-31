# dotfiles

Managed via symlinks. Edit files here, changes are live. New machine: clone + `./install.sh`.

## Layout

- `.zshrc` `.bashrc` `.profile` `.gitconfig` — shell & git (`.npmrc` stays machine-local, token only)
- `dotconfig/nvim` → `~/.config/nvim`
- `agents/` — canonical agent config; selected shared files and active skills are linked into `~/.agents`
  - `AGENTS.md` — global instructions; `CLAUDE.md` is a one-line shim importing it
  - `skills/` + `skills.manifest` — skill pool, manifest controls which tool gets which skill; `_archive/` is tracked but not exposed to tooling
  - `commands/` — cross-harness slash commands
  - `claude/`, `opencode/`, `cursor/` — per-tool settings (Claude settings/statusline, OpenCode plugins, Cursor `mcp.json`)
- `projects/` — local (untracked-in-repo) instruction overrides per project, symlinked into place
- `iterm2_profile/Default.json` — iTerm2 default profile export

## Usage

```sh
make   # idempotent; backs up conflicts to <file>.pre-dotfiles
```

To archive a skill, move its folder into `agents/skills/_archive/`, run `make`,
and restart any running agent sessions. The installer removes its `skills.manifest` row
and stale tool-facing symlinks.

Secrets never go in this repo.
