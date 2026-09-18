---
name: game-loop
description: Use for starting or continuing game-building work in small verified milestones; not for neutral orchestration, reviews, workflow editing, story work or unrelated tasks.
---

# Game Building loop

Build the game in small playable milestones, verifying each one yourself before moving on. Work without asking unless truly blocked.

## Scope and role first

Read project instructions, the active plan and any current assignment before choosing a milestone. Existing design pauses, reference authority, specialist visual gates and explicit write scopes take precedence over historical unchecked tasks. Do not initialize or replace an existing project plan. A neutral supervisor can dispatch and review workers without adopting this implementation loop; inspection of this skill is not activation.

Direct autonomous implementation continues through authorized milestones. A supervised worker completes full correction/check/diagnosis/follow-through cycles within its assignment, returning evidence at a meaningful reviewable outcome or the assigned work-period boundary, or a genuine blocker; if no boundary is stated, use the assigned milestone's reviewable outcome. Related local cycles may continue within that period without a fixed trial-count stop, but the worker does not self-promote a stage or start an unassigned milestone. The supervisor reviews and dispatches further work. Respect parent-owned commits, shared records and single-writer resources; report updates for their owner instead of editing outside scope.

## 1. Set up (once)

- Project directory: `~/projects/other/games/<short-slug>`. `git init` if it is not a repo yet.
- Engine: use the one the user named; otherwise Unity for 3D, Godot for small or 2D games.
- Unity projects (6.3 LTS, URP): create them only with `unity projects new <name> --path <dir> --editor-version 6000.3.24f1 --template com.konstantin.template.codg-urp`, never by writing `ProjectSettings`/`Packages` files by hand (hand-picked package versions break compilation). That template already has the MCP package, glTFast, the bridge auto-start script and upgraded URP materials, so no setup or dialogs are needed. Only if that template is missing, use `--template com.unity.template.urp-blank` and then, before the editor is first opened:
  - add `"com.coplaydev.unity-mcp": "https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v10.2.0"` and `"com.unity.cloud.gltfast": "6.20.0"` to `Packages/manifest.json`;
  - copy `unity/McpBridgeAutoStart.cs` from this skill's folder to `Assets/Editor/McpBridgeAutoStart.cs`.
  
  Then open it once with `unity open <project>`. The Unity MCP tools connect within about 30 s. Check first that no other Unity editor is running.
- Godot projects: install the godot-ai add-on (release `v4.0.4`, `godot-ai-v4-plugin.zip`) into `addons/godot_ai` and enable it in `project.godot`; the Godot MCP tools connect once the editor is open.
- If the engine MCP tools still don't respond, carry on with the CLI (`unity`, `godot --headless`) and editor scripts rather than stopping.
- Write `PLAN.md`:
  - **Concept**: one paragraph.
  - **Core loop and controls**.
  - **Look**: art direction, palette, lighting mood, reference style.
  - **Milestones**: 5–8 entries, each playable on its own, each with a concrete *done when* that a screenshot, test or log can prove.
  - **Progress**: a log, appended as you go.
- Commit: `plan: <game>`.

## 2. For each milestone

1. **Checkpoint**: inspect working and staged diffs. When you own commits, stage only your reviewed paths/hunks and commit `checkpoint: before <milestone>` if needed. Preserve unrelated or pre-staged changes; do not commit them incidentally. When the parent serializes commits, identify the baseline and leave commits to it. Never use blanket staging in a shared worktree.
2. **Build** the smallest version that satisfies *done when*. First check that the chosen edit scope can resolve the dominant problem; include related provisional implementation when needed, preserving user-approved constraints, explicit write boundaries and unrelated work.
3. **Compile/run**: read every error and warning you caused and fix them before going further. In Unity, wait for compilation to finish and read the console.
4. **Test**:
   - Run relevant existing tests and meaningful checks for changed behavior (`unity test` EditMode/PlayMode, or a headless Godot test script). Scale verification to risk; trivial reversible edits do not need new test suites.
   - Run changed playable behavior, simulate relevant inputs, and capture screenshots for visual claims. Documentation-only assignments do not require launching the engine.
5. **Review**: compare relevant evidence with *done when*, then fix what is off. For visual claims, inspect screenshots against the **Look** section; visual polish counts. Nonvisual changes can be reviewed through executable checks and logs without a screenshot or editor launch.
6. **Record and commit**: record what works, evidence and remaining limits in the plan's existing progress location, then commit only reviewed in-scope changes as `milestone <n>: <name>` if you own commits. Otherwise return these to the parent. Keep working trials, retained baselines, criterion-specific verification and explicit user acceptance distinct.

When an approach repeatedly makes no material progress, diagnose the failing assumption against the retained baseline, change the approach or editable scope within the assignment, and carry out justified follow-through while the work period permits. Local failure calls for adaptation, not an automatic worker return or unbounded repetition. Do not mark the milestone done or skip its unmet requirement because compilation, export or an unrelated test passed. Feasibility probes can run early without promoting the requested result.

Recover only your identified trial edits using scoped patches or an isolated saved candidate. Preserve concurrent changes and the last useful source/evidence. Never reset the entire worktree or restore a mixed-ownership file wholesale; when edits overlap, inspect and reconcile them, escalating only an actual unresolved conflict.

## 3. Assets and audio

- When implementation needs a substantial asset, use the available `asset-pipeline` skill: search the project library first, then specify dimensions, visible sides, interaction and delivery needs. If delegation is authorized, spawn an asset worker with that skill and request, continue independent scene work with a stable proxy, review its return and register the accepted revision. Do not regenerate an existing compatible asset or assume source review establishes runtime readiness.
- Free libraries first: Poly Haven through the Blender MCP, Kenney, Quaternius, KayKit. Log sources in `ASSETS.md`.
- Simple props: model them in Blender and export `.glb`.
- Paid generation (fal MCP) only if it is available in this session, with the cost checked first.
- Sound: `game-sfx` for effects and `game-music` for music (see AGENTS.md).

## 4. Finish

For direct work, stop at the authorized endpoint or a blocker that requires new input/authority. For supervised work, return at the meaningful outcome/work-period boundary or a genuine blocker, reporting unresolved stagnation or missing evidence; a batch return is not project completion. Report:
- what is playable,
- how to run it,
- relevant evidence (the last screenshot for visual claims; checks/logs for nonvisual changes),
- open issues.

Include the revision/checkpoint, checks actually performed and the next recommendation. For visual reconstruction, use the applicable reconstruction skill's reference and spatial evidence; passing gameplay checks alone does not establish resemblance. Stage promotion under supervision belongs to independent review, and user acceptance requires explicit user selection.
