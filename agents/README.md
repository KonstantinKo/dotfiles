# agents/ — one folder per destination

The folder an item lives in says where `make` links it. Nothing else decides.

| Folder | Reaches |
|---|---|
| `shared/` | every agent home, work and games |
| `work/` | day-job homes: `~/.claude`, `~/.claude-di`, `~/.codex`, `~/.codex-di`, OpenCode, Cursor |
| `work/di/` | company-account homes only: `~/.claude-di`, `~/.codex-di` |
| `work/claude/`, `work/codex/`, `work/opencode/`, `work/cursor/` | that one harness |
| `games/` | game-dev homes: `~/.codex-games`, `~/.claude-games` |
| `creative/` | Blender skill linked into game homes and video projects |
| `video/` | general skills for projects under `~/projects/video/`; `video/backlot/` holds the optional Backlot workflow, linked only under `~/projects/video/backlot/`. No agent home. |

Inside a folder the kind is by name: `skills/<name>/SKILL.md`, `commands/*.md` (Claude, OpenCode,
Cursor slash commands), `prompts/*.md` (Codex custom prompts), `agents/*.md` (OpenCode agents),
plus per-tool config files.

- `AGENTS.md` holds shared global preferences and is linked at `~/.agents/AGENTS.md`;
  `CLAUDE.md` imports it for broad use. `work/AGENTS.md` loads those preferences and adds
  work-only skill rules in the work homes. `work/CLAUDE.md` imports both files for Claude.
  `games/AGENTS.md` replaces the global instructions in the games homes; `games/CLAUDE.md`
  adds the Codex→Claude model-name mapping (Astra → Fable, Luna → Sonnet, anything else → Opus).
- `work/skills/_archive/` keeps retired skills tracked but unlinked.
- `games/vendor.txt` lists third-party skills (`<owner/repo> <path>`); `make` shallow-clones the
  repo into `~/.cache/dotfiles/vendor/` and links the listed folders. Update with
  `git -C ~/.cache/dotfiles/vendor/<owner>-<repo> pull`.

Cross-reading to keep in mind: OpenCode and Cursor also scan `~/.claude/skills` and
`~/.codex/skills`, so everything in `work/skills` is visible to them too. `~/.agents/skills` is
deliberately not used, because Codex scans it from every home and the games homes must not see
work skills. Skills are linked per home instead. `games/claude/` holds what only the Claude games
home needs: `settings.json` and the `mcp/` server sets that `clag` passes via `--mcp-config`.

Keep bodies harness-neutral. Only put an adapter in a per-tool folder when that harness needs a
different format.

Standalone experiments live under `~/projects/video/labs/`; Backlot productions live under
`~/projects/video/backlot/`. Run `make` after adding a Git-backed video project to link
the general skills into its `.agents/skills/` and `.claude/skills/`. Backlot projects also
receive the Backlot skills. Both harnesses use the same signed-in `higgsfield` CLI account.
