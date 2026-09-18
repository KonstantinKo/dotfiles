---
name: blender
description: Use for any work that touches Blender, such as live scene editing through the blender MCP, headless Python scripts, renders, or exporting models for a game.
---

# Blender

- Blender 5.2 is at `/Applications/Blender.app` (`blender` on PATH).
- Live scene editing goes through the `blender` MCP server. It needs Blender running with the "MCP for Blender" panel's server started (3D viewport → N → MCP for Blender → Start MCP Server). If the MCP tools cannot connect, say so instead of guessing.
- For batch or repeatable work (asset generation, exports, renders), prefer Python scripts run headless: `blender -b file.blend --python script.py`. Keep scripts in the project so results are reproducible.
- Export game assets as glTF binary (`.glb`) unless the engine needs something else.
