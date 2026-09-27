# Local Higgsfield Blender setup

Run `./install-blender.sh` once on this Mac, then run `make install` at the dotfiles root. The installer links the video scoped MCP configs and `use-blender` skill into the video root and each Git backed video project. It also trusts those exact project paths in both Codex homes so Codex loads their local configs. Restart Codex or Claude after installing. Claude asks once to approve the project's MCP server.

The installed `fnf-blender-mcp@0.2.2` package starts Blender in a dedicated background process. It does not require the Higgsfield cloud account and local `bl_*` calls do not spend credits. Save scenes before disconnecting. Higgsfield cloud generation remains subject to the per call estimate and approval rule in `agents/video/AGENTS.md`.

Package: https://www.npmjs.com/package/fnf-blender-mcp
