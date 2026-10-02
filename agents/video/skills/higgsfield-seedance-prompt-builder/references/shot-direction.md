# Shot direction for video prompts

Adapted from the user-supplied [CINEDANCE v4.4.2 guide](original-v4.4.2.md). These are filmmaking heuristics. Keep the selected model skill's prompt budget, reference syntax, motion-control rules and endpoint settings. Use only the points that improve the current shot; do not turn this into extra boilerplate in every prompt.

## Decide what must read

Give each shot a dominant purpose: performance, spatial continuity, impact, suspense, atmosphere, detail or a requested camera device. Fit its events into the available duration, including the ending or hold. Simplify secondary detail when it competes with the main beat. Preserve explicit requirements; explain material tradeoffs rather than silently replacing them.

## Establish visible space

Define the intended opening and ending. Respect a supplied first-frame image and deliberate entrances, empty openings or reveals. For complex blocking, state physical relationships before optional screen coordinates: who stands where, body orientation, gaze, camera side, foreground/background anchors and contact with props or ground. Torso direction and gaze can differ. Keep eyelines and screen direction coherent across cuts unless the requested staging calls for a change.

Use only active, attached references with the endpoint's actual tags. Assign each reference a role and exclude incidental pose, lighting or background when needed. A location reference need not dictate the camera angle. Remove stale characters, props and tags from earlier shots. If a reference video controls motion or camera, follow the model skill's rules about what text should describe.

## Make camera and performance agree

Choose framing and physical camera placement that can show the important action within the location. Small figures communicate through weight shifts, turns, steps and shoulder movement; subtle eye or jaw reactions need readable faces. Tie listener reactions to what happens or is said, rather than adding unrelated fidgeting.

Keep a static camera when it serves the scene. For a move, name its trigger, starting composition, landing composition and useful hold. Translate requested styles and devices into observable camera, optical, editing or performance behavior. A crash zoom needs a trigger and a held landing; a Dutch angle rolls the frame while camera position can remain fixed. Do not add tricks merely to make a shot sound cinematic.

## Ground action, light and sound

For physical action, select the relevant cause and effect: anticipation, contact, weight transfer, follow-through and settling. Describe motivated light sources and their effect on the surfaces or faces that matter. Avoid universal beauty-lighting or rim-lighting recipes.

For ordinary fast action, allow brief directional motion blur with readable moments of contact and recovery. Do not attach a universal “no blur” suffix; preserve deliberately unusual shutter or motion aesthetics when requested.

Use exact supplied dialogue, assigned to a speaker and beat. Add speech, narration, music or subtitles only when the task calls for them. Match sound sources to the scene and obey the endpoint's audio controls; a prose request for silence is not an audio-off switch.

## Repair locally

Check opening state, reference roles, readable action, feasible camera placement, ending and sound before output. When a generation fails, patch the relevant direction and keep the successful wording. Add only constraints aimed at the observed failure, in the format supported by the model.
