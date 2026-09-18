---
name: game-engines
description: Use for any work inside a Unity or Godot project, such as opening editors, scenes, prefabs, scripts, builds, headless checks, engine MCP tools, or in-engine screenshots.
---

# Game engines

- Unity (MCP for Unity) and Godot (godot-ai) MCP tools are always configured; they connect once the project's editor is open with the add-on installed (the `game-loop` skill lists the setup for new projects). If they don't respond, fall back to the CLI and editor scripts instead of guessing.
- Visual quality matters more than feature count: start from a tuned look (HDRI sky, tonemapping, bloom, ambient occlusion, colour grading) and check it in screenshots.

## Unity

- Unity 6.3 LTS (URP). Use the `unity` CLI for builds, tests and editor installs. Change scenes and prefabs only through MCP tools or editor scripts, never by hand-editing `.unity`/`.prefab` YAML. After editing C# scripts, wait for compilation to finish and read the console errors before doing anything else.
- Start Unity only via `unity open <project>`, run outside the sandbox (request escalated permissions); never launch the `Unity.app` binary directly, because inside the sandbox Unity loses its licensing service and the project never loads. Before opening, check `unity editors running` and reuse an editor that already has the project open.
- Open Unity projects with a plain `unity open <project>`; the project's `Assets/Editor/McpBridgeAutoStart.cs` starts the MCP bridge. Projects without it: add it from the `game-loop` skill folder.
- Run at most one Unity editor at a time; this machine cannot handle more. Close one project's editor before opening another, and never launch extra editors to test something.

## Godot

- Godot 4.7 (`godot` on PATH), GDScript only. `.tscn`/`.gd` files are plain text and safe to edit; run headless checks with `godot --headless --path <project> --quit`.

## Screenshots

If a screenshot tool returns no image, save the PNG to disk and open it with the image viewer tool. In Unity, Game View captures are only written on the next rendered frame; if the file does not appear, use a Scene View screenshot or render the main camera into a RenderTexture from an editor script and save that PNG.
