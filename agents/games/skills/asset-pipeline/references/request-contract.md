# Durable asset request and delivery contract

Proposed v1 protocol. No queue executable or scheduler is bundled. These fields can be mapped to an existing job system. Suggested first local implementation: SQLite transactions for ownership/events/budget, JSON manifests for human review, binary assets in the normal project store. Avoid simultaneous whole-file rewrites of one JSON queue.

## Request

Required information, whether initially supplied as prose or JSON:

- `schema_version`, immutable `request_id`, integer `spec_revision`, `idempotency_key`, content hash.
- `requester`: stable agent/task identifier, project root, optional supported notification destination. A caller identifier is not authorization to send external messages.
- `purpose`: scene use, dressing versus gameplay semantics, expected reuse and viewing conditions.
- `references`: paths/URIs and content hashes with primary/supporting role and what each constrains; style authority and explicit exceptions. For an asset inside an image, include a target description and optional region/mask with coordinate convention. Preserve the original plus any derived views and their relationship.
- Optional `concept_policy`: `use_supplied`, `derive_if_needed` or `create`; infer from the inputs if omitted. See [reference intake and examples](reference-inputs.md). A sufficient supplied image fulfills the concept deliverable without a generation call.
- `review_mode`: ordinary `iterative_delivery` by default; `first_delivery_test` only when requested. Record any fixed-reference test policy and visual checkpoints for an unproven high-fidelity route.
- `geometry`: units, dimensions or allowed envelope, source/export axes, origin/pivot, visible/hidden surfaces, separate parts, motion needs. Record unknown/inferred fields explicitly.
- `interfaces`: required connector IDs/versions, local frames and mating tolerances; empty for nonmodular work. A full interface schema can be supplied by the project.
- `delivery`: concept/source/runtime endpoint, formats, required evidence and acceptance criteria. Runtime includes target engine/hardware, instance count, triangle/material/texture budget, collision and animation needs.
- `budget`: currency, authorized paid ceiling and scope/reference, exploration/retry/time/storage limits. Missing paid authorization permits no new paid calls. Project/batch ceiling also applies.
- `dependencies`: immutable asset/material/interface versions; `priority` and optional needed-by time.
- `proxy`: stable ID, dimensions, axes and pivot that let the caller proceed with a placeholder.

Do not require invented precision. Dimensions can be an envelope or explicitly inferred for dressing; a mating interface needs its actual constraint. Validate contradictions before dependent work. Reject duplicate idempotency keys with different content; return the existing ticket for identical content. A new spec revision invalidates publication against the old revision, while preserving its evidence/costs.

## Job lifecycle

`queued → working → ready → accepted`

A working job also records a stage such as `intake`, `reuse`, `concept`, `build`, `review`, `method_review`, `delivery`, plus `waiting_external` and provider job IDs when relevant. `needs_input`, `budget_exhausted`, `failed`, and `cancelled` retain reasons and useful partial results. A failed defining visual criterion stays working at the appropriate stage, with a retained candidate. `awaiting_requester_review` identifies an internal checkpoint; `method_review` means a repeated failure requires a diagnosis/route decision before another production experiment. Neither means finished or awaiting new human approval. Record a user-directed pause explicitly. A real assignment/resource boundary may produce an `incomplete` result with the boundary and failed criteria; `first_delivery_test` may freeze such a result intentionally. A caller's change creates a new spec revision; rejection without changed specs creates a new attempt while keeping the previous ready result.

The queue returns a request ID and proxy contract immediately after durable submission. The caller continues independent scene work. A worker claim atomically grants a lease with a monotonically increasing fencing token; heartbeat renews it. After expiry, a replacement worker reconciles durable provider state before continuing. Only the current token and spec revision may publish state/results or reserve further costs. Losing ownership prevents new paid work and promotion. Expiry alone must not trigger a duplicate paid submission.

The queue transaction reserves cost before external submission. Because a database transaction cannot make a remote API call atomic, persist an intent first and the returned provider ID immediately. If a crash leaves intent without ID, reconcile through provider idempotency/status when supported. If reconciliation is impossible, mark submission uncertain and hold its reservation; do not auto-resubmit. No exactly-once provider guarantee is assumed.

Keep an append-only event sequence with UTC time, stage, actor, spec revision and fencing token; no media blobs/secrets. Persist inputs, remote IDs, outputs, usage and next action before waiting or handing over. Worker scratch directories are separate; accepted assets and shared materials are immutable by version. Resource limits apply across the queue, not just each worker.

Cancellation prevents future paid calls and result promotion. Attempt remote cancellation only if supported; record already-incurred or uncertain costs even when cancellation succeeds. Preserve useful partial output without marking it accepted. Late provider results for cancelled/superseded work may be recorded as evidence, not installed into the scene.

## Result

An immutable manifest includes:

- Request/spec/attempt and asset revision IDs; worker lease token at publication; input and artifact hashes.
- Endpoint achieved and `worker_reviewed` decision, requested criteria with passed/failed/unverified status and evidence paths. Include the locked primary reference/region/hash, the last requester checkpoint decision and unresolved defining visual defects.
- Editable source, runtime export if requested, preview/diagnostic images and reproducible build instructions; paths relative to project/artifact root where possible.
- Dimensions, source/export axes, pivot, part names, interfaces and compatible dependency versions.
- Material/texture dependencies, map bindings and physical scale assumptions, actual triangle/material/texture-memory measurements as applicable.
- Provenance/license and generation settings/provider IDs where applicable, paid estimated/confirmed/uncertain amounts, measured timings and retained bytes.
- Explicit departures, unsupported interactions, remaining technical limits, and import instructions.

Write files to a staging location, verify hashes/evidence, then atomically publish the manifest and ready event. A partial directory must not look ready. `ready` means worker-reviewed criteria pass for the requested endpoint, not merely that files exist. A failed visual criterion cannot be waived by a technical pass or a limitations paragraph. Requester acceptance follows direct visual review and endpoint-appropriate export/scene checks; source-only requests do not require invented runtime integration. The caller may not be the human user: preserve those acceptance levels separately. A source-only deliverable cannot pass a runtime request by changing its label.

Use a supported internal notification if available; delivery is at least once, and the caller deduplicates by request/spec/result revision. Persist events/result even if the caller has exited. On reconnect it reads status or events after its last sequence number. If no wakeup mechanism exists, status must say ready-awaiting-pickup; do not promise autonomous resumption.

## Minimal implementation acceptance tests

Before claiming an asynchronous service works, exercise: two concurrent claims; duplicate submit; changed spec; worker crash before/after provider-ID persistence; lease expiry with stale publication; cancellation while remote work runs; exhausted shared budget; partial delivery; duplicate/missed notification; and caller rejection followed by a corrected immutable result. Fake provider jobs suffice for these tests. An instruction-only skill does not establish any of these runtime guarantees.
