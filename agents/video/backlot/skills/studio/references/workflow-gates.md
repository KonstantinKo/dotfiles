# Workflow requirements

Generated from `backlot.workflow.REQUIREMENTS`.

The base workflow asks for an agreed brief, named scenes, exact deliverables, output verification, source coverage and scoped user approval. Add only requirements the production needs. `backlot stage --json` reports each missing scene or deliverable requirement.

| Requirement | Evidence |
|---|---|
| `picture` | Selected output ranges and a version-matched user approval. |
| `board` | An explicitly selected, approved board take for the scene. |
| `identity` | Declared character/identity Context locks and their selected takes. |
| `world` | Declared location/world Context locks and their selected takes. |
| `spatial` | A declared motion or spatial guide with exact bytes. |
| `blender` | A declared editable Blender scene/version and guide export. |
| `voice` | Declared voice media bound to the assembly or named caption source. |
| `captions` | Declared caption file with exact bytes. |
| `score` | Declared score media bound to this output revision. |
| `graphics` | Declared exact graphic source with exact bytes. |
| `review` | Version-bound review evidence for the declared criterion. |
| `remote_share` | A scoped share approval and recorded share location/term. |

An imported historical acceptance record can cover named requirements only for its original approved artifact and assembly recipe. New bytes require normal declared evidence.
