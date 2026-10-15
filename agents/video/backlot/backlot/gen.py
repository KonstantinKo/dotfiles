"""Generation pipeline shared by `gen`, `tts`, `batch` and `captions`: estimate, guard, reserve, run, persist."""

from __future__ import annotations

import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backlot import expenses, takes as takes_mod
from backlot import authority
from backlot import vault
from backlot.config import Studio
from backlot.errors import EXIT_BUDGET, EXIT_CONFIRM, BacklotError
from backlot.ids import validate_shot_id
from backlot.models import ModelSpec, apply_param_types, estimate_cost, find_model, load_models, normalize_kind, validate_estimate, validate_price
from backlot.project import Project
from backlot.providers import GenRequest, GenResult, ProviderError, get_provider
from backlot.providers.base import MEDIA_INPUTS, ProviderPreSubmitError, check_media_arity
from backlot.takes import Take
from backlot.thumbs import make_thumb


@dataclass
class GenOptions:
    kind: str
    model_id: str | None
    prompt: str = ""
    text: str = ""
    voice: str = ""
    image: list[str] | str | None = None
    audio: list[str] | str | None = None
    video: list[str] | str | None = None
    end_image: str | None = None
    shot: str | None = None
    n: int = 1
    params: dict[str, Any] | None = None
    parent: str | None = None
    depends_on: list[str] | None = None
    dry_run: bool = False
    yes: bool = False
    force: bool = False
    authorizations: list[str] = field(default_factory=list)

    def media(self, inp: str) -> list[str]:
        value = getattr(self, inp)
        if value is None or value == []:
            return []
        return [str(v) for v in value] if isinstance(value, (list, tuple)) else [str(value)]


@dataclass
class GenOutcome:
    takes: list[Take] = field(default_factory=list)
    created_shots: list[str] = field(default_factory=list)


@dataclass
class Planned:
    model: ModelSpec
    req: GenRequest
    per_run: float
    total: float
    spent: float
    quote: dict[str, Any]


def parse_params(items: list[str] | None) -> dict[str, Any]:
    import yaml

    out: dict[str, Any] = {}
    for item in items or []:
        if "=" not in item:
            raise BacklotError(f"--param expects k=v, got {item!r}")
        key, value = item.split("=", 1)
        out[key.strip()] = yaml.safe_load(value) if value.strip() else ""
    return out


def _duration(model: ModelSpec, params: dict[str, Any]) -> float | None:
    composition_plan = params.get("composition_plan")
    if "composition_plan" in params:
        chunks = composition_plan.get("chunks") if isinstance(composition_plan, dict) else None
        if not isinstance(chunks, list) or not chunks:
            raise BacklotError("composition_plan needs a non-empty chunks list")
        if len(chunks) > 30:
            raise BacklotError("composition_plan supports at most 30 chunks")
        durations_ms: list[int] = []
        for i, chunk in enumerate(chunks, 1):
            duration_ms = chunk.get("duration_ms") if isinstance(chunk, dict) else None
            if isinstance(duration_ms, bool) or not isinstance(duration_ms, (int, float)) or int(duration_ms) != duration_ms:
                raise BacklotError(f"composition_plan.chunks[{i - 1}].duration_ms must be an integer")
            if not 3000 <= int(duration_ms) <= 120000:
                raise BacklotError(f"composition_plan.chunks[{i - 1}].duration_ms must be 3000–120000")
            durations_ms.append(int(duration_ms))
        total_ms = sum(durations_ms)
        if not 3000 <= total_ms <= 600000:
            raise BacklotError("composition_plan total duration must be 3000–600000 ms")
        return total_ms / 1000.0
    for key in ("duration", "duration_s", "num_seconds", "seconds"):
        if key in params:
            try:
                return float(str(params[key]).rstrip("s"))
            except (TypeError, ValueError):
                continue
    for key in ("duration", "duration_s", "num_seconds"):
        if key in model.defaults:
            try:
                return float(str(model.defaults[key]).rstrip("s"))
            except (TypeError, ValueError):
                continue
    return model.max_duration_s


