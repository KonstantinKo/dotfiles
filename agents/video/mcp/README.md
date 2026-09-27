# Local Higgsfield Blender setup

Run `./install-blender.sh` once on this Mac, then run `make install` at the dotfiles root. The installer links the video scoped MCP configs and `use-blender` skill into the video root and each Git backed video project. It also trusts those exact project paths in both Codex homes so Codex loads their local configs. Restart Codex or Claude after installing. Claude asks once to approve the project's MCP server.

The installed `fnf-blender-mcp@0.2.2` package starts Blender in a dedicated background process. It does not require the Higgsfield cloud account and local `bl_*` calls do not spend credits. Save scenes before disconnecting.

The video projects also expose Higgsfield's official remote MCP at `https://mcp.higgsfield.ai/mcp` to Codex and Claude. Each client needs its own OAuth authorization for the intended Higgsfield account. In the project, run `codex mcp login higgsfield` for Codex or open `/mcp` and select `higgsfield` in Claude Code. Claude also asks once to trust the project MCP configuration. The CLI's existing login does not authorize the remote MCP clients.

The eight official CLI skills are video scoped. Seven come from `higgsfield-ai/skills` at commit `f83af0bc1d937c8119099a11f8ebbf5e6fb99819`; the eighth, `higgsfield-generate`, is the local approval aware entry point with the upstream guide under `references/official/`. Their MIT license is in `agents/video/HIGGSFIELD-SKILLS-LICENSE`. Re-run the skill installer at a reviewed upstream commit to update them; then reapply the local approval note. Higgsfield cloud calls remain subject to the per call estimate and approval rule in `agents/video/AGENTS.md`. Codex prompts before every remote MCP tool call; Claude's project hook asks before every remote MCP tool call.

Package: https://www.npmjs.com/package/fnf-blender-mcp
