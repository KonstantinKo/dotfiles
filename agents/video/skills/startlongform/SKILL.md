---
name: startlongform
description: "Start a long-form YouTube scripting session: refresher, develop an idea, critique a draft, refine, and save."
disable-model-invocation: true
argument-hint: "[optional topic, research, outline, or script]"
---

# /startlongform

A collaborative working session for one long-form YouTube video, especially educational or
substantive nonfiction. Read [longform-script](../longform-script/SKILL.md) first; it owns the
craft rules. Use the user's current message, supplied arguments and relevant conversation
context as input. Some harnesses supply command arguments as `$ARGUMENTS`.

## 1. Route
- **No topic, notes, research, outline or script supplied anywhere in the relevant context:**
  give the refresher in step 2, ask for a starting point, and stop until the user responds.
- **Topic, question or research supplied:** skip the unsolicited refresher; develop it in step 3.
- **Outline or script supplied:** skip the refresher; critique and refine in step 4. Use supplied
  audience, format, length and destination; infer and label any missing noncritical details.
- **Explicit request for a refresher:** give step 2 even when content is present, then continue
  the requested work if enough input is available.

A bare command or unexpanded argument placeholder counts as no content. A topic is enough
to start; the user does not need to bring a draft. Resume the active script on follow-ups.

## 2. Refresher
Keep it under about 25 lines. Give:
- The longform-script one-line model in plain language.
- A compact table: honest promise → viewer's question / starting knowledge → evidence and
  discoveries → final insight or useful result.
- Four reminders: concrete before abstract; payoffs before setups; words + visuals + sources;
  learning needs thinking time and factual checks.
- One freshly invented, explicitly hypothetical three-beat example showing a question,
  concrete evidence or demonstration, and an earned insight. Use a topic different from any
  examples already shown in the conversation. Label hypothetical results as unverified.
- If content is missing, ask: "What topic, question, notes, or draft should we work on?"
  Then stop. If the user requested a refresher alongside supplied content, continue to
  development or critique using that content.

## 3. Develop the idea
Produce a concise working brief: audience and assumed knowledge, central question, learning
or practical destination, distinct contribution, format and provisional length. State assumptions.
If the topic is broad, propose up to three specific angles and recommend one with a reason.
Ask at most one to three consequential questions together, using what's already known;
continue with useful work that does not depend on the answers.

Build a first proposal the user can react to:
- Up to three honest title + thumbnail concepts, with a recommended promise.
- The key visual, demonstration or evidence that makes this work as video.
- A payoff-first beat outline using the structure suited to this format, with estimated times,
  the question / setup and earned answer for each segment, and the ending.
- Research needed, contested claims and any missing evidence. Use supplied sources, and verify
  factual claims through available research tools; consult `yt-video` for video material.

With only a topic, offer the brief and outline before a full narration. Invite the user's
reaction to the most important unresolved angle. When the user requests a full script or the
session has established its direction, draft it without an additional approval gate.
For investigations and experiments, preserve a provisional conclusion until evidence supports it.

## 4. Critique and refine
Apply the longform-script evaluation checklist to each outline or draft.
1. Lead with the single biggest fix. Show at most five weak / failed items per round, each
   with the quoted line or missing beat and a concrete rewrite. Summarize passes in one line.
2. Check the promise, viewer starting point, destination, structure, payoffs, visuals and
   evidence. Identify relevant techniques in plain language; the user need not know rule numbers.
3. Offer up to three alternatives when an opening, angle or ending needs a real choice.
4. Collaborate at the requested level: focused suggestions when the user wants to write;
   rewrite or draft when asked. Develop partial notes rather than demanding a finished script.
5. Resolve material questions through research or user input. Keep unsupported claims marked;
   do not present inferred results, footage or interview quotes as already obtained.

For a complete draft, show the chosen title/thumbnail promise, timed beat outline, and a
`Time / Beat | Ears | Eyes | Evidence / Status` script table (or an agreed equivalent).
Include word count, estimated duration with pauses/demos, production needs and facts still
needing verification. Use a deliberate hybrid rather than full narration when it suits delivery.
Recommend an aloud rehearsal and, when practical, a small audience test. Distinguish
"structurally ready" from "fact-checked and ready to record" if evidence remains unresolved.

## 5. Save when requested or when the user approves saving
Honor an established destination. Otherwise use:
`~/projects/video/longform/<YYYY-MM-DD>-<slug>/` (slug: two to four topic words).
For a new project, add `-2`, `-3`, etc. if the folder exists; do not overwrite another project.
For an explicitly resumed project, update its files while preserving useful notes and alternatives.

- `script.md`: frontmatter with working title, `status: draft | ready`, estimated `length_min`
  and creation date; audience, starting knowledge, destination, format, promise and final
  insight; packaging options, beat outline and narration/visual/evidence table; production
  needs, alternative openings and estimated timing. `ready` requires material checks to pass.
- `sources.md`: claim IDs, exact claims, linked sources or calculations, claim type,
  qualifications / disagreement, verification status, and remaining research questions.
- `notes.md`: decisions, concise critique history, open questions and audience/rehearsal feedback
  when available. Record meaningful changes without discarding the user's original direction.

Print the saved path. Saving a script ends this workflow; production setup follows only when
requested. Standalone scripting does not require initializing a Backlot production or generating
media. Paid provider calls retain the video project's per-call approval requirements.