def _check_depends_on(project: Project, deps: list[str]) -> None:
    missing = []
    for dep in deps:
        try:
            vault.context_note(project, dep)
        except BacklotError:
            missing.append(dep)
    if missing:
        raise BacklotError(
            "unknown Context notes in --depends-on: " + ", ".join(missing)
            + f"; create them under {project.vault_project / 'Context'} from the matching _template.md first"
        )


def plan(studio: Studio, project: Project, opts: GenOptions) -> Planned:
    """Resolve model + request, validate everything that can be validated before spending."""
    kind = normalize_kind(opts.kind)
    model_id = opts.model_id or project.default_model(kind)
    if not model_id:
        raise BacklotError(f"no --model given and project.yaml has no default model for kind {kind!r}")
    model = find_model(studio.vault, model_id)
    validate_price(model)
    if model.kind != kind and not (kind == "video" and model.kind == "lipsync"):
        raise BacklotError(f"model {model.id} is kind {model.kind!r}, not {kind!r}")
    if opts.shot:
        validate_shot_id(opts.shot)
    params = apply_param_types(model, dict(opts.params or {}))
    media = {inp: [takes_mod.resolve_media(project, ref) for ref in opts.media(inp)] for inp in MEDIA_INPUTS}
    req = GenRequest(
        prompt=opts.prompt,
        text=opts.text,
        voice=opts.voice,
        images=media["image"],
        audios=media["audio"],
        videos=media["video"],
        end_image=takes_mod.resolve_media(project, opts.end_image) if opts.end_image else None,
        params=params,
        duration_s=_duration(model, params),
    )
    if opts.parent:
        parent = takes_mod.load_take(project, opts.parent)
        if parent.kind != model.take_prefix:
            raise BacklotError(f"--parent {opts.parent} is a {parent.kind} take; a {model.take_prefix} variation needs a {model.take_prefix}-* parent")
    _check_depends_on(project, list(opts.depends_on or []))
    if "prompt" in model.inputs and not (req.prompt or req.text) and "composition_plan" not in params and model.kind not in ("upscale", "stt"):
        raise BacklotError("model needs --prompt")
    if "composition_plan" in params and (req.prompt or req.text):
        raise BacklotError("composition_plan cannot be combined with --prompt or --text")
    if model.kind == "tts" and not (req.text or req.prompt):
        raise BacklotError("tts needs --text or --file")
    missing = [inp for inp in model.required_inputs() if getattr(req, inp) is None]
    if missing:
        raise BacklotError(f"model {model.id} needs " + " and ".join(f"--{m}" for m in missing))
    try:
        check_media_arity(model, req)
    except ProviderError as exc:
        raise BacklotError(str(exc)) from exc
    provider = get_provider(model.provider, studio.provider_config(model.provider))
    try:
        per_run = provider.estimate(model, req)
    except ProviderError as exc:
        raise BacklotError(str(exc)) from exc
    if per_run is None:
        per_run = estimate_cost(model, duration_s=req.duration_s, chars=req.chars)
    per_run = round(float(per_run), 4)
    validate_estimate(model, per_run)
    total = round(per_run * max(opts.n, 1), 4)
    quoted = authority.quote(model, req, cost_eur=per_run, shot=opts.shot,
                             parent=opts.parent, depends_on=opts.depends_on,
                             override_max_call=opts.force)
    return Planned(model=model, req=req, per_run=per_run, total=total,
                   spent=takes_mod.spent_eur(project), quote=quoted)


