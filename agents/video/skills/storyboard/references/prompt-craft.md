# Prompt craft for boards and video

One prompt describes one frame (image) or one continuous motion (video). Build it in this order and keep every element traceable to a Context note.

## Order
1. Subject: who or what, pulled verbatim from the Cast or Prop note (age, build, hair, wardrobe, defining detail). One subject per clause.
2. Action: a single verb phrase in present tense. Video: what changes across the clip, start state to end state.
3. Setting: from the Location note (place, time of day, weather, key props in frame).
4. Camera: shot size (ECU, CU, MCU, MS, WS, EWS), angle (eye level, low, high, top), movement (static, slow push in, pan left, handheld, tracking).
5. Lens: focal length and aperture feel (35mm, 85mm, shallow depth of field, deep focus).
6. Lighting: source, direction, quality, colour (soft window light from left, warm practicals, overcast, hard noon sun).
7. Style: fragments from `Visual Language.md` (film stock, grain, palette, contrast, era). Do not restate the whole note; reuse its prompt fragments verbatim so shots match.
8. Negative: from `Visual Language.md` negatives plus shot specifics (no text, no logos, no extra people, no watermark).

## Rules
- One sentence per element, comma separated, no adjectives that are not in a Context note.
- Keep cast descriptions identical across shots; consistency comes from repetition and from passing `locked_take` as `--image` when the model accepts a reference.
- For video, put the motion in the action and the camera; the still is already given by the board. Avoid describing what the board already shows.
- Duration and fps go in `--param`, never in the prompt.
- Write the prompt into the shot note before generating, so the take's `prompt` and the note agree.

## Video prompt from a board
`<action across the clip>, <camera movement>, <what must stay fixed: wardrobe, framing, light>, <pace: slow, natural, brisk>`
Example: "she lifts the cup and looks out of the window, slow push in, wardrobe and window light unchanged, natural pace".

## Variation deltas
State only what changes: "same, wider, 24mm" or "same, golden hour instead of overcast". Pass `--parent <take>` so the ID reads `img-014.2`.
