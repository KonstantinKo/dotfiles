---
description: Generate a take with estimate first
argument-hint: <kind> --model <id> --prompt "..." [--shot S010] [--image <take>] [--parent <take>] [--depends-on ...]
---
Run the dry-run quote first. On exit 3, show the exact quote and remaining budget, then follow [Decision and spend](../skills/studio/references/decision-and-spend.md) to record explicit approval and execute the exact call with `--yes --authorization <id>`. `--yes` alone is never approval; free/local calls need no spend authorization. Refuse to run without `--shot` or a stated purpose in chat, and without `--depends-on` when the prompt draws on Context notes. Relay the take id and thumbnail path.