def guard(
    studio: Studio, project: Project, info: dict[str, Any], *, per_call: float, total: float, spent: float,
    yes: bool, dry_run: bool = False, force: bool = False, label: str = "",
    quoted: dict[str, Any] | None = None, authorizations: list[str] | None = None, calls: int = 1,
) -> None:
    """Budget checks and explicit one-use consent for every paid call."""
    budget = project.budget_eur
    info = {**info, "estimate_eur": total, "spent_eur": spent, "budget_eur": budget,
            "quote": quoted}
    if dry_run:
        raise BacklotError(f"dry-run {label}: ~{total:.3f} EUR (spent {spent:.3f} / {budget:.2f})", code=0, data={"dry_run": True, **info})
    if total <= 0:
        return
    if budget <= 0:
        raise BacklotError(
            "budget_eur is 0 or missing in project.yaml; set a positive budget before generating",
            code=EXIT_BUDGET, data={"budget_exceeded": True, **info},
        )
    max_call = project.threshold("max_call_eur", studio)
    if per_call > max_call and not force:
        raise BacklotError(
            f"single call ~{per_call:.3f} EUR is above max_call_eur {max_call:.2f}; re-run with --force or raise max_call_eur",
            code=EXIT_BUDGET, data={"max_call_exceeded": True, "max_call_eur": max_call, **info},
        )
    if spent + total > budget:
        raise BacklotError(
            f"budget exceeded: {spent:.3f} + {total:.3f} > {budget:.2f} EUR (raise budget_eur in project.yaml)",
            code=EXIT_BUDGET, data={"budget_exceeded": True, **info},
        )
    if not yes or len(authorizations or []) != calls:
        raise BacklotError(
            f"exact approval required for each paid call ({calls}); quote the request, record the user message, then pass one --authorization per call with --yes",
            code=EXIT_CONFIRM, data={"needs_confirmation": True, **info},
        )


def execute(studio: Studio, project: Project, opts: GenOptions) -> GenOutcome:
    """Run the full pipeline; raises BacklotError with EXIT_CONFIRM / EXIT_BUDGET when blocked."""
    p = plan(studio, project, opts)
    model, req = p.model, p.req
    info = {"model": model.id, "provider": model.provider, "kind": model.kind, "n": opts.n}
    guard(studio, project, info, per_call=p.per_run, total=p.total, spent=p.spent,
          yes=opts.yes, dry_run=opts.dry_run, force=opts.force, label=f"{model.id} x{opts.n}",
          quoted=p.quote, authorizations=opts.authorizations, calls=max(opts.n, 1))
    outcome = GenOutcome()
    if opts.shot and vault.ensure_shot_note(project, opts.shot):
        outcome.created_shots.append(opts.shot)
    provider = get_provider(model.provider, studio.provider_config(model.provider))
    for i in range(max(opts.n, 1)):
        auth_id = opts.authorizations[i] if p.per_run > 0 else None
        _run_one(project, model, req, opts, provider, p.per_run, info, outcome, auth_id, p.quote)
    vault.write_costs(project)
    vault.write_status(project, studio)
    return outcome


def _reserve(project: Project, model: ModelSpec, req: GenRequest, opts: GenOptions, per_run: float, info: dict[str, Any], auth_id: str | None, quoted: dict[str, Any]) -> Take:
    """Under the takes lock: re-check the budget against everything spent or reserved, then reserve an id."""
    with takes_mod.locked(project):
        spent = takes_mod.spent_eur(project)
        if spent + per_run > project.budget_eur:
            raise BacklotError(
                f"budget exceeded: {spent:.3f} + {per_run:.3f} > {project.budget_eur:.2f} EUR (pending takes count)",
                code=EXIT_BUDGET, data={"budget_exceeded": True, "estimate_eur": per_run, "spent_eur": spent, "budget_eur": project.budget_eur, **info},
            )
        take_id = takes_mod.allocate_id(project, model.take_prefix, opts.parent)
        media = quoted["request"]["media"]
        source_refs = [
            {"id": ref, "path": str(path), "sha256": version["sha256"], "role": name}
            for name in ("image", "audio", "video")
            for ref, path, version in zip(opts.media(name), req.media(name), media[name])
        ]
        if opts.end_image and req.end_image:
            source_refs.append({"id": opts.end_image, "path": str(req.end_image),
                                "sha256": media["end_image"][0]["sha256"], "role": "end_image"})
        take = Take(
            take=take_id, kind=model.take_prefix, model=model.id, provider=model.provider, shot=opts.shot,
            status="pending", cost_eur=per_run, parent=opts.parent, depends_on=list(opts.depends_on or []),
            prompt=req.prompt or req.text, params=_record_params(req), voice=req.voice or None, endpoint=model.endpoint,
            authorization_id=auth_id,
            original_request={"prompt": opts.prompt, "text": opts.text, "voice": opts.voice,
                              "image": opts.media("image"), "audio": opts.media("audio"),
                              "video": opts.media("video"), "end_image": opts.end_image,
                              "params": dict(opts.params or {})},
            effective_request=quoted["request"], source_refs=source_refs,
            coverage=[{"shot": opts.shot}] if opts.shot else [],
        )
        return takes_mod.reserve_take(project, take)


