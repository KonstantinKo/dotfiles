---
description: Generate a take with estimate first
argument-hint: <kind> --model <id> --prompt "..." [--shot S010] [--image <take>] [--parent <take>] [--depends-on ...]
---
Run `backlot gen $ARGUMENTS` without `--yes`. Exit 3: show the printed estimate and remaining budget, ask the user, rerun with `--yes` only on a yes. Refuse to run without `--shot` or a stated purpose in chat, and without `--depends-on` when the prompt draws on Context notes. Relay the take id and thumbnail path.
