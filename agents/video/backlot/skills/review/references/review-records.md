# Review and repair records

`backlot.reviews` stores version-bound evidence. It does not approve a take, edit a shot card, run a provider, or authorize spend. Pass a resolved `Project` and a mapping to each function; each returns the YAML-safe record it wrote. Validation failures raise `BacklotError`.

## Record a review

`register_review(project, spec)` writes `Records/reviews/review-<uuid>.yaml`. Bind every record to exact subject bytes:

```python
spec = {
    "subject": {"kind": "take", "id": "vid-014.2", "sha256": "<64-char sha256>"},
    "source": {"kind": "human_playback", "ref": "conversation:message-81", "observed_at": "2026-10-02T09:30:00Z"},
    "coverage": {"mode": "full_playback", "ranges": []},
    "technical": {"checks": [
        {"name": "full decode", "result": "pass", "evidence": ["ffmpeg:decode-log"]},
    ]},
    "semantic": {"criteria": [
        {"id": "identity-stable", "name": "Subject stays recognizable",
         "result": "fail", "timecodes": ["00:00:01.4"], "evidence": ["playback:middle"]},
    ]},
    "context": {"status": "not_applicable", "reason": "Standalone clip"},
    "listening": {"status": "pending", "reason": "Audio review not done"},
    "presentation": {"status": "presented", "kind": "cli_output",
                      "ref": "backlot-review:run-51", "observed_at": "2026-10-02T09:30:00Z"},
    "accepted_limits": [],
}
record = register_review(project, spec)
```

`subject.kind` is `take` or `render`; a render ID is a path inside this project's `renders/`. The helper reads the current bytes and rejects a wrong declared hash or a take hash that disagrees with its metadata. Source evidence requires a free-form `kind`, stable `ref`, and timezone-qualified ISO `observed_at`; these fields identify evidence but do not verify that it is truthful.

Technical checks and semantic/context/listening criteria are separate. Technical pass/fail checks need evidence references; criterion pass/fail results need evidence or timecodes. Unsupported criteria need a reason. The optional listening layer defaults to `unsupported` with “listening review not supplied”; never convert that to a pass based on video decode or image inspection. Subjective user decisions belong in the Decisions ledger, not the review record.

Coverage modes are `full_playback`, `sampled`, and `technical_only`. Sampled mode requires explicit `{start_s, end_s}` ranges and yields `pass_limited` when all recorded checks pass. Technical-only mode cannot claim a semantic pass or playback ranges. Full-playback coverage is an explicit reviewer claim; this helper does not observe playback. Missing presentation evidence leaves the record `not_presented`.

To mark `presentation.status: presented`, the CLI caller must emit the review findings to the user as part of that command and attach a stable output/event reference and timestamp. Do not set it when only storing a record. A stored, unpresented review currently has no presentation-update API and cannot be used to plan a repair.

Accepted limitations use exact, already-recorded `accept-limit` decision IDs for the same subject ID and SHA-256:

```python
"accepted_limits": [{"criterion_id": "minor-age-drift", "decision_id": "dec-<32 hex>"}]
```

The helper checks that each ID names an `accept-limit` decision whose subject ID and version equal this record's subject ID and SHA-256. It carries mapped limitations into later reviews of the same version, even if a later call omits them. This is not an approval and does not change the ledger.

## Plan a repair

`plan_repair(project, spec)` writes a no-spend plan under `Records/repairs/`. It accepts only a presented first-pass review, rechecks the parent bytes, and targets criteria recorded as failed, pending, or unsupported. For a take, original/effective requests and source refs come from take metadata. A render needs the same exact fields in `parent_manifest`.

```python
plan = plan_repair(project, {
    "parent_review_id": record["id"],
    "repair_kind": "provider_job",  # provider_job | local_edit | external_edit
    "target_criteria": ["identity-stable"],
    "changes": [{"field": "prompt", "before": "single figure",
                 "after": "one unchanged figure throughout motion",
                 "reason": "address the observed middle-frame morph"}],
    "source": {"kind": "user_message", "ref": "conversation:message-84",
               "observed_at": "2026-10-02T09:34:00Z"},
})
```

The plan retains the exact parent subject/hash, original and effective request, source refs, inherited effective controls, explicit before/after changes, and accepted limitations. `provider_call_submitted` is always false; the function never creates a job or grants spend authority. A targeted accepted limitation stays closed unless `reopen_limits` names its decision ID and includes `source_kind: user_message`, `source_ref`, `source_message`, and timezone-qualified `observed_at`. Reopening is recorded on that plan only; it does not alter the original decision.

## Record the result

`record_repair_result(project, spec)` appends to `Records/repair-results/`. Report job state separately from human findings. A completed job needs an output subject and exact hash; an effective outcome always needs output bytes. Include a target review row for every targeted criterion when recording criteria. Context is a separate review and defaults to pending.

```python
result = record_repair_result(project, {
    "repair_id": plan["id"],
    "source": {"kind": "human_playback", "ref": "conversation:message-90",
               "observed_at": "2026-10-02T09:42:00Z"},
    "job_status": "completed",  # completed | failed | pending | not_applicable
    "target_outcome": "effective",  # effective | ineffective | pending | context_fail
    "output": {"kind": "render", "id": "repaired.mp4", "sha256": "<64-char sha256>"},
    "target_review": {"criteria": [
        {"id": "identity-stable", "name": "Subject stays recognizable", "result": "pass",
         "timecodes": ["00:00:01.4"], "evidence": ["playback:repair-middle"]},
    ]},
    "context": {"status": "pass", "criteria": [
        {"id": "splice", "name": "Join matches adjacent shot", "result": "pass",
         "timecodes": ["00:00:02.0"], "evidence": ["cut-review:join"]},
    ]},
})
```

`completed` alone never establishes repair success: the target must pass and context must pass or be explicitly `not_applicable`. Identical parent/output hashes cannot be effective; they are recorded as ineffective. A changed image with a failed contextual join is `context_fail`, even if the target criterion passes. Results set `approval_changed: false`.

For `job_status: failed`, a cause is retained only when `failure` has both an observed `message` and an `evidence_ref` to the actual error. Otherwise the record says `failed; cause unavailable`. Do not infer moderation, provider policy, or another cause from an empty response or a generic failure.

## CLI integration contract

CLI handlers should resolve the current project once, build these mappings from observed records and explicit user evidence, call the corresponding helper, and print the returned record ID and outcome. Preserve each returned `BacklotError` as a refusal with its reason. Keep result storage separate from `backlot approve` and other decision commands. Only a subsequent, separately authorized command may submit a paid call, using the existing exact-call authorization flow. Status or cost display must not refresh or rewrite records as a side effect.
