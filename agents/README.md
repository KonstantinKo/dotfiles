# User-Shared Agent Workflows

This directory is the canonical user-level source for workflows that should work across Claude Code, OpenCode, Codex, Cursor (`agent` CLI), and other harnesses.

- `commands/` contains neutral command prompts. Tool-specific command folders should symlink to these files when the harness supports slash commands.
- `skills/` contains thin skill wrappers for harnesses that discover skills but not commands. Keep bodies neutral and point to the canonical command prompt when possible.
- `skills/_archive/` keeps inactive skills tracked without exposing them to skill discovery. After moving a skill there, run `make` from the repository root; the installer removes its manifest row and stale symlinks.

Do not duplicate workflow bodies in tool-specific config unless the harness requires a different adapter format.
