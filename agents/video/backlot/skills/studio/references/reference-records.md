# Reference records

Use a reference record to say why a source is relevant, what it supports, and where its authority ends. The project-dir starter is `templates/projectdir/references.yaml`; the compact request record is `templates/projectdir/edit/shot-card.yaml`.

## Authority and scope

Use only the authority a source actually supports. Record one or more of these dimensions explicitly:

- `appearance`: visible styling, surface or material qualities.
- `identity`: the identity or stable traits of a specific person or character.
- `layout`: spatial relationships, composition, camera placement or geometry.
- `motion`: a pose, action or movement over time.
- `lighting`: direction, quality, color or falloff of light.

A source can support several dimensions when each is stated. `proves` captures supported observations; `exclude` names details that must not be copied; `limitations` records ambiguity or unseen information. `approval_scope` states the permitted use and boundary, with `approval_ref` pointing to the decision when one exists. A convenient photo or CG guide does not gain broader authority by being attached.

## Provenance and selection

Keep the canonical source revision, its SHA-256, source description, acquisition date and method together. Optional `view_zone` and `light_orientation` identify a useful crop and the light visible in that view. They describe the source; they do not broaden its authority.

Search for semantic features such as an action, object relation or visible change. Inspect the candidate frame and its neighbors, then save a verified locator. Nearby-frame context can disambiguate a useful view when a remembered or approximate timestamp points elsewhere. A timestamp by itself is not evidence that the selected frame shows the requested feature.

## Request records

The shot card separates source facts, assumptions and approved deviations. Facts point to a reference and checked locator. Assumptions include a basis and confidence. Deviations state the exact scope and approval reference. Its ordered `source_refs` list contains only sources sent with that request; list order is submission order. Do not attach a shared gallery or imply that every shot needs references.

Omit fields that do not apply, and leave unknown directions unset or null instead of inventing them.

Keep creative direction concise and put provider, exact model/version/operation, effective controls and applicable promotion in the route fields. Record any estimate with its currency, unit, source, observation date and confidence. Use `amount: null` and `confidence: unknown` when the price is unknown; zero means a verified zero-cost route. Unknown route behavior or settings remain unknown until supported by current provider documentation or a dated local observation.
