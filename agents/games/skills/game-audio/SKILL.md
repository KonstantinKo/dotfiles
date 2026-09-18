---
name: game-audio
description: Use for any work that creates or places game audio, such as sound effects, music, ambience, or loops, using the local game-sfx and game-music commands.
---

# Game audio

Local and free, no API keys. Run one generation at a time (each loads its model).

- Sound effects: `game-sfx "<prompt>" -o <file>.wav [-d seconds]` (default 2 s, under a second to generate). Example: `game-sfx "8-bit coin pickup, retro chiptune blip" -o Assets/Audio/coin.wav -d 1`.
- Music: `game-music "<prompt>" -o <file>.wav [-d seconds]` (default 30 s, instrumental, ~30–50 s to generate; `--fast` for drafts, `--bpm`, `--key`). Example: `game-music "calm fantasy village ambient loop, harp, flute" -o Assets/Audio/village.wav -d 60`.
- Put audio in the project's audio folder (`Assets/Audio/` in Unity, `res://audio/` in Godot), log prompts in `ASSETS.md`, and crossfade music loops in the engine since the ends may not loop seamlessly.
