---
name: autotune
description: Manually-started keep-or-revert loop (inspired by karpathy/autoresearch) that makes one of my skills measurably better. Use when the user wants to improve, optimize, tighten, or tune a specific skill, or invokes /autotune <skill-name>. Auto-drafts a frozen eval set (trigger prompts + sample inputs + rubric) behind a mandatory approval gate, then iterates variations of the skill on scratch copies, keeping only versions that pass a triggering-accuracy gate and improve a rubric score, until 3 rounds yield no improvement. Writes the winner back to the real skill file only after the user confirms. Never runs automatically.
user_invocable: true
---

You optimize a single skill through an autoresearch-style modify, measure, keep-or-revert loop. You run only when invoked. You never start automatically and you may be interrupted at any time. Follow these instructions verbatim.

The transferable ideas from autoresearch: one comparable metric, a frozen evaluation basis, keep-or-revert per iteration, an append-only experiment log, and a simplicity bias (improvement-by-deletion is valued).

# Invocation

`/autotune <skill-name>` optimizes the named skill.

1. Parse the argument as `<skill-name>`.
2. If no argument is given, ask the user which skill to tune. Do not guess.
3. Resolve the scratch directory once and reuse it for the whole run:
   `SCRATCH="${CLAUDE_JOB_DIR:+$CLAUDE_JOB_DIR/tmp}"; [ -z "$SCRATCH" ] && SCRATCH="$(mktemp -d)"; RUN_DIR="$SCRATCH/autotune-<skill-name>"; mkdir -p "$RUN_DIR"`
4. Proceed to Setup (target resolution).

# Setup: resolve the target skill

Skills live in two roots, in two layouts each. Resolve `<skill-name>` to one file:

```bash
NAME="<skill-name>"
ROOTS=( "$HOME/.claude/skills" )
[ -d "$PWD/.claude/skills" ] && ROOTS+=( "$PWD/.claude/skills" )
MATCHES=()
for R in "${ROOTS[@]}"; do
  [ -f "$R/$NAME/SKILL.md" ] && MATCHES+=( "$R/$NAME/SKILL.md" )
  [ -f "$R/$NAME.md" ]       && MATCHES+=( "$R/$NAME.md" )
done
printf '%s\n' "${MATCHES[@]}"
```

- 0 matches: tell the user the skill was not found and list the roots searched. Stop.
- More than 1 match: show the matches and ask the user which one to target. Do not guess.
- Exactly 1 match: set `SKILL_PATH` to it.

Then snapshot the original and validate it:
- `cp "$SKILL_PATH" "$RUN_DIR/original"`
- A skill file is structurally valid if it begins with a `---` frontmatter block containing at least a `description:` line. If `$RUN_DIR/original` is not valid, tell the user and stop (autotune optimizes existing valid skills only).

From here on, never edit `$SKILL_PATH` directly. All work happens on copies under `$RUN_DIR`.

# Build the frozen eval set

The metric is only comparable if the evaluation basis is fixed. Build it once, here, and never change it during the run.

1. Read `$RUN_DIR/original` (description, body, any embedded examples).
1b. **Ground the eval set in real failures before drafting.** A set drafted only from the skill's own description optimizes against imagined use, not observed pain. First pull what actually went wrong:
   - Grep the agentdesk vault (`/Users/konstantin/projects/obsidian/agentdesk`) for the target skill's name: `friction:` lines in `01 Daily/*.md`, "Friction → fixes" sections in weekly notes (`01 Daily/*-W*.md`), and `desk/items/` + `desk/archive/` bodies. Each hit becomes a labelled eval case: a **sample input** (reconstruct the scenario) and, where it was a mis-fire, a `NO-FIRE` **trigger prompt**.
   - If nothing in the vault names this skill, say so and fall back to drafting from the description alone.
2. Draft three things (seed them with the grounded cases from 1b, then fill gaps):
   - **Trigger prompts:** about 12 user-message examples, each labelled `FIRE` (the skill should activate) or `NO-FIRE` (it should not). Include near-miss negatives: plausible-sounding messages a too-greedy description would wrongly catch. Cover the skill's real triggers from its description.
   - **Sample inputs:** 2 to 3 representative inputs the skill would actually run on, used to judge output quality.
   - **Rubric:** 3 to 6 criteria, scored together 0-100, describing what a good run of THIS skill looks like (specific to its job, not generic).
3. Present the full draft to the user and ask them to edit, cut, or add cases. This approval is mandatory and blocking: do not proceed to scoring until the user approves. A bad eval set silently optimizes the skill in the wrong direction.
4. On approval, write the approved set to `$RUN_DIR/eval.md` with three clearly delimited sections (`## Trigger prompts`, `## Sample inputs`, `## Rubric`) and treat it as frozen for the rest of the run.

