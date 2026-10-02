# Upstream source

Editable local copy; updates are manual.

- Repository: [mattpocock/skills](https://github.com/mattpocock/skills)
- Path: `skills/productivity/writing-for-agents`
- Imported revision: `d81f3a183412e71a5b1e84ca21bc1a35eea03a60`
- Imported on: 2026-10-02
- License: MIT; see [LICENSE](LICENSE).
- Source at import: [skill directory](https://github.com/mattpocock/skills/tree/d81f3a183412e71a5b1e84ca21bc1a35eea03a60/skills/productivity/writing-for-agents)
- Latest upstream: [skill directory](https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-for-agents)

## Local changes

`SKILL.md` adds a source pointer and a local integration note after frontmatter. The remaining skill and reference files match the imported revision. Preserve subsequent local changes when updating.

The integration note respects repository conventions, user authorization, and the active harness:

Preserve explicit safety and authorization rules when pruning instructions. Treat the invocation mechanics below as harness-specific: inspect the active harness's supported frontmatter before relying on discovery or tool behavior.

## Compare and update

Clone upstream into a temporary directory, fetch current `main`, and compare both the imported base and the latest files with this local folder. Run these from this skill directory, replacing `<upstream-checkout>` with that temporary clone:

```sh
git -C <upstream-checkout> fetch origin main
git -C <upstream-checkout> diff d81f3a183412e71a5b1e84ca21bc1a35eea03a60..origin/main -- skills/productivity/writing-for-agents
git -C <upstream-checkout> switch --detach d81f3a183412e71a5b1e84ca21bc1a35eea03a60
git diff --no-index -- <upstream-checkout>/skills/productivity/writing-for-agents .
```

The first comparison shows incoming upstream changes; the second shows local edits against the imported revision and includes local `LICENSE` and `UPSTREAM.md` additions. Merge desired changes into the local files; avoid overwriting the folder or using `rsync --delete`. Update the imported revision here and the source link in `SKILL.md` after merging. Retain the license and this pointer.
