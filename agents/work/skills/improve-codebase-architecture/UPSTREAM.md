# Upstream source

Editable local copy; updates are manual.

- Repository: [mattpocock/skills](https://github.com/mattpocock/skills)
- Path: `skills/engineering/improve-codebase-architecture`
- Imported revision: `d81f3a183412e71a5b1e84ca21bc1a35eea03a60`
- Imported on: 2026-10-02
- License: MIT; see [LICENSE](LICENSE).
- Source at import: [skill directory](https://github.com/mattpocock/skills/tree/d81f3a183412e71a5b1e84ca21bc1a35eea03a60/skills/engineering/improve-codebase-architecture)
- Latest upstream: [skill directory](https://github.com/mattpocock/skills/tree/main/skills/engineering/improve-codebase-architecture)

## Local changes

`SKILL.md` adds a source pointer and a local integration note after frontmatter. The remaining skill and reference files match the imported revision. Preserve subsequent local changes when updating.

The integration note respects repository conventions, user authorization, and the active harness:

Read `docs/agents/domain.md` when present and use its glossary and ADR locations instead of the defaults below. Follow the repo-specific architecture skill when one exists. Build the local HTML report with inline CSS/SVG instead of CDN assets. Keep it local unless the user requests publication; when they request the `html-communication` publishing workflow, follow that skill's publishing requirements. Use the active harness preview tools for browser inspection.

## Compare and update

Clone upstream into a temporary directory, fetch current `main`, and compare both the imported base and the latest files with this local folder. Run these from this skill directory, replacing `<upstream-checkout>` with that temporary clone:

```sh
git -C <upstream-checkout> fetch origin main
git -C <upstream-checkout> diff d81f3a183412e71a5b1e84ca21bc1a35eea03a60..origin/main -- skills/engineering/improve-codebase-architecture
git -C <upstream-checkout> switch --detach d81f3a183412e71a5b1e84ca21bc1a35eea03a60
git diff --no-index -- <upstream-checkout>/skills/engineering/improve-codebase-architecture .
```

The first comparison shows incoming upstream changes; the second shows local edits against the imported revision and includes local `LICENSE` and `UPSTREAM.md` additions. Merge desired changes into the local files; avoid overwriting the folder or using `rsync --delete`. Update the imported revision here and the source link in `SKILL.md` after merging. Retain the license and this pointer.
