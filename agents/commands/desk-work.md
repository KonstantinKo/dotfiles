---
description: Pick up an answered agentdesk item in a fresh main session and do the work.
disable-model-invocation: true
---

# /desk-work

You are a **worker**, not a manager. This is a full main session. You may do actual work: code, fixes, execution, verification, and follow-through until done or blocked.

The item to pick up, as a slug or path, follows at the end of this prompt.

1. Resolve it in `/Users/konstantin/projects/obsidian/agentdesk/desk/items/` and read the whole file: body, `## Resume`, and `## Answer`.
2. Before editing, building, or running dev servers, create or use a dedicated git worktree. If the `## Resume where` path is the main checkout, create a new worktree/branch for the item and follow that repo's worktree setup checklist. If `where` already points at an isolated worktree, use it. Do not do desk-work implementation in the main checkout.
3. Do the work described in that worktree, continuing from where the producer left off, guided by the user's decision in `## Answer` and the `## Resume` block (`where`, `do`, `done when`, `pointers`).
4. When finished, update the item header (`status: done`, `updated` UTC), and if fully closed move it to `archive/`. If new loose ends or follow-ups appear, log them per `/Users/konstantin/projects/obsidian/agentdesk/desk/PRODUCER.md`.
5. If blocked again, set the item back to `needs-input` with a fresh `## Resume` block and stop. This keeps the same park-and-respawn loop.

Item:

$ARGUMENTS
