---
name: blender-background
description: Use when working on an isolated Blender scene, saving system resources by working in the background and not opening the desktop app.
---

# Background Blender in video projects

This project has the `blender-background` MCP server, backed by `fnf-blender-mcp@0.2.2`. It runs a dedicated local background Blender process. Its `bl_*` tools do not spend Higgsfield credits. Use it for isolated scene work or when desktop Blender is closed.

Start with `bl_health`, then `bl_get_scene_summary`. Read the MCP's `bl_get_skill(name: "blender-scene")` for scene guidance and `bl_list_skills` for the other bundled Blender workflows. Use `bl_open_project` for an existing saved `.blend`, make the requested edits, render evidence with `bl_render`, and save with `bl_save_project` before ending the session.

The existing `blender` MCP works in the currently open desktop Blender scene when its add-on server is started. Use that connection when the user wants to watch or continue work in the open scene. The `blender-background` MCP cannot see unsaved desktop changes; save the desktop file first, then open it in the background process. Background scenes are separate for each Codex or Claude connection.

For repeatable scripted work, the shared `blender` skill also supports Blender's headless Python CLI. If a task uses Higgsfield cloud generation, follow the video project's approval rule and the `higgsfield-generate` skill before every paid call.
