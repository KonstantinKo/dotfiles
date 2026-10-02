---
name: shortstart
description: "Start a YouTube Short scripting session: refresher, critique, refine, save. Use when the user runs /shortstart."
disable-model-invocation: true
argument-hint: "[optional topic or draft outline]"
---

# /shortstart

A working session for one YouTube Short. The craft rules live in the `shorts-script` skill;
read its SKILL.md first (@../shorts-script/SKILL.md) and judge everything against it.

Input:

```
$ARGUMENTS
```

## 1. Route
- **Empty, or only a vague topic** → step 2, then ask for the draft.
- **Contains a draft or outline** (a hook, beats, or script lines) → skip step 2, go to step 3.

## 2. Refresher (keep it under ~25 lines)
Print:
- The one-line model: last line first, a 1-second hook that promises it, beats linked by
  "but / so", cut when the payoff lands.
- The skeleton as a 4-row table: Hook (0–3 s) · Foreshadow (to ~7 s) · Narrative (but/so
  beats) · Twist (last 2–4 s, then hard cut).
- Five hook rules in one line each: works on mute, payoff in frame 1, 5–10 words, no greeting,
  one unexpected change to something familiar.
- **A freshly invented example** as a `Time | Beat | Line | Shot` table (~30–40 s). Pick a
  random niche each run (cooking, tech tip, history fact, travel, fitness, science, money,
  craft, language, nature...). Never reuse examples from the skill or earlier sessions.
- Then ask: "Your topic or draft?" and stop.

## 3. Critique loop
For each draft the user gives:
1. Run the `shorts-script` evaluation checklist. Show only the items that are weak or fail,
   each with the quoted line and a concrete rewrite. One line for everything that passes.
2. Lead with the single biggest fix. At most five issues per round; save the rest.
3. If the ending is unclear, ask for it before anything else: no ending, no Short.
4. Offer up to three alternative hooks from different hook families when the hook is weak.
5. Let the user rewrite; don't take over the draft unless asked. When every checklist item
   passes, say it's ready and show the full script as a `Time | Beat | Line | Shot` table
   with word count and estimated length (≈2.5–3 words/s).

Remember the user has no reference to the details of this brief or the shorts-script skill.
Their only reference is their knowledge and what you've already output earlier in the
conversation. Thus do not only reference rule numbers, the user has no mental map which number
corresponds to what.

## 4. Save (when the user approves, or asks to save)
Folder: `~/projects/video/shorts/<YYYY-MM-DD>-<slug>/` (slug: 2–4 words from the topic).
Create it if missing; never overwrite an existing folder, add `-2` (and increasing) instead.

- `script.md`
  ```
  ---
  title: <working title>
  status: draft | ready | shot | published
  length_s: <estimate>
  created: <YYYY-MM-DD>
  ---
  # <working title>
  **Six words:** … · **Ending:** … · **Hook family:** …

  | Time | Beat | Line | Shot |
  |---|---|---|---|

  ## Alternative hooks
  ## Shot and prop list
  ```
- `notes.md`: the critique rounds in brief (what changed and why), open questions, ideas to
  test (e.g. which hook to try first).

Print the folder path and stop.
