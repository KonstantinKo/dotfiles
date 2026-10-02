# Upstream source

Editable local copy; updates are manual.

- Repository: [mattpocock/skills](https://github.com/mattpocock/skills)
- Path: `skills/engineering/codebase-design`
- Imported revision: `d81f3a183412e71a5b1e84ca21bc1a35eea03a60`
- Imported on: 2026-10-02
- License: MIT; see [LICENSE](LICENSE).
- Source at import: [skill directory](https://github.com/mattpocock/skills/tree/d81f3a183412e71a5b1e84ca21bc1a35eea03a60/skills/engineering/codebase-design)
- Latest upstream: [skill directory](https://github.com/mattpocock/skills/tree/main/skills/engineering/codebase-design)

## Local changes

`SKILL.md` adds a source pointer and a local integration note after frontmatter. The remaining skill and reference files match the imported revision. Preserve subsequent local changes when updating.

The integration note respects repository conventions, user authorization, and the active harness:

Use this vocabulary for architecture discussions while preserving the project's established domain and framework terms. Follow `docs/agents/domain.md` for glossary paths. Interpret the design principles as heuristics subordinate to documented project standards.

## Compare and update

Clone upstream into a temporary directory, fetch current `main`, and compare both the imported base and the latest files with this local folder. Run these from this skill directory, replacing `<upstream-checkout>` with that temporary clone:

```sh
git -C <upstream-checkout> fetch origin main
git -C <upstream-checkout> diff d81f3a183412e71a5b1e84ca21bc1a35eea03a60..origin/main -- skills/engineering/codebase-design
git -C <upstream-checkout> switch --detach d81f3a183412e71a5b1e84ca21bc1a35eea03a60
git diff --no-index -- <upstream-checkout>/skills/engineering/codebase-design .
```

The first comparison shows incoming upstream changes; the second shows local edits against the imported revision and includes local `LICENSE` and `UPSTREAM.md` additions. Merge desired changes into the local files; avoid overwriting the folder or using `rsync --delete`. Update the imported revision here and the source link in `SKILL.md` after merging. Retain the license and this pointer.
