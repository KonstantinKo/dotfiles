---
description: Lock a Context element to an approved take
argument-hint: <take> <Cast/Name|Locations/Name|Props/Name> <reason> <source-ref> <approval-message>
---
Arguments: $ARGUMENTS (take id, Context note name, reason, exact user approval text, and its message reference). Run `backlot approve <take> --lock <note> --reason "<reason>" --source-message "<explicit approval text>" --source-ref "<user message reference>" --scope "lock <note>"`. Missing source text/reference or reason: ask first. See [Decision and spend](../skills/studio/references/decision-and-spend.md). Relay the one-line result and, if all four locks are now true, say the project can move to boards.