Obey the writing rules in everything you draft: no em-dash, no double hyphen.

# Score a candidate

Given a candidate skill text and the frozen `$RUN_DIR/eval.md`, produce one comparable result.

1. **Structural check.** If the candidate lacks valid frontmatter (a `---` block with a `description:`), record the result as `crash` and stop scoring it.
2. **Triggering accuracy.** For each trigger prompt in `eval.md`, decide whether a skill with this candidate's description would fire on that prompt. Judge each prompt against the candidate's `description:` frontmatter plus any explicit trigger or no-trigger guidance in its body (the parts that govern when the skill activates), not the full how-to body. Compare to the frozen `FIRE` / `NO-FIRE` label. `triggering_accuracy = correct / total`.
3. **Rubric score.** For each sample input, run the candidate skill's instructions on that input (dispatch a subagent given the candidate skill text plus the input, capture its output). Then judge the collected outputs against the frozen rubric for a single `rubric_score` from 0 to 100.
4. **Result.** Return the triple `(gate_passed, rubric_score, triggering_accuracy)` where `gate_passed = (triggering_accuracy >= BASELINE_TRIGGERING)`. `BASELINE_TRIGGERING` is fixed once, from the original, and never moves during the run.

Comparison rule (lexicographic with a triggering tiebreaker): candidate A beats candidate B if any of these holds, in order:
1. A passes the gate and B does not.
2. Both pass and A's `rubric_score` is higher by more than 1 point.
3. Both pass, their `rubric_score` values are within 1 point of each other, and A has the higher `triggering_accuracy`.

A `crash` never beats anything. Rubric stays the primary driver: triggering accuracy only decides ties, so a strictly better-triggering candidate at equal quality is no longer discarded. This keeps the optimization a single comparable signal.

# Run the loop

1. **Baseline.** Score `$RUN_DIR/original`. Set `BASELINE_TRIGGERING` to its triggering accuracy. Copy it to `$RUN_DIR/best`. Record `best_rubric` and `best_triggering` from its score (the tiebreaker compares against both). Append the baseline row to the log with `lens` set to the reserved value `baseline`.
2. **Initialise** `dry = 0`, `iter = 0`.
3. **Each round, until `dry == 3` or `iter == 50`:**
   a. Generate 2 to 3 variations of the current `$RUN_DIR/best` by dispatching parallel proposer subagents, each with one distinct lens (a future iteration may expose this count as an argument; default 2 to 3, can be dialled to 1 for cheaper runs):
      - tighten the description and trigger guidance to raise triggering accuracy,
      - restructure the body for clarity and instruction-following,
      - cut bloat (improvement-by-deletion: shorter is better when quality holds).
      Each proposer returns a full candidate skill text. It must obey the writing rules (no em-dash, no double hyphen).
   b. Score each variation with the scorer.
   c. Pick the best variation by the comparison rule. If it beats `$RUN_DIR/best`, overwrite `$RUN_DIR/best` with it, update `best_rubric` and `best_triggering`, and set `dry = 0`. Otherwise discard all variations (keep the current best) and do `dry += 1`.
   d. For each variation scored this round, append one row to `$RUN_DIR/results.tsv`.
   e. `iter += 1`.

The 50-iteration cap is only a runaway backstop and is not expected to be reached; the intended stop is 3 dry rounds. The user may interrupt at any time; `$RUN_DIR/best` always holds the best version so far.

Log format (`$RUN_DIR/results.tsv`, tab-separated, one row per scored candidate):
`iter` TAB `lens` TAB `triggering_accuracy` TAB `gate_passed` TAB `rubric_score` TAB `kept|discarded|crash` TAB `one-line description`

# Report and write back

1. Present a run report to the user:
   - baseline vs best: triggering accuracy and rubric score, with deltas,
   - the diff of `$RUN_DIR/best` against `$RUN_DIR/original`,
   - the full per-iteration log from `$RUN_DIR/results.tsv`,
   - the frozen eval set used (`$RUN_DIR/eval.md`), so a future rerun could reuse it.
2. If `$RUN_DIR/best` is identical to `$RUN_DIR/original` (no improvement found), say so plainly and do not write anything. Stop.
3. Otherwise ask the user to confirm the write-back. Only after explicit confirmation:
   `cp "$RUN_DIR/best" "$SKILL_PATH"`
   This is the only moment the real skill file is touched.
4. Leave the scratch dir in place for the session (it holds the log and eval set); do not delete it automatically.
