# Execution and shared contract

## Choose an execution path

Resolve supports Lua 5.1 and Python scripting. For scripts the user will paste, return a complete Lua script that can run in **Workspace > Console** with the Console language explicitly set to **Lua**; scripts in Resolve's supported `Fusion/Scripts` folders appear under **Workspace > Scripts** after startup. Inside Resolve, `resolve`, `bmd`, and `fusion` are provided as globals. A script may also initialize its handle with `local resolve = Resolve()` as Blackmagic's own Lua examples do.

Make a paste-ready script self-contained: put a short `CONFIG` table at the top, resolve the intended project/timeline/items, and assert exact stable IDs when known before the first write. If live inspection could not supply IDs, require an exact unique name plus project/timeline context, print the resolved IDs, and stop if a match is missing or ambiguous. Check every mutation's return value; print a final result with target IDs, counts, and output paths as relevant. State the expected Console output and whether a rerun is safe. Make reruns idempotent when practical; otherwise detect prior application and fail with a clear message. Do not rely on a top-level Lua `return` to display results or to exit a pasted Console chunk. For a large script, give the `.lua` file and an explicit `dofile("/absolute/path/to/script.lua")` Console command, or direct the user to the Scripts menu. If live execution is unavailable, state plainly that the script was not run in Resolve.

A typical handoff keeps target and edit choices together:

```lua
local CONFIG = {
    projectId = "resolved-project-id",
    timelineId = "resolved-timeline-id",
    targetItemIds = { "resolved-item-id" },
    -- requested values and output paths belong here too
}

assert(project:GetUniqueId() == CONFIG.projectId, "Wrong project; no edits made")
assert(timeline:GetUniqueId() == CONFIG.timelineId, "Wrong timeline; no edits made")
-- Resolve each configured item ID and assert exactly one match before writing.
```

Use actual resolved values in the delivered script. If inspection is unavailable, the script may resolve by an exact unique name under asserted project/timeline context, but it must fail on zero or multiple matches and print the stable ID it resolved. Never present placeholder IDs as a ready-to-run script.

External scripting is a separate path: Resolve must be running, the external-scripting preference must allow it, and the installed edition/runtime must support the requested connection. Do not require external MCP setup to author or run an in-app script. Treat Free versus Studio as a capability of the current operation and channel; do not infer that no useful script can be written or that every task requires handoff.

The current Higgsfield `/use-davinci` MCP covers Color inspection/version, CDL and LUT operations, saving, and Studio integration. It does not expose the whole Resolve API or a full Fusion bridge. Use only its actual tools and schemas when choosing it; use documented in-app scripting for operations beyond that scope.

## Bound and verify edits

Inspect the active project, timeline, target object, and relevant settings before changing them. Match a target by a stable `GetUniqueId()` where available and confirm its name/context; names and list indices can change or collide. Reacquire handles after structural changes such as adding or removing timeline items, tracks, media, or Fusion comps.

Keep writes bounded to the requested clips, tracks, frame ranges, properties, and output paths. Prefer explicit item handles and narrow arrays over operations on all clips, all jobs, or the entire project. Check every API return value, then read back changed values and confirm the affected object still matches the intended target. A successful call is not proof that the requested state persisted.

Resolve scripting calls are not a transactional batch. If a call fails, times out, or returns an ambiguous result, inspect current project state before retrying; a mutation may already have happened. Do not replay a non-idempotent edit based only on a missing response. Save when requested or needed to preserve the authorized result, and verify the save call's return value.

Before edits that reorganize or remove timeline items, tracks, media, or Fusion comps, create and verify a separate project backup or duplicate through a supported Resolve path. Routine reversible property edits do not need a blanket approval stop; preserve a return path in proportion to the structural risk.

Do not invent API names from UI labels or assume a UI feature has a scripting equivalent. Check the installed `DaVinciResolveScript.pyi` and official examples. For Fusion-specific scripting, consult the installed Fusion scripting docs/API; a `FusionComp` handle alone does not establish what operations it supports.
