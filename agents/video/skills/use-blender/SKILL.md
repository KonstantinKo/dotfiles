---
name: use-blender
description: Use the local Higgsfield Blender MCP in video projects to inspect, edit, render, and save Blender scenes. Use for the tutorial's /use-blender workflow.
---

# Use Blender in video projects

This project has the `higgsfield-use-blender` MCP server, backed by `fnf-blender-mcp@0.2.2`. It runs a dedicated local background Blender process. Its `bl_*` tools do not spend Higgsfield credits.

Start with `bl_health`, then `bl_get_scene_summary`. Read the MCP's `bl_get_skill(name: "blender-scene")` for scene guidance and `bl_list_skills` for the other bundled Blender workflows. Use `bl_open_project` for an existing saved `.blend`, make the requested edits, render evidence with `bl_render`, and save with `bl_save_project` before ending the session.

This MCP cannot see unsaved changes in a desktop Blender window. Save the desktop file first, then open that file in the MCP. Background scenes are separate for each Codex or Claude connection.

For repeatable scripted work, the shared `blender` skill also supports Blender's headless Python CLI. If a task uses Higgsfield cloud generation, follow the video project's approval rule and the `higgsfield-generate` skill before every paid call.
