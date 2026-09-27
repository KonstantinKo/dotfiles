---
description: Launch competitorResearch agent for feature competitor research
agent: competitorResearch
subtask: true
---

# Do Competitor Research

Run competitor research for this feature description:

```text
$ARGUMENTS
```

Return the final `## Competitor Research Result` in nested list format. The `competitorResearch` agent must delegate external research only to its hidden mini research subagents.

The `competitorResearch` agent must always persist research under `.project/docs/work/YYYY-MM-DD-topic/research/` with agent-owned files: `search.md`, `feature-<productSlug>.md`, `weakness-<productSlug>.md`, and `result.md`, writing early and updating after each major phase.
