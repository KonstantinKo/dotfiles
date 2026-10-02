---
name: davinci-resolve
description: Operate DaVinci Resolve projects and author Resolve automation scripts. Use for media, timeline, Fusion, color, render, and project work in Resolve; specialized motion, captions, and localization workflows have dedicated sibling skills.
---

# DaVinci Resolve

Use the installed Resolve scripting API as the authority for live automation. Prefer Studio live automation when the connected app and available interface support the requested operation. A limited MCP is not a general Resolve or Fusion bridge. If live access is unavailable, keep making useful progress: when the user asks for a script, provide complete runnable Lua for **Workspace > Console** in Lua mode, or a `.lua` file for **Workspace > Scripts**. Do not make the installed edition a global reason to hand off; distinguish authoring a script from whether this session can execute it.

Read [execution and shared contract](references/execution-and-contract.md) for entry points, API boundaries, and safe project edits. Read [timeline, media, and render operations](references/timeline-media-render.md) for the confirmed API surface and verification. The small [capability probe](references/capability_probe.lua) is a read-only in-app Lua example. See [provenance](references/provenance.md) for source boundaries and validation status.

For focused workflows, follow [davinci-resolve-motion](../davinci-resolve-motion/SKILL.md), [davinci-resolve-captions](../davinci-resolve-captions/SKILL.md), or [davinci-resolve-localization](../davinci-resolve-localization/SKILL.md). Keep this skill's execution contract when using them.
