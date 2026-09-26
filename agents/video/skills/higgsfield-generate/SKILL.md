---
name: higgsfield-generate
description: Use Higgsfield's signed-in CLI for image or video work in a video project, including model discovery, cost estimates, approved generation, and reviewing results. Do not use for game projects.
---

# Higgsfield generation

The `higgsfield` CLI at `~/.local/bin/higgsfield` uses this Mac user's signed-in Higgsfield subscription. Check `higgsfield --help` and subcommand help for current syntax. If authentication expires, use `higgsfield auth login --port 18765`; port 8765 conflicts with another local server here. Never expose login tokens or callback URLs.

## Before each paid call

1. Identify the exact model, prompt, reference files, settings, and intended output. Query the model schema if needed. For a Backlot production, also follow its `project.yaml`, budget, and `backlot` workflow.
2. Run the CLI's read-only cost estimate for those exact inputs (`higgsfield generate cost ...`) and check the current balance (`higgsfield account status`). Cost estimation may upload supplied reference files; select only files the user intends to send.
3. Show the user the model, inputs, settings, estimated credits, and balance. Ask for explicit approval for **that one call** and wait for an affirmative reply. A request to set up tools, follow a tutorial, or test a workflow is not approval to spend.
4. Run only the approved call. If the inputs, settings, or price change, estimate again and get fresh approval. Do not automatically retry, reroll, or start a second paid call.
5. Record the result and actual credit charge in the project's `ASSETS.md` and `NOTES.md` when those files exist.

Read-only discovery and local previews can proceed without a paid call. Treat video, image, audio, 3D, and marketing generation through Higgsfield as paid unless a current cost estimate proves otherwise.
