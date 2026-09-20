# dotfiles

Managed via symlinks. Edit files here, changes are live. New machine: clone + `./install.sh`.

## Layout

- `.zshrc` `.bashrc` `.profile` `.gitconfig` — shell & git (`.npmrc` stays machine-local, token only)
- `dotconfig/nvim` → `~/.config/nvim`
- `agents/` — everything AI-agent related, one folder per destination (see `agents/README.md`):
  `shared/` (all homes), `work/` (day-job homes), `work/di/` (company account only),
  `work/<tool>/` (one harness), `games/` (`~/.codex-games`, `~/.claude-games`). Each holds `skills/`, `commands/` or
  `prompts/`, `agents/`, and tool config.
- `projects/` — local (untracked-in-repo) instruction overrides per project, symlinked into place
- `iterm2_profile/Default.json` — iTerm2 default profile export

## Usage

```sh
make   # idempotent; backs up conflicts to <file>.pre-dotfiles
```

Conflicting real files are moved to `~/.dotfiles-backup/<timestamp>/`, never deleted.
To move a skill between areas or archive it (`agents/work/skills/_archive/`), move the folder,
run `make`, restart running agent sessions. Stale links are removed automatically.

## Two accounts per tool

Claude Code and Codex each run from two config homes so both accounts stay logged in
side by side (`CLAUDE_HOMES` / `CODEX_HOMES` in `install.sh`):

| | labs account (default) | company account (Linear/Slack MCPs) |
|---|---|---|
| Claude | `~/.claude` → `cla` | `~/.claude-di` → `clax` |
| Codex | `~/.codex` → `codex` | `~/.codex-di` → `codx` |

Shared into every home by `make`: `CLAUDE.md`/`AGENTS.md`, `settings.json`, `statusline.sh`,
skills. Per home: auth, `.claude.json` (MCP servers, project trust), plugins, sessions,
Codex `config.toml` (seeded once from `agents/work/codex/config.di.toml`).

New Claude home: log in once (`clax` → `/login`), then
`agents/claude/bootstrap-home.sh ~/.claude-di` installs the plugin set and copies user-scope
MCP servers. New Codex home: switch the chatgpt.com browser session to that account first, then `codx login`.
Never `codex logout` (revokes that account's tokens everywhere) and never copy `auth.json`.
In T3 Code, add a second Claude/Codex provider instance with the `CLAUDE_CONFIG_DIR` /
`CODEX_HOME` path field (not "Shadow home", which shares `config.toml`).

### Game-dev homes

`~/.codex-games` → `codg` is a third Codex home for private game projects. Everything for it
lives in `agents/games/`: `AGENTS.md`, `codex/config.toml` seed (Blender/Godot/Unity/fal MCPs,
no Figma/Linear/Slack), `bin/fal-mcp-codg`, own `skills/` (`game-loop`, `asset-pipeline`,
`concept-to-reality`), `prompts/` (`$asset-pipeline`, `$concept-to-reality`) and `vendor.txt`
(Unity-Technologies/skills: unity-cli, ui, ui-uitk, physics, navigation, audio, shader graph,
URP, package management). Work skills never reach this home. Log in once with `codg login`. The Blender MCP needs Blender running with the "MCP for Blender" add-on
server started (`uvx blender-mcp==<version> install-addon` installs the matching add-on).

`codg` is a shell function in `~/.zshenv`. Plain `codg` has the Blender, Godot (godot-ai)
and Unity (CoplayDev MCP for Unity) MCPs; each connects once its editor is open with the add-on.
`codg unity-ab` swaps the Unity MCP for AnkleBreaker (A/B testing). The local fal.ai asset MCP
reads its API-scope key from the macOS Keychain item `fal.ai (codg)`; add or rotate it with
`security add-generic-password -U -a "$USER" -s "fal.ai (codg)" -w` (the trailing `-w`
prompts without putting the secret in shell history). The `game-loop` skill triggers on game-building requests, or explicitly via `$game-loop`.
The codg config runs Codex in yolo mode (`approval_policy = "never"`, `sandbox_mode = "danger-full-access"`) — private game projects only.
T3 Code gets the same setup via the `codex_games` provider instance in `~/.t3/userdata/settings.json` (`homePath: ~/.codex-games`).
New Unity projects use the machine-local custom template `com.konstantin.template.codg-urp`
(`~/Unity user templates/`, made with `unity templates create --keep-project-settings` from an
upgraded URP project plus `agents/games/skills/game-loop/unity/McpBridgeAutoStart.cs`); it avoids the
URP material-upgrade dialog and starts the MCP bridge on open.
Local audio for the agent: `game-sfx` / `game-music` in `~/.local/bin` (models under
`~/.local/share/game-audio`, see its README).

`~/.claude-games` → `clag` is the Claude twin of that home: same `agents/games/AGENTS.md`
(plus `games/CLAUDE.md`, which maps the Codex model names it uses — Astra → Fable, Luna → Sonnet,
every other GPT model → Opus), same games + shared skills, the `prompts/` linked as slash
commands, and no work skills, MCPs or plugins. Claude-only pieces live in
`agents/games/claude/`: `settings.json` (Fable, bypass permissions, caveman only) and
`mcp/{base,unity-coplay,unity-anklebreaker}.json`. `clag` is a shell function in `~/.zshenv`
that starts Claude with `CLAUDE_CONFIG_DIR=~/.claude-games` and
`--mcp-config base.json unity-coplay.json --strict-mcp-config`; `clag unity-ab` swaps the Unity
MCP for AnkleBreaker. Log in once (`clag` → `/login`), then
`agents/work/claude/bootstrap-home.sh ~/.claude-games --settings agents/games/claude/settings.json --plugins-only`
installs the plugin set (no work MCPs are copied). In T3 Code the same home is the `claude_games`
provider instance in `~/.t3/userdata/settings.json`; it passes the MCP files through `launchArgs`
without `--strict-mcp-config`, so T3's own MCP tools keep working.

Secrets never go in this repo.
