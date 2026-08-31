---
name: html-communication
description: Create a self-contained HTML document for a plan, specification, report, comparison, findings, summary, or UI mock presentation. Use when the user asks to communicate through readable HTML; do not use for HTML that ships as product code.
---

# HTML Communication

Create one self-contained HTML file capped at 512 KB.

## Document

- Write it like a working document, not a landing page: dense, scannable, and
  free of hero sections, decorative chrome, or marketing voice.
- Default to true black (`#000`), white primary text, and dark gray secondary
  surfaces or accents unless the user requests another direction.
- Make it mobile-readable with a responsive viewport and fluid layout.
- Use semantic HTML, inline CSS, inline SVG, and HTTPS or data-URL images.
- Use a classic inline script only when interactivity materially improves the
  document. Keep scripted pages useful without JavaScript.
- If the document has no script, external links may use `target="_blank"` with
  `rel="noopener noreferrer"`. If any script exists, omit `target="_blank"`.

Never include external or module scripts, inline event handlers, `javascript:`
URLs, forms, frames, embeds, objects, applets, meta refresh, linked stylesheets,
secrets, private URLs, or local filesystem paths. The Postplan sandbox blocks
storage, network fetches, workers, frames, forms, and popups; do not design core
behavior around them.

## UI mock variants

When the user asks for variants:

- Render actual styled variants rather than prose descriptions.
- Label them `A`, `B`, `C`, and so on for easy selection.
- Lay them out for direct comparison.
- Keep one HTML file across iterations so its hosted draft URL can remain stable.

## Publish

When the request asks for a hosted, published, or shareable document:

1. Write the HTML locally at a stable absolute path outside the repository unless
   the user requests a tracked location.
2. Run `npx --yes postplan upload <absolute-path>`.
3. Return both the local path and the URL printed by Postplan.

Uploading the same absolute path updates its existing draft URL. Use `--new` only
when the user requests a separate draft. If Postplan reports missing credentials,
ask the user to run `npx postplan auth login`, then retry after they confirm.

If validation fails, fix the document and retry once. If the same failure
persists, report it rather than weakening requested functionality or repeatedly
mutating the remote draft. Never claim the document is hosted before upload
succeeds.

If visual correctness is part of the claim, render the local document with the
available collaborative browser and inspect it at representative desktop and
mobile widths before publishing.