def _run_one(project: Project, model: ModelSpec, req: GenRequest, opts: GenOptions, provider, per_run: float,
             info: dict[str, Any], outcome: GenOutcome, auth_id: str | None, quoted: dict[str, Any]) -> None:
    if auth_id:
        authority.reserve(project, auth_id, quoted)
    try:
        take = _reserve(project, model, req, opts, per_run, info, auth_id, quoted)
    except Exception:
        if auth_id:
            authority.update_state(project, auth_id, "available")
        raise

    def on_submit(request_id: str) -> None:
        take.request_id = request_id
        record_paid_operation(project, take)
        takes_mod.write_meta(project, take)
        if auth_id:
            authority.update_state(project, auth_id, "submitted", take=take.take, request_id=request_id)

    req.on_submit = on_submit
    req.on_before_submit = (lambda: authority.check_before_submit(project, auth_id)) if auth_id else None
    with tempfile.TemporaryDirectory(prefix="backlot-") as tmp:
        req.workdir = Path(tmp)
        try:
            staged = authority.stage_request(req, quoted, Path(tmp) / "approved-inputs")
            if staged.on_before_submit:
                staged.on_before_submit()
            result = provider.run(model, staged)
            if auth_id and not take.request_id:
                take.request_id = result.job_id
                record_paid_operation(project, take)
                takes_mod.write_meta(project, take)
                authority.update_state(project, auth_id, "submitted", take=take.take,
                                       request_id=result.job_id or None)
            _complete(project, take, result, opts, outcome)
            if auth_id:
                authority.update_state(project, auth_id, "completed", take=take.take,
                                       request_id=take.request_id or None)
        except (ProviderError, BacklotError, OSError) as exc:
            if per_run and not (isinstance(exc, ProviderPreSubmitError) and not take.request_id):
                record_paid_operation(project, take)
            if auth_id:
                authority.update_state(project, auth_id,
                                       "available" if isinstance(exc, ProviderPreSubmitError) and not take.request_id else "uncertain",
                                       take=take.take, request_id=take.request_id or None, error=str(exc))
            _fail(project, take, exc, pre_submit=isinstance(exc, ProviderPreSubmitError))
            detail = (f" (take {take.take} kept as failed, request {take.request_id})" if take.request_id else
                      f" (take {take.take} kept for billing review; submission status uncertain)" if auth_id and not isinstance(exc, ProviderPreSubmitError) else "")
            raise BacklotError(f"{model.provider}: {exc}" + detail) from exc


def _fail(project: Project, take: Take, exc: BaseException, *, pre_submit: bool = False) -> None:
    """A reservation that never reached the provider is dropped; one with a request id was
    (possibly) billed and stays as `failed` with its cost until `backlot recover` completes it."""
    if not take.request_id and (not take.authorization_id or pre_submit):
        takes_mod.discard_take(project, take.take)
        return
    take.status = "failed"
    take.error = str(exc).splitlines()[0][:300] if str(exc) else exc.__class__.__name__
    takes_mod.write_meta(project, take)
    vault.write_take_note(project, take, None)
    vault.write_costs(project)


