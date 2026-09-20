---
name: reflect
description: Review repeated workflow friction and propose smallest reusable improvement. Use when user asks to learn from recent sessions or improve recurring agent workflow.
---

# Reflect

Find repeated, evidenced workflow friction. Recommend smallest useful improvement,
including no change.

## Evidence

Inspect in order:

1. Current conversation and explicit user feedback.
2. Existing AGENTS.md, skills, commands, config, task journals, and project docs.
3. Recent relevant session artifacts when safe and necessary.
4. External docs only when proposal depends on third-party behavior.

Do not inspect unrelated personal data, credentials, or private systems.

## Evaluation

Strong candidates have repeated occurrences, meaningful cost/risk, stable inputs,
clear output, and clear stopping condition.

For each candidate assess:

- frequency;
- context/token/time cost;
- inconsistency or safety risk;
- stability;
- existing coverage.

## Smallest Useful Form

Prefer, in order:

1. No change.
2. Small existing instruction/config adjustment.
3. Project playbook or durable decision doc.
4. Reusable skill.
5. Manual command for stable explicit workflow.
6. Dedicated agent only when role needs genuinely distinct model/tool boundary.

Avoid fixed specialist personas when capable primary model can choose workflow.
Avoid overlapping assets and speculative automation.

## Change Gate

Present evidence and proposal before modifying global prompts, skills, commands,
agents, plugins, MCPs, or permissions unless user explicitly requested exact edit.
State restart requirement for OpenCode config-time changes.

## Output

Report:

- repeated findings and evidence;
- smallest recommended changes;
- candidates skipped and why;
- evidence still needed.

Creating nothing is valid success.
