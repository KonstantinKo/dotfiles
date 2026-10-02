# Upstream source

Editable local copy; updates are manual.

- Repository: [mattpocock/skills](https://github.com/mattpocock/skills)
- Path: `skills/engineering/pr`
- Imported revision: `d81f3a183412e71a5b1e84ca21bc1a35eea03a60`
- Imported on: 2026-10-02
- License: MIT; see [LICENSE](LICENSE).
- Source at import: [skill directory](https://github.com/mattpocock/skills/tree/d81f3a183412e71a5b1e84ca21bc1a35eea03a60/skills/engineering/pr)
- Latest upstream: [skill directory](https://github.com/mattpocock/skills/tree/main/skills/engineering/pr)

## Local changes

`SKILL.md` adds a source pointer and a local integration note after frontmatter. The body also makes the repository template authoritative and limits the displayed template to a fallback. Other imported files match the imported revision. Preserve subsequent local changes when updating.

The integration note respects repository conventions, user authorization, and the active harness:

Use the repository PR template and explicit user requirements before this fallback template. External posts require explicit session authorization and the prescribed attribution footer. Writing a body alone does not authorize publication; existing authorization remains valid.

## Compare and update

Clone upstream into a temporary directory, fetch current `main`, and compare both the imported base and the latest files with this local folder. Run these from this skill directory, replacing `<upstream-checkout>` with that temporary clone:

```sh
git -C <upstream-checkout> fetch origin main
git -C <upstream-checkout> diff d81f3a183412e71a5b1e84ca21bc1a35eea03a60..origin/main -- skills/engineering/pr
git -C <upstream-checkout> switch --detach d81f3a183412e71a5b1e84ca21bc1a35eea03a60
git diff --no-index -- <upstream-checkout>/skills/engineering/pr .
```

The first comparison shows incoming upstream changes; the second shows local edits against the imported revision and includes local `LICENSE` and `UPSTREAM.md` additions. Merge desired changes into the local files; avoid overwriting the folder or using `rsync --delete`. Update the imported revision here and the source link in `SKILL.md` after merging. Retain the license and this pointer.
