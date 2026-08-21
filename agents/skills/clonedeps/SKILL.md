---
name: clonedeps
description: Clone selected dependency source into ignored local workspace for implementation-level inspection. Use only when docs or installed package are insufficient for active task.
---

# Clone Dependency Source

Use only when source internals materially help active debugging, integration, or
framework work. Prefer docs, installed package code, and native OpenCode references
when sufficient. Keep recommendations small: usually zero to three repositories.

## Workflow

1. Identify exact dependency and resolved version from lockfile/installed package.
2. Resolve official source repository and matching tag/commit.
3. Explain why source is needed; skip clones that add no task value.
4. Verify ref with `git ls-remote` where practical.
5. Ask before network cloning unless user already requested clone.
6. Clone read-only source under:

```text
.agent-deps/repos/<owner>__<repo>/
```

7. Add `.agent-deps/` to `git rev-parse --git-path info/exclude` when needed.
   Never edit tracked ignore files or AGENTS.md solely for local clones.
8. Use shallow clone/fetch where practical. Do not initialize submodules unless
   active task requires them.
9. Do not run dependency install, build, test, hook, or repository scripts from
   cloned source.

Reject `file://`, embedded credentials, unexpected SSH remotes, or private repos
unless user explicitly approves. Verify existing clone remote before reuse.

Optional ignored `.agent-deps/manifest.json` may record repo, ref, package path,
and reason. Git checkout remains source of truth; do not commit manifest by default.

## Cleanup

When source is no longer useful, remove relevant clone after confirming no local
changes need preservation. Remove empty local manifest entries. Leave project files
untouched.
