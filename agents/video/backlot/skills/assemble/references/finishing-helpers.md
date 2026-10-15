# Finishing helpers

Use the score helpers only for a selected score change to an accepted picture. They bind the work to the cut bytes, measured frame rate and frame count, and an explicit picture or title-end time origin. See [`finishing-checks.md`](../../studio/references/finishing-checks.md) for listening and visual review requirements.

## Score plan and mix

`backlot score-plan <spec.json>` validates a plan without writing media. `backlot score-mix <spec.json>` writes the requested output path. The CLI resolves relative paths from the active project folder.

```json
{
  "cut": "renders/accepted-picture.mp4",
  "score": "inputs/score.wav",
  "output": "renders/accepted-picture-scored.mp4",
  "title_end_boundary": 72,
  "gain_db": -8.0,
  "cue_plan": {
    "cut_sha256": "<64 lowercase hexadecimal characters>",
    "fps": "24/1",
    "frame_count": 240,
    "time_origin": {"kind": "title_end", "frame_boundary": 72},
    "cues": [
      {"id": "first cue", "start_frame": 0, "end_frame": 24}
    ]
  }
}
```

`title_end_boundary` is the number of picture frames before score begins. Cue intervals use integer, half-open frame ranges: `[start_frame, end_frame)`. A `picture_start` origin uses absolute frame positions and must declare boundary `0`; a `title_end` origin uses positions relative to `title_end_boundary`. Every cue plan must match the cut hash, measured FPS and frame count, and each cue must fit after the title boundary and within the cut. The helper measures the selected score stream's decoded samples to report actual duration, then trims or pads the score layer to the remaining picture length.

Supply `gain_db` explicitly. A file with one audio stream selects that stream automatically; if the score has multiple audio streams, set `score_stream` to the desired zero-based audio ordinal. Every audio stream in the accepted cut is included in the mix. The output has one AAC audio stream, so original tracks are no longer addressable as separate stems. The helper re-encodes audio, stream-copies video, and checks the video packet hashes and timing against the accepted cut. It reports the listening review as not performed; a clean technical check does not establish that the score sounds right.

The output path must be new. Keep the returned SHA-256 and picture identity with the scored variant. A score plan is invalidated by any byte change to either input.

## Archive manifest and bundle

The CLI supports `backlot archive create <spec.json>`, `backlot archive check <manifest.json>`, and `backlot archive bundle <manifest.json> <new-directory>`.

```json
{
  "manifest_path": "renders/archive-manifest.json",
  "files": [
    {"source": "renders/accepted-picture.mp4", "path": "sources/picture.mp4", "role": "accepted picture"},
    {"source": "inputs/score.wav", "path": "sources/score.wav", "role": "score source"},
    {"source": "edit/score-plan.json", "path": "recipes/score-plan.json", "role": "recipe input"},
    {"source": "renders/scored.mp4", "path": "outputs/scored.mp4", "role": "scored output"}
  ],
  "recipe": {
    "kind": "backlot.finishing.mix_score",
    "inputs": {"cut": "sources/picture.mp4", "score": "sources/score.wav"},
    "extras": ["recipes/score-plan.json"],
    "outputs": ["outputs/scored.mp4"]
  }
}
```

Each `source` is hashed when the manifest is created. `path` is a safe, normalized, archive-relative member name; the optional `sha256` must match the source. Declare every selected source, recipe input, recipe extra, and output in `files`, then bind it by its `path` under `recipe`. The helper checks exact SHA-256 and byte size, and reports missing or changed files. Manifest creation and checking do not copy media or prove that a backup exists.

`archive bundle` copies the declared files into a fresh directory and writes a new bundle-local manifest. It rejects an existing destination, unsafe member paths, missing inputs, and changed inputs. It does not execute commands stored in a recipe. `bundle_files_verified` means the copied members match the manifest; `backup_verified` and `reproduction_verified` remain false until separate recovery and recipe-run checks are actually performed. Keep original master identity and share-link expiry in their deliverable records; a bundle or expired share link does not change the master hash.
