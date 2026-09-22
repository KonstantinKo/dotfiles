---
name: html-communication
description: Use when the user asks to communicate through an HTML document; don't use for HTML that ships as product code.
---

# HTML Communication

## Document

Create one self-contained HTML file capped at 512 KB.

- Write it like a working document, not a landing page: dense, scannable; 
  no: hero, decorative chrome, or marketing voice.
- Create a design that fits the topic.
- Make it mobile-readable with a responsive viewport and fluid layout.
- Use semantic HTML, inline CSS, inline SVG, and HTTPS or data-URL images.
- Use a classic inline script only when interactivity materially improves the
  document. Keep scripted pages useful without JavaScript; the sandbox blocks
  storage, fetch, workers, frames, forms, and popups.
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

Konstantin has given standing permission to upload every artifact created or updated
with this skill. Upload is required, including in Auto mode. Do not ask for
separate permission or stop at the local file.

1. Write the HTML locally at a stable absolute path outside the repository unless
   the user requests a tracked location.
2. Run `npx --yes postplan whoami` to verify the stored API key before publishing.
3. Run `npx --yes postplan upload <absolute-path>`.
4. Return both the local path and the URL printed by Postplan.

Re-upload the same absolute path to update the existing URL. Use 
`postplan upload <absolute-path> --new` only when a new draft is wanted.

If validation fails, fix the document and retry. If a script upload needs
authentication, ask the user to run `npx postplan auth login`, then retry without
removing rhe requested interactivity.

Never open a browser or claim the document is hosted before upload succeeds.
If visual correctness is part of the claim, render the local document with the
available collaborative browser and inspect it at representative desktop and
mobile widths before publishing. But do not verify in a browser unless the user
asks.
