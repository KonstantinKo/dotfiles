# Timeline, media, and render operations

The installed `DaVinciResolveScript.pyi` is the method/signature reference. API objects are handles; API methods commonly return `bool`, a handle/list, or `nil` on failure. Check what each documented call returns before continuing.

## Frame coordinates

Keep timeline position, source-media position, timecode, and Fusion composition time distinct. `Timeline.GetStartFrame()` and `GetEndFrame()` report the timeline's frame bounds. `TimelineItem.GetStart()` and `GetEnd()` are positions on the edit timeline; `GetSourceStartFrame()` and `GetSourceEndFrame()` describe positions from the source clip. They are different coordinate spaces. Do not subtract the timeline start or treat a timeline position as a Fusion-local frame unless the specific API documents that conversion.

Read `Timeline.GetSettings()` first for `timelineFrameRate`; a timeline may have custom settings that override the project rate. If that value is absent, fall back to `Project.GetSettings()`. The documented value may be fractional (for example, `23.976`); the accepted setting can be a string such as `"29.97 DF"`. Preserve the actual rate and drop-frame convention. Use integer frame indices for frame-addressed edits, and enable subframe precision only when the task needs it and the target method supports it.

## Media and timeline inspection

Confirmed APIs include `Project.GetMediaPool()`, `Project.GetCurrentTimeline()`, `Timeline.GetTrackCount()`, `Timeline.GetItemListInTrack()`, `TimelineItem.GetUniqueId()`, `TimelineItem.GetMediaPoolItem()`, and `MediaPoolItem.GetUniqueId()`. Use these to inventory a narrowly scoped target before editing. `MediaPool.AppendToTimeline()` appends the supplied media-pool items and returns created timeline items; its argument is a list of dictionaries in Lua table form. Use the exact documented keys for the installed version rather than guessing them from prose or a different release.

The Lua API represents Python-style lists as one-based indexed tables and dictionaries as key-value tables. Build each input table according to the exact signature. For example, the installed official Lua example uses `{ mediaPoolItem = clip, startFrame = 0, endFrame = 23 }` inside the list passed to `AppendToTimeline`.

## Render completion and review

The documented project calls include `SetRenderSettings()`, `AddRenderJob()`, `StartRendering()`, `IsRenderingInProgress()`, `GetRenderJobList()`, and `GetRenderJobStatus(jobId)`. Preserve the returned job ID and inspect its status for completion or failure. A false `IsRenderingInProgress()` only says no render is currently active; it does not establish that a particular job succeeded.

After completion, confirm the expected output exists, is non-empty and decodes, and check its dimensions, frame rate, duration, and audio when relevant. Review actual rendered frames or the image itself before claiming a visual result is correct. If the output cannot be inspected, say that delivery is unverified visually; do not equate a queued job, successful API return, or file handoff with a reviewed render.
