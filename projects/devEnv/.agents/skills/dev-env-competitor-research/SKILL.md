---
name: dev-env-competitor-research
description: devEnv competitor research workflow adapted from Opencode competitorResearch. Use for product/UX/workflow/integration questions needing current external precedent, competitor patterns, weaknesses, opportunities, and `.project/docs/work/**/research/**` handoff files.
---

# Dev Env Competitor Research

Verify current repo is devEnv before running.

## Required Reads

- `.project/docs/plan/listFormatGuide.md`
- `.project/docs/work/README.md`
- `.project/docs/feature/README.md`
- `.project/docs/architecture/router.md`
- `.project/docs/architecture/admin.md`
- `.project/docs/architecture/templates.md`
- `references/opencode-command-do-competitorResearch.md`
- `references/opencode-agent-competitorResearch.md`
- mini-agent refs under `references/opencode-agent-competitor*.md`

## Codex Adaptation

- Preserve the Opencode competitor research semantics from copied refs.
- Use current web research. Cite URLs.
- Separate evidence from inference.
- Spawn `dev-env-competitor-search`, then `dev-env-competitor-feature`, then `dev-env-competitor-weakness` subagents when useful.
- Only edit `.project/docs/work/**/research/**`.

## Output

Write:

- `.project/docs/work/YYYY-MM-DD-topic/research/search.md`
- `.project/docs/work/YYYY-MM-DD-topic/research/feature-<productSlug>.md`
- `.project/docs/work/YYYY-MM-DD-topic/research/weakness-<productSlug>.md`
- `.project/docs/work/YYYY-MM-DD-topic/research/result.md`

Return a compact pointer with status and blockers.
