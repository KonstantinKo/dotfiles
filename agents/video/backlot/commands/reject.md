---
description: Reject a take with a reason
argument-hint: <take> <reason> [<source-ref> <review-evidence-or-rejection>]
---
Arguments: $ARGUMENTS (take id, reason, and review or user evidence when available). Run `backlot reject <take> --reason "<reason>" --source-message "<review evidence or explicit user rejection>" --source-ref "<artifact path/timecode or user message reference>" --scope "<rejection scope>"`. A reviewer may reject on evidence; do not represent it as the user's decision. Never invent source evidence. The CLI permits legacy omission of source flags, but new records should include concrete evidence when available. See [Decision and spend](../skills/studio/references/decision-and-spend.md). Relay the result and offer a variation (`--parent <take>`) when the reason is fixable in the prompt.
