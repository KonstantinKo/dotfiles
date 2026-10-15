# dotfiles

Shared configuration for macOS and Linux. Edit the repo, commit and push, then pull and rerun the installer on each machine. Agent auth, sessions, secrets, Git identity, and workspace choices stay machine-local.

## Layout

- `.zshenv` `.zshrc` `.bashrc` `.profile` `.gitconfig` — shell & git (`.npmrc` stays machine-local, token only)
- `dotconfig/nvim` → `~/.config/nvim`
- `agents/` — everything AI-agent related, one folder per destination (see `agents/README.md`):
  `shared/` (all homes), `work/` (day-job homes), `work/di/` (company account only),
  `work/<tool>/` (one harness), `games/` (`~/.codex-games`, `~/.claude-games`). Each holds `skills/`, `commands/` or
  `prompts/`, `agents/`, and tool config.
- `agents/video/` — general video skills; `agents/video/backlot/` is the optional Backlot studio (see `agents/video/backlot/ARCHITECTURE.md`), linked into `~/projects/video/backlot/` with CLI `backlot`
- `projects/` — private instructions and skills for specific project repos, symlinked into place
- `iterm2_profile/Default.json` — iTerm2 default profile export

## Install and update

On omini (Bash/Omarchy), after cloning to `~/dotfiles`:

```bash
cd ~/dotfiles
./install.sh --workspaces games,creative,video,personal --projects-root "$HOME/projects"
exec bash -l
```

`work` installs company homes, skills, MCP settings, and the work Git email.
`games` installs isolated Codex/Claude games homes and OpenCode; `creative` adds Blender
skills to games/video; `video` adds video and Backlot project tooling; `personal` adds
private vault instructions. Choose any comma-separated combination. New Linux homes
default to `games,creative,video,personal`; macOS defaults to all five for compatibility.
Use an explicit `--workspaces` value when enrolling a machine.

The installer saves choices in `~/.config/dotfiles/machine.sh`, outside Git. `make` or
`./install.sh` reuses them after a pull. CLI options override explicit `DOTFILES_WORKSPACES`,
`DOTFILES_PROJECTS_ROOT`, and `DOTFILES_EXCLUDE_SKILLS` environment variables, which override
saved values. To change choices, rerun with `--workspaces`.
`--exclude-skills skill-name,another-skill` persists individual skill exclusions; pass
an empty string to clear exclusions. `--projects-root` is case-sensitive and may point
to an existing migration symlink. Both machines can use `~/projects`; an alternative
such as `~/Projects` is supported by the launcher and Backlot config resolution.

```bash
git pull --ff-only
./install.sh
# No network/vendor downloads (uncached third-party skills are skipped):
./install.sh --offline
```

Conflicts are backed up under `~/.dotfiles-backup/<timestamp>-<pid>/`. Existing Bash,
profile, and Zsh environment files receive a loader for shared shell functions;
Omarchy startup configuration is retained. Auth/session files are never installed or
copied. Codex configs are seeded once, then remain machine-local. Changing workspace
choices retires only recorded managed symlinks; old seeded configs, generated OpenCode
files, auth, local skills, and backups remain available for explicit cleanup. Stop old
agent sessions when changing a profile. Skill moves/deletions are applied on reinstall.

Set a personal Git identity on omini (the shared `.gitconfig` has no company identity):

```bash
git config --file ~/.config/dotfiles/git.local user.name 'Konstantin Koss'
git config --file ~/.config/dotfiles/git.local user.email 'YOUR PERSONAL EMAIL'
```

The previous global Git config is backed up if it conflicts; restore any additional
machine-specific settings in `git.local`. `.npmrc` remains local and is never linked.

### Linux prerequisites and credentials

The installer itself needs Bash, Git, and standard Unix tools. Agent tooling additionally
uses Node/npm (`npx`), `uv`/`uvx`, `jq`, and the desired Claude/Codex/OpenCode CLIs. Backlot
uses Python 3.12 through `uv`, FFmpeg, and its locked Python dependencies (`uv sync --project
agents/video/backlot`). Install Blender and Godot through the OS package manager. The
background Blender MCP is a separate opt-in install:

```bash
./agents/video/mcp/install-blender.sh
```

Blender resolves from `BLENDER_EXECUTABLE`, then `blender` on PATH, then the macOS app.
Godot resolves from `GODOT_QUIET_BIN`/`GODOT_BIN`, `godot`/`godot4` on PATH, then the macOS
app. `godot-quiet` retains the macOS GPU shim; Linux uses headless Godot with a coreutils
`timeout` watchdog. Use normal `godot` for visible/GPU editor work on Linux. Unity MCPs
require a separately installed Unity editor and project bridge.

