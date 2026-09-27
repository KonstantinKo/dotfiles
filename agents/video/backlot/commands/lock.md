---
description: Lock a Context element to an approved take
argument-hint: <take> <Cast/Name|Locations/Name|Props/Name> <reason>
---
Arguments: $ARGUMENTS (take id, Context note name, reason). Run `backlot approve <take> --lock <note> --reason "<reason>"`. Missing reason: ask for it first. Relay the one-line result and, if all four locks are now true, say the project can move to boards.
