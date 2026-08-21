# Konstantin's private project context (gitignored)

## Working rules (formerly auto-memory)

- **Translations:** `apps/app`/`apps/manager` → edit English locale files ONLY (Crowdin owns the rest). `apps/lesson-editor` → update EVERY `messages/*.json` catalog (en + de), catalog parity is tested.
- **Variants (lesson-editor variation engine):** variants are real, promotable, production-grade candidates — full i18n, both themes, tests; never dev-only demos. Variant ids/labels describe the UI change itself; internal parity/process vocabulary ("current", "edge", export dates) never enters the shared switcher. Promoting an existing variant needs no new ADR/Decision Note.
- **Integration tests:** run from repo root via `bun run [app]:test:integration -- -- --grep "name"`.
- **Permissions work:** check Resource/Action, never role names (custom roles exist). Permissions doctrine SSOT: `~/projects/platform-permissions`.
- **graphify code-map:** build code-only (`.graphifyignore` non-code, else LLM-key error); `explain`/`path` are exact, `query` noisy.

## Content Studio / Video Studio — source of truth

The single source of truth for the Content Studio / Video Studio effort (`apps/lesson-editor`) is the Obsidian folder:

`~/projects/obsidian/agentdesk/content-studio/`

- Start at `BRAIN.md` (project identity, status, source map, people, workstreams).
- Design sources live in `sources/claude-design/` — the newest dated design digest there is the design SOT; older ones are historical.
- Design-vs-code parity state lives in `design-parity/` (gap analysis, variant work packages, handoff briefs).
- Workstream briefs + variation-engine handoff live in `workstreams/`.

When working on lesson-editor design parity, variants, or gap analyses: read `BRAIN.md` and the latest parity ledger first, and write updates back there (not into repo docs, which are team-shared).
