---
name: davinci-resolve-motion
description: Build or repair editable motion graphics and 2D character animation in DaVinci Resolve Studio's Fusion page. Use for reference matching, kinetic typography, Fusion rigs, reusable motion templates, or animation review; use davinci-resolve for application access and scripting.
---

# Resolve motion in Fusion

Use the installed **DaVinci Resolve Studio** and the user's current project when available. This skill guides design and construction; [davinci-resolve](../davinci-resolve/SKILL.md) owns connection, execution, API discovery, backups, and deliverable handling. A user can also ask for a Python or Lua script to paste into Resolve's Console or place in its Scripts menu. Author that script from documented and probed behavior, syntax check it, and state plainly when it has not run in Resolve. Script authoring alone does not require an MCP connection or app launch.

Treat a supplied reference or approved existing result as the target. Record its actual frames, holds, cuts, moving and stationary parts, text hierarchy, and visible motion causes. For a text-only brief, choose and record a coherent visual direction before animation. Make a small component and timing map, then build a representative still and motion passage before multiplying components. Read [reference and timing](references/reference-and-timing.md) for reconstruction, match cuts, easing, and review.

Translate each meaningful object into a named Fusion branch: source artwork or Text+ → local transforms, masks, and effects → Merge into the scene. Use a Group for a readable reusable subgraph, or a separate Fusion composition/clip when an independent timeline source is useful. Keep source identity and timing explicit; a copied group or composition may still depend on shared media or controls. Read [native construction](references/native-construction.md) before designing text, shapes, deformation, or scripts.

Animate the smallest cause that explains the observed change: shared movement on a parent Transform or group, local keys on independent parts, and deformation only where the silhouette actually changes. Use sparse pose and event keys, shape their interpolation in Fusion's Spline editor, and inspect frames between keys. Preserve hard cuts, linear passages, stationary elements, and deliberate holds. Do not apply one generic ease or automatic bounce to every object.

Expose a small set of useful named controls with units, defaults, and tested ranges. Keep manual adjustments independent of optional demonstration timing. For Edit page reuse, choose and test the intended Fusion macro/template controls on the actual target page; a Group alone does not establish a usable template. Read [controls and templates](references/controls-and-templates.md) when editability or reuse is requested.

For illustrated characters, read [2D character rigs](references/character-rigs.md). Design around separated artwork, pivots, occlusion, and tested deformation. AE Puppet pins and Essential Properties are not direct Fusion features; choose native Fusion methods by the required motion and verify their behavior.

Render the **nested timeline result** at representative frames and a playable interval. Check start, extrema, transitions, settle, last visible frame, text fit, matte edges, and any repeated or reused instances. Test one real content or control edit in a duplicate, restore intended values, and report what was actually inspected. A saved graph, script return, or queued render is not visual proof.
