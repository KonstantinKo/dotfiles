---
name: file-upload
description: When user asks to upload a file, or one is needed for PR descriptions, use this skill.
---

# File upload

Upload files with `scripts/upload-r2.sh`. The destination is public and intended
for durable links, so upload only when the request implies public sharing. If the
file may contain secrets, personal data, or other non-public material, stop and
ask before uploading it.

## Upload

```bash
"<skill-directory>/scripts/upload-r2.sh" [--temporary|--durable] <path-to-file>
```

The script prints the public URL and nothing else on success. It slugifies the
basename and adds a timestamp plus random suffix, so callers do not need to
invent a unique filename.

- `--temporary` is the default. Objects expire after 14 days. Use it for ad hoc
  sharing, review drafts, and single-use artifacts.
- `--durable` has no automatic expiry. Use it for PRs, issues, documentation, or
  any link that should remain valid as history.

The checked-in defaults target Konstantin's dedicated public artifact bucket.
`R2_BUCKET` and `FILE_PUBLIC_BASE_URL` can override them for another account.
Read [references/r2-setup.md](references/r2-setup.md) only when helping configure
or replace the host. Wrangler must be authenticated; on an authentication
failure, report it and do not retry unchanged credentials.

## Use the URL in GitHub

- Embed images (`png`, `jpg`, `jpeg`, `gif`, `webp`) as
  `![description](URL)`.
- Link videos (`mp4`, `mov`, `webm`) as `[🎥 screen recording](URL)` because
  GitHub does not reliably inline-play externally hosted video.
- When an inline preview materially helps and a clip is roughly 30 seconds or
  shorter, create a GIF in a temporary directory, upload it, then embed the GIF
  above the full-quality video link:

  ```bash
  ffmpeg -i recording.mp4 -vf "fps=10,scale=800:-1:flags=lanczos" -loop 0 preview.gif
  ```

Do not add generated previews to the repository.
