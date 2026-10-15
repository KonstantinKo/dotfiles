# Video Blender and Higgsfield setup

Run `./install-blender.sh` once on macOS or Linux, then run `make install` at the dotfiles root. The installer links the video scoped MCP configs and `blender-background` skill into the video root and each Git backed video project. It also trusts those exact project paths in the selected Codex homes so Codex loads their local configs. Restart Codex or Claude after installing. Claude asks once to approve the project's MCP server.

The `blender-background` server uses the installed `fnf-blender-mcp@0.2.2` package to start Blender in a dedicated background process. It does not require a Higgsfield account and local `bl_*` calls do not spend credits. Save scenes before disconnecting. The existing `blender` server in the games profile controls an open desktop Blender scene through the "MCP for Blender" add-on; start its server in Blender's N panel. Use it when you want to see or continue work in that scene.

The video projects also expose Higgsfield's official remote MCP at `https://mcp.higgsfield.ai/mcp` to Codex and Claude. Each client needs its own OAuth authorization for the intended Higgsfield account. In the project, run `codex mcp login higgsfield` for Codex.

For Claude in T3, select the `claude_games` provider and open the video project. Its launcher reads the project `.mcp.json`; approve `blender-background` and `higgsfield` when Claude offers the project MCP approval, then use `/mcp` to sign in to `higgsfield`.

The terminal `clag` shell function uses `--strict-mcp-config` and automatically adds the nearest video project `.mcp.json`. From the video project, run `clag`, then use `/mcp` for Higgsfield OAuth. The CLI's existing login does not authorize the remote MCP clients.

The eight official CLI skills are video scoped. Seven come from `higgsfield-ai/skills` at commit `f83af0bc1d937c8119099a11f8ebbf5e6fb99819`; the eighth, `higgsfield-generate`, is the local approval aware entry point with the upstream guide under `references/official/`. Their MIT license is in `agents/video/HIGGSFIELD-SKILLS-LICENSE`. Re-run the skill installer at a reviewed upstream commit to update them; then reapply the local approval note. Higgsfield cloud calls remain subject to the per call estimate and approval rule in `agents/video/AGENTS.md`. Codex prompts before every remote MCP tool call; Claude's project hook asks before every remote MCP tool call.

Package: https://www.npmjs.com/package/fnf-blender-mcp

`blender-background-mcp` resolves Blender from `BLENDER_EXECUTABLE`, PATH, or the macOS app. Its npm package stays machine-local. Ensure `~/.local/bin` is on the agent launcher PATH.
