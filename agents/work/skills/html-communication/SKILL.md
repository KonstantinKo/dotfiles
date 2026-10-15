---
name: html-communication
description: Use when the user asks to communicate through an HTML document/artifact; don't use for HTML that ships as product code.
---

# HTML Communication

Create a self-contained HTML document capped at 512 KiB. Write a dense,
scannable working document with a design that fits its topic and a responsive
viewport for mobile reading. Embed CSS, SVG, and image data in the file.

Use classic inline JavaScript when it materially improves the document, and
keep the content useful without it. The viewer sandbox blocks external
resources, network requests, storage, frames, forms, and popups. Omit external
scripts, module scripts, linked stylesheets, embeds, and inline event handlers.
Keep credentials, secrets, and unnecessary personal data out of the document.
Use ordinary HTTPS links for references with `rel="noopener noreferrer"`.

For UI variants, render styled alternatives labeled A, B, C for direct
comparison. Keep the same local file across iterations to preserve its URL.

## Publish

Konstantin has given standing permission to publish artifacts created or
updated with this skill to the company service, including in Auto mode.

1. Write the HTML at a stable absolute path outside the repository unless the
   user requests a tracked location.
2. Run `doartifacts publish <absolute-path>`. The default service is
   `https://artifacts.doinstruct.dev`; use this company service for work artifacts.
3. Return the local path and the URL reported by the successful upload.

Re-publish the same absolute path to update the existing artifact. Artifacts
expire after 14 days without authenticated viewing or updating.

If authentication is required, run `doartifacts login`, let the user approve
the matching code in their own company browser, then retry. If initiating login
is unavailable, ask the user to run that command. Colleagues need neither
Cloudflare tooling nor a Cloudflare account. If the CLI or authentication is unavailable, keep the
file local and report the blocked publication with the next command needed;
never switch to another publishing service or claim an upload succeeded.

Fix reported HTML validation errors and retry while preserving requested
interactivity. When visual verification is requested, render locally with the
available collaborative browser and inspect desktop and mobile widths.
