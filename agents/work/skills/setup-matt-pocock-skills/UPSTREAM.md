# Upstream source

Editable local copy; updates are manual.

- Repository: [mattpocock/skills](https://github.com/mattpocock/skills)
- Path: `skills/engineering/setup-matt-pocock-skills`
- Imported revision: `d81f3a183412e71a5b1e84ca21bc1a35eea03a60`
- Imported on: 2026-10-02
- License: MIT; see [LICENSE](LICENSE).
- Source at import: [skill directory](https://github.com/mattpocock/skills/tree/d81f3a183412e71a5b1e84ca21bc1a35eea03a60/skills/engineering/setup-matt-pocock-skills)
- Latest upstream: [skill directory](https://github.com/mattpocock/skills/tree/main/skills/engineering/setup-matt-pocock-skills)

## Local changes

`SKILL.md` adds a source pointer and a local integration note after frontmatter. The remaining skill and reference files match the imported revision. Preserve subsequent local changes when updating.

The integration note respects repository conventions, user authorization, and the active harness:

Reuse existing `docs/agents/` configuration and the established issue tracker and domain layout. When `CLAUDE.md` imports or links to `AGENTS.md`, edit the canonical `AGENTS.md` rather than expanding the shim. Preserve project-specific layouts such as `CONTEXT.md` and `docs/decisions/`. Installing this skill does not run setup or authorize tracker writes.

## Compare and update

Clone upstream into a temporary directory, fetch current `main`, and compare both the imported base and the latest files with this local folder. Run these from this skill directory, replacing `<upstream-checkout>` with that temporary clone:

```sh
git -C <upstream-checkout> fetch origin main
git -C <upstream-checkout> diff d81f3a183412e71a5b1e84ca21bc1a35eea03a60..origin/main -- skills/engineering/setup-matt-pocock-skills
git -C <upstream-checkout> switch --detach d81f3a183412e71a5b1e84ca21bc1a35eea03a60
git diff --no-index -- <upstream-checkout>/skills/engineering/setup-matt-pocock-skills .
```

The first comparison shows incoming upstream changes; the second shows local edits against the imported revision and includes local `LICENSE` and `UPSTREAM.md` additions. Merge desired changes into the local files; avoid overwriting the folder or using `rsync --delete`. Update the imported revision here and the source link in `SKILL.md` after merging. Retain the license and this pointer.
