---
name: game-assets
description: Use for any work that sources, generates, or records game assets such as models, textures, images, sprites, or video, including third-party downloads and paid fal.ai generation.
---

# Game assets

- Prefer free, license-clean sources (Poly Haven, Kenney, Quaternius) or generated assets. Record where every third-party asset came from in `ASSETS.md`.
- Paid generation services cost real money: check the credit cost first and keep usage modest.
- When fal.ai tools are available, use them for an explicitly requested fal model, reference-guided consistency, background removal/upscaling, or video. Prefer the built-in image generator for ordinary raster generation and the local `game-sfx` / `game-music` commands for audio drafts (see the `game-audio` skill). But if visual fidelity is a goal and a paid tool will get you better results than a free one, then you are actively encouraged to spend.
- fal.ai results in general are often more budget-friendly than in-engine DIY when compared to api-token-costs. Don't be afraid of using it if you deem the results usable.
- Save accepted outputs under the project's normal asset folder, and record the model ID, prompt, seed/settings, source URL, and actual or estimated cost in `ASSETS.md`. Never upload secrets or unrelated private files.
- For multi-step asset production (concept → model → engine), use the `asset-pipeline` skill.
