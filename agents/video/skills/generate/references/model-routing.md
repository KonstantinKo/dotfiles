# Model routing

Source of truth: `Studio/Models/<id>.md` frontmatter and body. `backlot models --kind <k>` lists what is `active`. Never route to `untested` or `disabled` without telling the user.

## Filter, then rank
1. Filter by `kind` (image, video, tts, music, sfx, upscale, stt, lipsync).
2. Filter by `inputs`: image-to-video needs `image`; lipsync needs `video` and `audio`; reference boards need `image` on an image model.
3. Filter by `max_duration_s` >= shot duration and `resolutions` containing the project resolution (or one the render can scale from without upscaling more than 1.5x).
4. Filter by `tier` against lock state:
   - `lite`: options, exploration, unlocked elements, motion tests.
   - `pro`: final pass on shots whose `depends_on` are all locked.
   - `ultra`: hero shots named in `Rules.md`, or on explicit user request.
5. Rank remaining by the strengths section of the model note against the shot's needs (faces, hands, text, fast motion, camera control, long takes, style adherence). Prefer the provider named in `Rules.md`; `comfyui-local` costs nothing but needs Desktop running (`backlot doctor`).

## Cost
`cost_eur` per `cost_unit`. Per second video: seconds x cost. Per image: n x cost. Per 1k chars: ceil(chars/1000) x cost. `backlot gen --dry-run` gives the number; quote that, never your own arithmetic, when asking.

## Params
`defaults {}` in the model note are applied by the CLI. Override with `--param k=v` only for keys the note lists. Duration and fps always go in params.

## Fallback order
Record the chosen model and the runner-up in the shot note under `## Routing`. On two failures, switch to the runner-up. On provider errors, run `backlot doctor` before retrying.