Log in separately to each agent provider (`codg login`, `clag` → `/login`, OpenCode
`/connect`) and GitHub (`gh auth login`) as needed. Never copy account auth files.
MCP executables rely on `~/.local/bin` being in the launching application's PATH; the
shared Bash/Zsh loader adds it. Restart GUI agent apps after updating their environment.
Higgsfield uses its own OAuth login. API credentials are optional until using the relevant
provider; no secret values belong in this repo.

For fal.ai, prefer a one-session `FAL_KEY` environment variable or a private machine-local
file. Create it without putting the key into shell history:

```bash
mkdir -p ~/.config/dotfiles/secrets
(umask 077; read -r -s -p 'fal.ai API key: ' fal_key; printf '\n';
 printf '%s' "$fal_key" > ~/.config/dotfiles/secrets/fal-key)
```

The fal MCP and Backlot launcher read `FAL_KEY`, then `FAL_KEY_FILE` (defaults to the file
above, mode 600/400 required), then their existing macOS Keychain item. Games use
`fal.ai (codg)` / `$USER`; Backlot uses `fal-api` / `FAL_KEY`. Existing Mac Keychain enrollment
continues to work. Company tokens and npm package credentials are unnecessary on omini.

### Verification

```bash
python3 -m unittest discover -s tests -v
uv run --project agents/video/backlot pytest -q agents/video/backlot/tests
```

Installer tests use disposable homes and `--offline`, preserving the actual home.

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
`agents/work/claude/bootstrap-home.sh ~/.claude-di` installs the plugin set and copies user-scope
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
reads an environment/file key (above), or the macOS Keychain item `fal.ai (codg)`; add or rotate it with
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
`agents/games/claude/`: `settings.json` (Fable, bypass permissions) and
`mcp/{base,unity-coplay,unity-anklebreaker}.json`. `clag` is a shell function in `~/.zshenv`
that starts Claude with `CLAUDE_CONFIG_DIR=~/.claude-games` and
`--mcp-config base.json unity-coplay.json --strict-mcp-config`; `clag unity-ab` swaps the Unity
MCP for AnkleBreaker. Under `~/projects/video`, `clag` also loads the nearest `.mcp.json`
automatically, so launch it from the video project directory. Log in once (`clag` → `/login`), then
`agents/work/claude/bootstrap-home.sh ~/.claude-games --settings agents/games/claude/settings.json --plugins-only`
installs the plugin set (no work MCPs are copied). In T3 Code the same home is the `claude_games`
provider instance in `~/.t3/userdata/settings.json`; it passes the MCP files through `launchArgs`
without `--strict-mcp-config`, so T3's own MCP tools keep working.

Secrets never go in this repo.

## Optional Linux work profiles

On an owner-managed Linux worker, clone this repository to `~/dotfiles` and run:

```sh
cd ~/dotfiles
./install-work-linux.sh --launchers
export PATH="$HOME/.local/bin:$PATH"
```

This installs only company Claude and Codex profiles (`~/.claude-di`, `~/.codex-di`),
shared/work instructions and commands. Skill precedence is shared → work → company →
harness. `_archive` is excluded. Keep the checkout in place: the profiles use symlinks.
The generic cloud runtime and colleagues do not need this private repository or installer.

Omit `--launchers` if T3 launches the CLIs directly; set its provider home paths to those
company directories. Optional `clax` and `codx` are executable scripts, so noninteractive
shells can use them by absolute path without sourcing shell startup files. The CLIs must
already be installed on `PATH`. Existing launchers are preserved.

The installer seeds only empty portable settings and leaves existing settings, config and
authentication untouched. It does not install packages, change shell/Git configuration,
copy credentials, enable permission bypasses, configure MCPs, or install personal/game
profiles. Conflicting instruction/skill links and files are backed up under
`~/.dotfiles-backup/work-linux.*`; symlinked profile/container directories are rejected.
Re-running updates links and removes dangling skill links owned by this checkout.

Sign into each company profile separately, with or without the optional launchers:

```sh
CLAUDE_CONFIG_DIR="$HOME/.claude-di" claude auth login
CODEX_HOME="$HOME/.codex-di" codex login
```

Check
CLI authentication independently from MCP readiness: MCP servers, their OAuth sessions,
plugins and skill-specific external tools need their own Linux-compatible setup. Do not
copy the macOS configs or auth files. For GitHub HTTPS credentials, `gh` must be on `PATH`
and authenticated; an optional repository-local helper can be added with
`git -C /path/to/repo config --local --add credential.https://github.com.helper '!gh auth git-credential'`
after checking that repository's existing helpers. No global helper is changed.

Run the isolated installer checks with `bash tests/install-work-linux.sh`.
