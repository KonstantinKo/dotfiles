---
name: code-review
description: Review standards, spec compliance, and behavioral correctness automatically after feature or fix implementation, or on an explicit review request. Use fresh independent subagents and verify their findings.
---

> Local rules: Honor project-specific review instructions and the user’s authorization boundaries. Keep findings in chat unless posting is explicitly requested. Use the active harness’s skill mechanism or read the named `SKILL.md`.
>
> Editable local copy from [mattpocock/skills](https://github.com/mattpocock/skills/tree/d81f3a183412e71a5b1e84ca21bc1a35eea03a60/skills/engineering/code-review). Source revision, update procedure, and local changes: [UPSTREAM.md](UPSTREAM.md).

Two-axis review of the exact task diff:

- **Standards**: does the code conform to this repo's documented coding standards?
- **Spec**: does the code faithfully implement the goal/spec, with correct behavior and acceptable regression risk?

Run both axes in **fresh parallel read-only subagents**, separate from the implementation agents. The primary agent verifies their findings before reporting or acting on them.

## Process

### 1. Pin the base and review scope

Use the supplied comparison base. Otherwise infer it from the current workflow, PR target, or an unambiguous upstream merge-base; ask only when the base cannot be inferred. Resolve it to a commit with `git rev-parse` and record the merge-base and current `HEAD`.

Capture `git diff <fixed-point>...HEAD` and `git log <fixed-point>..HEAD --oneline`, plus relevant staged, unstaged, and untracked task changes. Exclude unrelated changes explicitly; if task ownership is unclear, clarify that scope. Freeze the exact combined diff and file contents for both reviewers, including untracked files, so their review cannot silently follow later edits. An empty committed diff is valid when task changes are uncommitted; stop only if the combined scope is empty. Record the reviewed paths and which changes were excluded.

### 2. Identify the spec source

Use the goal, acceptance criteria, validation contract, or spec supplied by the orchestrator or user first. Otherwise look for a provided spec path, originating issue references in commits, or a matching spec under `docs/`, `specs/`, or `.scratch/`.

Read `docs/agents/issue-tracker.md` only when fetching an issue requires the repo's tracker workflow. Missing tracker configuration does not block a review with a supplied or local spec. If a referenced remote spec cannot be fetched, report that limitation rather than inventing its requirements. When no spec is available, the Spec reviewer still checks behavioral correctness and regressions, marking requirement compliance as unavailable.

### 3. Identify the standards sources

Anything in the repo that documents how code should be written, such as `CODING_STANDARDS.md` or `CONTRIBUTING.md`.

On top of whatever the repo documents, the Standards axis always carries the **smell baseline** below: a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when a repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation. Like any standard here, skip anything tooling already enforces.

Each smell reads *what it is* → *how to fix*; match it against the diff:

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy**: a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps**: the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches**: the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

### 4. Spawn both sub-agents in parallel

Start fresh read-only reviewers who did not implement the change. Give both the frozen exact diff, base/HEAD, commit list, relevant file contents, goal/spec, and applicable project/user instructions. They may inspect surrounding code and run appropriate read-only checks, but must leave fixes to the primary agent.

**Standards reviewer** also receives the standards-source files from step 3 and the smell baseline pasted in full. Ask it to report documented violations with the rule source and file/hunk evidence, and possible smells labelled as judgement calls. Repo standards override the baseline; skip checks already enforced by tooling. Under 400 words.

**Spec reviewer** checks missing or partial requirements, unintended scope, incorrect behavior, regression risks, and meaningful test gaps. Ask it to cite requirements where available and show the concrete triggering behavior and file/line evidence for correctness findings. Without a spec, review correctness and regressions while explicitly leaving requirement compliance unassessed; do not invent requirements. Under 400 words.

### 5. Verify and report

Check each proposed finding against current code and relevant behavior before accepting it. Discard false positives; distinguish documented violations, heuristic smells, and behavioral defects. If the reviewed scope changed, flag it and refresh the affected review rather than claiming the old review covers new changes.

When fixes are authorized, address verified issues, run focused checks, and repeat the affected independent review before considering the work done. Preserve unresolved limitations and product decisions for the user.

Report concisely under separate **Standards** and **Spec** headings, with verified findings and file/line evidence or a pass for each axis. Note unavailable spec compliance, excluded changes, and verification limitations when material. Give the count and worst issue within each axis; keep the axes separate rather than choosing an overall winner.

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.
