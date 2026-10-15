---
description: Approve a take with a reason
argument-hint: <take> <reason> <source-ref> <approval-message>
---
Arguments: $ARGUMENTS (take id, reason, exact user approval text, and its message reference). Run `backlot approve <take> --reason "<reason>" --source-message "<explicit approval text>" --source-ref "<user message reference>" --scope "<approved use>"`. Do not infer approval from feedback or a broad project decision. Missing source text/reference or reason: ask. See [Decision and spend](../skills/studio/references/decision-and-spend.md). Relay the result; if the take belongs to a shot, name the shot's new status.
