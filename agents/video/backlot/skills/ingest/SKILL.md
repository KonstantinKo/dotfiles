---
name: ingest
description: Ingest source material into a Backlot project's Context: PDF, deck, URL, footage or reference images become Knowledge.md, Inspiration.md with intent, and cast or location candidates. Use for "here's the deck", "read this PDF", "use this URL as reference", "I dropped footage in inputs", "add these references".
---

# Ingest

## Purpose
Get facts and references out of user material and into Context notes the crew can cite, with intent stated for every reference.

## Inputs
- Files in `~/projects/video/backlot/<slug>/inputs/` or paths the user gives; URLs
- `Projects/<slug>/Context/Knowledge.md`, `Context/Inspiration.md` (append, newest section on top)
- `Brief.md` for what matters

## Tools (all local)
- PDF, DOCX, PPTX: `~/.local/bin/marker_single <file> --output_dir /tmp/backlot-ingest/<slug>` (Markdown plus images), or `~/.local/bin/docling <file> --to md`.
- URL: `~/.local/bin/trafilatura -u "<url>" --markdown`.
- Video URL: `yt-dlp -f "bv*[height<=720]+ba/b" -o "inputs/%(title)s.%(ext)s" "<url>"`, then treat as footage.
- Footage: `ffprobe` for length and format; `ffmpeg -i <file> -vf "fps=1/5,scale=512:-1" /tmp/backlot-ingest/<slug>/<name>-%03d.jpg` for frame grabs; view the grabs.
- Images: view directly.

## Steps
1. Copy user files into `inputs/` if they are elsewhere. Note the source path and date.
2. Extract with the tool for the type. Read the Markdown; skim the frame grabs.
3. Knowledge: append to `Context/Knowledge.md` a section per source: source line (file or URL, date), then facts as short bullets the script may use (names, numbers, claims, product details, legal wording). Quote exact wording for claims. Mark contradictions between sources.
4. Inspiration: append to `Context/Inspiration.md` a section per reference with a thumbnail (copy to `_thumbs/ref-<n>.jpg`, under 256 px) and an intent line: what to take from it (lighting, palette, pace, framing, wardrobe) and what to ignore. Ask the user for the intent when it is not obvious; a reference without intent is not usable.
5. Candidates: people, places or objects that recur in the material become draft notes `Context/Cast|Locations|Props/<Name>.md` with `locked: false` and a `## From sources` section citing where they appear. Do not generate anything.
6. Footage the user wants to use as-is: list it in `Knowledge.md` under `## Supplied footage` with path, length and frame grabs. The timeline references the file path directly; it is not a take.
7. Report: sources ingested, facts count, references with intent, candidate notes created, open questions.

## Outputs
- `Context/Knowledge.md`, `Context/Inspiration.md`, `_thumbs/ref-*.jpg`
- Draft Cast, Location, Prop notes

## Gate
None. The user confirms intents when asked.

## Example phrases
- "here's the product deck, pull out what matters"
- "use this article as the factual basis"
- "I put the old commercial in inputs, grab the look"
