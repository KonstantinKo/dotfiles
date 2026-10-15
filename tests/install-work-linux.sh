#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT
export HOME="$test_root/home with spaces"
fixture="$test_root/dotfiles"
mkdir -p "$HOME/.claude-di" "$HOME/.codex-di" "$fixture"
cp "$repo/install-work-linux.sh" "$fixture/"
mkdir -p "$fixture/agents/work/claude/commands" "$fixture/agents/work/codex/prompts" "$fixture/agents/work/commands"
printf 'global\n' > "$fixture/agents/AGENTS.md"
printf 'work\n' > "$fixture/agents/work/AGENTS.md"
printf 'imports\n' > "$fixture/agents/work/CLAUDE.md"
for layer in shared work work/di work/claude work/codex; do
  mkdir -p "$fixture/agents/$layer/skills/collision" "$fixture/agents/$layer/skills/_archive"
done
mkdir -p "$fixture/agents/shared/skills/shared-only" "$fixture/agents/work/di/skills/company-only"
printf 'shared command\n' > "$fixture/agents/work/commands/command.md"
printf 'claude command\n' > "$fixture/agents/work/claude/commands/command.md"
printf 'prompt\n' > "$fixture/agents/work/codex/prompts/prompt.md"
printf 'keep settings\n' > "$HOME/.claude-di/settings.json"
printf 'keep config\n' > "$HOME/.codex-di/config.toml"
printf 'keep claude auth\n' > "$HOME/.claude-di/.credentials.json"
printf 'keep codex auth\n' > "$HOME/.codex-di/auth.json"
mkdir -p "$HOME/.claude-di/skills"
printf 'keep conflict\n' > "$HOME/.claude-di/skills/collision"
bash "$fixture/install-work-linux.sh" --launchers >/dev/null
bash "$fixture/install-work-linux.sh" --launchers >/dev/null
[ "$(cat "$HOME/.claude-di/settings.json")" = 'keep settings' ]
[ "$(cat "$HOME/.codex-di/config.toml")" = 'keep config' ]
[ "$(cat "$HOME/.claude-di/.credentials.json")" = 'keep claude auth' ]
[ "$(cat "$HOME/.codex-di/auth.json")" = 'keep codex auth' ]
for tool in claude codex; do
  [ "$(readlink "$HOME/.$tool-di/skills/collision")" = "$fixture/agents/work/$tool/skills/collision" ]
  [ -L "$HOME/.$tool-di/skills/shared-only" ]
  [ -L "$HOME/.$tool-di/skills/company-only" ]
  [ ! -e "$HOME/.$tool-di/skills/_archive" ]
done
[ "$(cat "$HOME/.claude-di/commands/command.md")" = 'claude command' ]
[ -L "$HOME/.codex-di/prompts/prompt.md" ]
[ "$(cat "$HOME"/.dotfiles-backup/work-linux.*/.claude-di/skills/collision)" = 'keep conflict' ]
for absent in .claude .codex .claude-games .codex-games .zshrc .bashrc .profile .gitconfig .npmrc .agents/skills projects .config; do
  [ ! -e "$HOME/$absent" ]
done
mkdir -p "$test_root/bin"
cat > "$test_root/bin/claude" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
[ "$CLAUDE_CONFIG_DIR" = "$HOME/.claude-di" ]
[ "$#" = 2 ] && [ "$1" = '--print' ] && [ "$2" = 'hello world' ]
MOCK
cat > "$test_root/bin/codex" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
[ "$CODEX_HOME" = "$HOME/.codex-di" ]
[ "$#" = 2 ] && [ "$1" = 'exec' ] && [ "$2" = 'hello world' ]
MOCK
chmod +x "$test_root/bin/claude" "$test_root/bin/codex"
PATH="$test_root/bin:$PATH" "$HOME/.local/bin/clax" --print 'hello world'
PATH="$test_root/bin:$PATH" "$HOME/.local/bin/codx" exec 'hello world'
rm -r "$fixture/agents/shared/skills/shared-only"
ln -s "$test_root/missing" "$HOME/.codex-di/skills/user-link"
bash "$fixture/install-work-linux.sh" >/dev/null
[ ! -L "$HOME/.codex-di/skills/shared-only" ]
[ -L "$HOME/.codex-di/skills/user-link" ]
# A real checkout also installs into a fresh home without any personal setup.
export HOME="$test_root/fresh"
mkdir -p "$HOME"
bash "$repo/install-work-linux.sh" >/dev/null
[ "$(cat "$HOME/.claude-di/settings.json")" = '{}' ]
[ -f "$HOME/.codex-di/config.toml" ]
[ ! -e "$HOME/.local/bin" ]
[ ! -e "$HOME/.claude-games" ]
# Container symlinks are rejected instead of writing through them.
export HOME="$test_root/symlink-home"
mkdir -p "$HOME" "$test_root/other-profile"
ln -s "$test_root/other-profile" "$HOME/.claude-di"
if bash "$repo/install-work-linux.sh" >/dev/null 2>&1; then
  echo 'Expected rejection of symlinked profile' >&2; exit 1
fi
[ -z "$(ls -A "$test_root/other-profile")" ]
echo 'Linux work-profile behavioral checks passed.'
