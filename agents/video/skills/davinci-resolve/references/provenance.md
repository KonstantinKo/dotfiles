# Provenance and validation

This is a local adaptation of transferable workflow ideas from `fnf-after-effects-mcp-0.1.3`, especially `ae-mcp-realities` and `ae-clean-rig/references/09-validation-delivery.md` plus `10-ae-scripting.md`. The original corpus is at:

`/Users/konstantin/projects/video/labs/higgsfield-motion-research/sources/fnf-after-effects-mcp-0.1.3/skills/after-effects`

Adapted ideas include bounded edits, stable target resolution, readback after mutation, inspection before retrying uncertain operations, and checking actual rendered output. AE-specific APIs and assumptions were not carried over. This is not an official Higgsfield port of Resolve guidance.

For Resolve API details, prefer the installed Blackmagic documentation:

- `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/README.md`
- `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/DaVinciResolveScript.pyi`
- The adjacent official `Examples` directory

The local README identifies the API as updated 31 Aug 2026; the installed `.pyi` was dated 10 Sep 2026. Validation here is static: the reference Lua probe is syntax-checked, and the skill is checked with `quick_validate.py`. No Resolve app was launched, no project was connected or modified, and no render was produced or visually reviewed during skill authoring.
