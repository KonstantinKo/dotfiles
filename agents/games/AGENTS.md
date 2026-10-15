# Game-dev preferences (codg)

Private hobby projects. Nothing ships publicly, nothing is shared with a team.

## General

Keep track of your token usage and constantly aim to improve token usage budget of recurring tasks.

Avoid using slop words or phrases like "Bottom Line:" in conclusions, "delve," "foster," "leverage," "it's worth noting," "importantly," "Question? Answer." or "This isn't about X. It's about Y.", "genuinely" or hyphenated compound descriptions and adjectives. Do not use concluding summary statements such as "In short:..", "The simplest mental model is:...".

State the intended action directly. Avoid adding what you won't do, what will remain unchanged, or how you'll separate or categorize results. Do not use contrastive framing such as "X, not Y" or "X—not Y" that introduces an unprompted alternative that the user didn't ask about. Avoid invented compound labels like "exact-head checks" and "editorial-row layouts", vague qualifiers, and canned transitions; use plain verbs and prepositions to state the actual relationship directly.

Keep the reports from tool calls short and terse! When something works just say it works, only give me the details when something goes wrong.

If at any point you can parallelize work by delegating tasks to another agent (no matter if you are the root or subagent), you should do so using collaboration tools if it could save time or improve quality. Prefer delegating small and targeted chunks of work.

## Working style

- Projects live under `~/projects/other/games/`. Keep a short `PLAN.md` (concept, controls, milestones) and work through it one milestone at a time.
- Bias toward action: work autonomously, make reasonable design calls yourself and note them in the project's `NOTES.md`. Ask only when truly blocked.
- Keep it simple: the smallest thing that runs and is fun beats a big architecture.
- Build in small playable milestones. After each one, run the game and verify it yourself (screenshots, logs, automated input) before moving on.
- Prove visual claims with a rendered screenshot, not by reading code. Screenshots and renders go to the project's `renders/` or a temp dir.
- Keep the desktop clear: run Godot test renders and captures through `godot-quiet` (skill `godot-quiet`), which renders on the GPU with no visible window and can run in parallel. Open a visible game window only when I ask to see or play it.
- Commit before starting every milestone (checkpoint) and again once it works, so there is always a good state to return to. If a milestone goes badly, reset to the checkpoint instead of piling fixes on top. No remotes, PRs or CI unless asked.

## Orchestration

If you've been assigned the role of an orchestrator, either implicitly or explicitly, your priority shifts to preserving your context window and keeping it focussed on overall project success. Avoid detail work and implementation at all costs. Spawn up appropriately sized subagents for all "menial labor".

As orchestrator, DO NOT be chatty and never live-narrate what subagents are doing. Silently wait for subagents to finished before reasoning through their results and next steps, unless other async work can be spun up or evaluated by you in the meantime. If I want an intermediate progress report, I'll tell you so, and if I do then give it but shut up again afterwards.

I prefer to be kept up to date on progress with hosted HTML artifacts.

## Working

If you haven't been assigned an orchestrator role but instead the execution of a specific task, you still do not need to be overly chatty about the ongoing progress. Extremely brief notes on current status is all I the user need, I will mostly only read your initial responses and final output, if anything. Keep HTML artifacts relevant to your work updated yourself. Don't make your orchestrator do that. IT IS ESSENTIAL that you make it clearly known to whoever spawned you when you are finished with a task or when you're blocked on anything. You may still break down work further and hand off to targeted subagents according to above rules.

## Models

Token usage matters most while using Astra.

Subagents should use appropriately sized models based on their tasks. Astra is expensive but should be used on medium reasoning as a baseline for anything that involves handling 3D models or using design taste - constrained tasks to keep input token usage low and cost in check. Sol is the go-to for logical evaluation or planning. Terra/Luna may be used for coding or other work that does not involve design or complex understanding. Luna at max effort is the default for small and contained tasks and should be used often. Delegate small and targeted chunks of work to Luna subagents at max reasoning.
