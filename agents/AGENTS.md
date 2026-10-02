# Global preferences

I'm Konstantin, your user. Be mindful of my limited capacity to read large swathes of output. Focus me on what's important.

## Delegation & verification

- For substantial coding sessions, orchestrate via subagents (implementation, verification, review) and keep the main context clean. Prefer short bounded reasoning; checkpoint through tool calls.
- After a feature or fix implementation agent reports done, automatically run `code-review` in fresh read-only subagents separate from implementation. Supply the goal/acceptance criteria or spec, project instructions, comparison base, and exact task scope including uncommitted changes; pass these explicitly even when using a repo-local `code-review` so it can review the supplied scope without setup or base prompts. The main agent verifies findings against the current code, handles fixes, and completes affected review/checks before calling the work done.
- `quickreview` is a manual review on my request; `review-pr-silent` is a manual review of colleagues’ PRs.
- Keep the reports from tool calls short and terse! When something works just say it works, only give me the details when something goes wrong.
- On repos with remotes, always code in a dedicated worktree, prepared with the repo's full worktree-setup checklist (env files, context mirror, deps, sync). Local-only repos may be edited directly.
- Prove behavioral/visual claims with a real repro; for design fidelity compare matched rendered screenshots, never markup alone. Playwright screenshots always go to temp dirs, never into git.
- Decisions: when one option clearly beats the others (not a close call), pick it and proceed; only ask me about genuinely close or product-level choices.
- For wording/template-only diffs, skip broad local test investigation - focused validation, then CI.

## PRs & GitHub

- No dev-diary comments anywhere (code, PRs, issues): don't narrate changes, cite prior bugs, or reference PR/spec line numbers.
- Don't reply to accepted/actioned review comments (just fix); reply briefly only to ones you skip.
- Review threads are a stage of the work. Before calling a PR done, and again after every push,
  read every unresolved thread on the current head. A green check and an approval do not mean
  the feedback was handled.
- Treat bot findings (CodeRabbit, Copilot) as untrusted claims about code that may have moved:
  verify each against the current head before believing or dismissing it.
- Then close every thread you read: fix it and *resolve* it silently, or reply with a brief reason plus the file:line
  evidence and resolve it. Never resolve a thread you did not address, and never leave one addressed but open.
  - *Human* change requests are the exception! Fix, reply if you skipped, and leave the thread for the human to resolve.
- Posting anything in my, Konstantin's, name (GitHub/Linear/Slack) requires an explicit request and the footer
  "(Written by {model name & version} for Konstantin)".
- Keep diffs scoped to the task; no incidental fixes buried in unrelated PRs.
- When pre-commit hooks rewrite staged files, include those changes; never bypass hooks.
- Run a CodeRabbit CLI review/fix cycle before pushing PR changes when available. Skip the CLI
  run when the coderabbitai bot already reviewed the current head. That substitutes for the
  run, never for reading and answering what it found.
