# Decision and spend records

Use this procedure for every paid provider call and every recorded take approval or rejection. Preserve the original user message reference and its original timestamp when recording decisions; do not substitute the time of later reconciliation.

## Paid calls

1. Quote the exact call with the relevant `backlot gen`, `tts`, `captions`, or `batch` command using `--dry-run --json`. Show the exact provider, route/model/version, inputs in submission order, effective settings, promotion, quoted cost, remaining budget, and observed provider balance. Keep the quote file.
2. After the user explicitly approves that exact call, create one authorization for it. Record the original approval text and message reference, the observed balance amount in its native unit, where and when the balance was observed, and a timezone-qualified expiry:

   ```sh
   backlot authorize /tmp/backlot-quote.json \
     --source-message "<explicit approval text>" \
     --source-ref "<user message reference>" \
     --balance <observed amount> \
     --balance-unit "<native unit, such as EUR or credits>" \
     --balance-source "<account/source and observation time>" \
     --expires "<ISO-8601 timestamp with timezone>"
   ```

   For a batch quote, authorize each paid call separately and select it with `--quote-index <1-based index>`.
3. Run the exact quoted call with `--yes --authorization <returned ID>` and without `--dry-run`. For `batch`, pass one `--authorization <ID>` per paid call in request order. `--yes` alone is never approval. A free/local call needs no spend authorization.
4. An accepted paid submission consumes its authorization. Reuse is allowed only for a proven pre-submit failure while the authorization remains valid. Every paid retry needs a new exact quote and authorization. A changed route, input, material setting, or price also needs a new quote and explicit approval.

Do not infer provider balance or convert a shared balance into a per-job charge. Preserve unknown amounts and units as unknown.

## Take decisions

An approval records a user's explicit decision. Preserve its original text, stable message reference, original timestamp, reason, and narrow use scope. A reviewer's rejection may instead cite technical or semantic evidence; identify it as reviewer evidence and use a concrete artifact path/timecode as the reference. A rejection does not imply user rejection. Never invent a user quote or reference. The current `reject` command permits legacy records without source flags; preserve those as unverified rather than backfilling guessed evidence. Use the CLI so the decision is recorded with the take:

```sh
backlot approve <take> --reason "<reason>" \
  --source-message "<explicit approval text>" --source-ref "<user message reference>" \
  --scope "<approved use>" [--lock <Context note>]

backlot reject <take> --reason "<reason>" \
  --source-message "<review evidence or explicit user rejection>" --source-ref "<artifact path/timecode or user message reference>" \
  --scope "<rejection scope>"
```

An approval for one take or use does not authorize another take, variation, route, or spend. Reviewer evidence cannot reopen a user-accepted limitation; only a user decision can do that. Keep source chronology tied to the original message.
