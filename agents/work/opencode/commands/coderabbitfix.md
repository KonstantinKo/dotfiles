---
description: Run local CodeRabbit CLI review/fix loop until clean
agent: build
---

# CodeRabbit Local Fix Loop

Run CodeRabbit CLI locally against current branch/worktree. Fix valid findings, verify, repeat until clean. Do not merge or push unless user explicitly asks.

## Rules

- Use local CodeRabbit CLI: `coderabbit review --agent`.
- If `coderabbit review --agent` times out after findings, treat captured findings as valid input, fix confirmed issues, then rerun.
- Verify each finding against current code before editing.
- Fix only valid actionable findings.
- Loop as long as needed to fix all verified findings. Stop only when clean or blocked. Apply a max loop count only if user specifies one in `$ARGUMENTS`.
- If none of the actionable findings verify, do not invent fixes; loop ends clean.
- Keep changes minimal.
- Do not commit, push, merge, or delete branches unless user explicitly asks.
- Do not force-push.
- Do not use destructive git commands.

## Preflight

1. Run `git status --short --branch`.
2. Inspect current change shape:
   - `git log --oneline -10`
   - `git diff --stat`
   - `git diff --cached --stat`
3. Create `todowrite` items for CodeRabbit loop, fixes, and verification.
4. Check CLI availability:
   - `coderabbit --help`

## Loop

Loop as long as needed to fix all verified issues. Use a maximum iteration count only when user explicitly provides one in `$ARGUMENTS`.

For each iteration:

1. Run local review:
   - `coderabbit review --agent`
   - Use generous command timeout, at least 15 minutes. CodeRabbit commonly takes a while; do not rush.
2. If output has no findings, stop.
3. If output has findings:
   - Parse each finding.
   - Verify against current code.
   - Fix confirmed issues with smallest correct edit.
   - Skip invalid/stale findings; record reason.
4. Run verification:
   - Prefer repo verify command such as `just verify`.
   - Also run targeted tests/builds for touched areas.
5. Rerun `coderabbit review --agent` with generous timeout, at least 15 minutes.

## Timeout Handling

If `coderabbit review --agent` times out:

1. Read captured output from tool result.
2. Fix any complete findings already printed.
3. Rerun review with longer timeout if needed.
4. If repeated timeout produces no findings and previous verification is green, report timeout as residual tooling risk instead of blocking forever.

## Final Report

Return compact report:

```text
CodeRabbit local loops: <n>
Fixed:
- <issue> -> <files>
Skipped findings:
- <finding + reason or none>
Checks:
- <command> -> <result>
Remaining risks:
- <risk or none>
```

## Additional User information

$ARGUMENTS