def record_paid_operation(project: Project, take: Take) -> None:
    """Keep one quoted operation with an unknown actual charge until receipt evidence exists."""
    if take.cost_eur <= 0:
        return
    if take.expense_id:
        if take.request_id:
            expenses.link_operation(project, take.expense_id, take.request_id)
        return
    estimate = {"amount": take.cost_eur, "unit": "EUR", "basis": "project budget quote"}
    record = expenses.register(project, {
        "provider": take.provider, "operation_id": take.request_id or None,
        "evidence_key": f"take:{take.take}", "source_kind": "generated",
        "estimate": estimate, "project_ledger": estimate,
        "charge_status": "unknown", "charge": None,
        "model": take.model, "authorization_id": take.authorization_id,
    })
    take.expense_id = record["id"]


def _complete(project: Project, take: Take, result: GenResult, opts: GenOptions, outcome: GenOutcome) -> None:
    """Under the takes lock: save the first file into the reserved take, extra files into fresh ids."""
    if not result.files:
        raise BacklotError("provider returned no files")
    total_cost = take.cost_eur
    take.request_id = take.request_id or result.job_id
    if total_cost:
        record_paid_operation(project, take)
    per_file = round(total_cost / len(result.files), 4)
    take.seconds = round(result.seconds, 2)
    with takes_mod.locked(project):
        for i, media in enumerate(result.files):
            if i == 0:
                current = take
            else:
                current = Take.from_dict({**take.to_dict(), "take": takes_mod.allocate_id(project, take.kind, opts.parent), "file": "", "created": ""})
            current.cost_eur = per_file if i < len(result.files) - 1 else round(total_cost - per_file * i, 4)
            takes_mod.save_take(project, current, media, raw=result.raw)
            thumb = _thumb(project, current)
            vault.write_take_note(project, current, thumb)
            vault.record_take_on_shot(project, current)
            outcome.takes.append(current)


def recover(studio: Studio, project: Project, take_id: str) -> Take:
    """Fetch the result of a failed/pending take by its provider request id and complete it."""
    take = takes_mod.load_take(project, take_id)
    if take.status not in takes_mod.UNFINISHED:
        raise BacklotError(f"take {take_id} is {take.status}; only pending or failed takes can be recovered")
    if not take.request_id:
        raise BacklotError(f"take {take_id} has no request_id; submission may have been accepted. Check provider history before any new paid call")
    models, _ = load_models(studio.vault)
    model = next((m for m in models if m.id == take.model), None)
    endpoint = take.endpoint or (model.endpoint if model else "")
    if not endpoint:
        raise BacklotError(f"take {take_id}: no endpoint recorded and model note {take.model} not found")
    provider = get_provider(take.provider, studio.provider_config(take.provider))
    opts = GenOptions(kind=take.kind, model_id=take.model, shot=take.shot, parent=take.parent)
    outcome = GenOutcome()
    with tempfile.TemporaryDirectory(prefix="backlot-recover-") as tmp:
        try:
            result = provider.fetch(endpoint, take.request_id, Path(tmp))
            _complete(project, take, result, opts, outcome)
        except (ProviderError, OSError) as exc:
            raise BacklotError(f"{take.provider}: {exc}") from exc
    vault.write_costs(project)
    vault.write_status(project, studio)
    return outcome.takes[0]


def _thumb(project: Project, take: Take) -> Path | None:
    try:
        return make_thumb(project.root / take.file, vault.thumbs_dir(project), take.take)
    except (BacklotError, OSError) as exc:
        print(f"warn: thumbnail for {take.take} failed: {exc}", file=sys.stderr)
        return None


def _record_params(req: GenRequest) -> dict[str, Any]:
    params = dict(req.params)
    for inp in MEDIA_INPUTS:
        files = req.media(inp)
        if len(files) == 1:
            params[inp] = str(files[0])
        elif files:
            params[inp + "s"] = [str(f) for f in files]
    if req.end_image:
        params["end_image"] = str(req.end_image)
    if req.duration_s and "duration" not in params:
        params["duration"] = req.duration_s
    return params
