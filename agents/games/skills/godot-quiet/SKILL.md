---
name: godot-quiet
description: Run a Godot project or exported macOS build with real GPU rendering and no visible window. Use for every Godot run that needs pixels (screenshots, test renders, movies, automated playthroughs, performance samples), including several at once.
---

# godot-quiet

`godot-quiet` is on PATH and takes the same arguments as `godot`. The game renders with the project's real renderer (Metal, Forward+ or whatever the project selects) at full frame rate, while its window stays off the screen: nothing appears on the desktop or in the Dock, focus stays where it is, and the user's mouse pointer is left alone. Audio defaults to the Dummy driver.

Choose the runner by what the run needs:

| Need | Command |
|---|---|
| Logic only: unit tests, import, export, parse checks | `godot --headless --path <project> ...` |
| Pixels: screenshot, movie, visual check, GPU timing | `godot-quiet --path <project> ...` |
| Pixels from an exported build | `godot-quiet --app <Game.app> ...` |
| The user asks to see or play the game | `godot --path <project>` |

`--headless` uses a dummy renderer and returns empty viewport images, so pixel work always goes through `godot-quiet`.

## Recipes

```sh
# Screenshot: a script that waits for frames, saves the viewport and quits
godot-quiet --path . --resolution 1920x1080 -s res://tests/capture.gd -- --out=/tmp/shot.png

# Movie or frame sequence at a fixed step
godot-quiet --path . --fixed-fps 30 --write-movie /tmp/run/frame.png --quit-after 300

# Exported app
godot-quiet --app "build/My Game.app" --quit-after 600
```

A capture script saves the frame after it has been drawn:

```gdscript
await RenderingServer.frame_post_draw
get_viewport().get_texture().get_image().save_png(out_path)
get_tree().quit()
```

## Rules

- Every run ends itself: `quit()` in the script or `--quit-after <frames>`. A watchdog stops the process after 900 seconds with exit code 142; set a different limit with `--timeout <seconds>` (0 disables it) before the Godot arguments.
- Exit code, stdout and stderr are Godot's own, so a script's `quit(1)` fails the command.
- Parallel runs are fine. Give each one its own output path.
- Drive the game with synthetic input (`Input.parse_input_event`, `Input.action_press`). The hidden window never gains focus, so `DisplayServer.window_is_focused()` is false and OS keyboard or mouse events never arrive.
- `--resolution WxH` sets the viewport size in pixels and may exceed the screen.
- `OS.alert` dialogs are suppressed and logged to stderr as `godot-quiet: suppressed alert`.

## How it works

The wrapper injects `quiet.m` (compiled once into `~/.cache/godot-quiet/`) through `DYLD_INSERT_LIBRARIES`. It keeps the macOS display server and blocks window ordering, app activation, fullscreen and pointer capture. Set `GODOT_QUIET_BIN` to use another editor binary. An exported app signed with the hardened runtime ignores the injection and shows its window; run such a project from source instead.
