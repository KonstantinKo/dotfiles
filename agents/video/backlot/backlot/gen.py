"""Generation pipeline shared by `gen` and `tts`: estimate, confirm, budget, run, persist."""

from __future__ import annotations

import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backlot import takes as takes_mod
from backlot import vault
from backlot.config import Studio
from backlot.errors import EXIT_BUDGET, EXIT_CONFIRM, BacklotError
from backlot.ids import validate_shot_id
from backlot.models import ModelSpec, apply_param_types, estimate_cost, find_model, normalize_kind
from backlot.project import Project
from backlot.providers import GenRequest, ProviderError, get_provider
from backlot.takes import Take
from backlot.thumbs import make_thumb


@dataclass
class GenOptions:
    kind: str
    model_id: str | None
    prompt: str = ""
    text: str = ""
    voice: str = ""
    image: str | None = None
    audio: str | None = None
    video: str | None = None
    shot: str | None = None
    n: int = 1
    params: dict[str, Any] | None = None
    parent: str | None = None
    depends_on: list[str] | None = None
    dry_run: bool = False
    yes: bool = False


@dataclass
class GenOutcome:
    takes: list[Take] = field(default_factory=list)
    created_shots: list[str] = field(default_factory=list)


def parse_params(items: list[str] | None) -> dict[str, Any]:
    import yaml

    out: dict[str, Any] = {}
    for item in items or []:
        if "=" not in item:
            raise BacklotError(f"--param expects k=v, got {item!r}")
        key, value = item.split("=", 1)
        out[key.strip()] = yaml.safe_load(value) if value.strip() else ""
    return out


def _resolve_input(project: Project, ref: str | None) -> Path | None:
    return takes_mod.resolve_media(project, ref) if ref else None


def _duration(model: ModelSpec, params: dict[str, Any]) -> float | None:
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


def plan(studio: Studio, project: Project, opts: GenOptions) -> tuple[ModelSpec, GenRequest, float, float]:
    """Resolve model + request and return (model, request, estimate_total, spent_so_far)."""
    kind = normalize_kind(opts.kind)
    model_id = opts.model_id or project.default_model(kind)
    if not model_id:
        raise BacklotError(f"no --model given and project.yaml has no default model for kind {kind!r}")
    model = find_model(studio.vault, model_id)
    if model.kind != kind and not (kind == "video" and model.kind == "lipsync"):
        raise BacklotError(f"model {model.id} is kind {model.kind!r}, not {kind!r}")
    if opts.shot:
        validate_shot_id(opts.shot)
    params = apply_param_types(model, dict(opts.params or {}))
    req = GenRequest(
        prompt=opts.prompt,
        text=opts.text,
        voice=opts.voice,
        image=_resolve_input(project, opts.image),
        audio=_resolve_input(project, opts.audio),
        video=_resolve_input(project, opts.video),
        params=params,
        duration_s=_duration(model, params),
    )
    if opts.parent:
        takes_mod.load_take(project, opts.parent)
    _check_depends_on(project, list(opts.depends_on or []))
    if "prompt" in model.inputs and not (req.prompt or req.text) and model.kind not in ("upscale", "stt"):
        raise BacklotError("model needs --prompt")
    if model.kind == "tts" and not (req.text or req.prompt):
        raise BacklotError("tts needs --text or --file")
    missing = [inp for inp in model.required_inputs() if getattr(req, inp) is None]
    if missing:
        raise BacklotError(f"model {model.id} needs " + " and ".join(f"--{m}" for m in missing))
    provider = get_provider(model.provider, studio.provider_config(model.provider))
    try:
        per_run = provider.estimate(model, req)
    except ProviderError as exc:
        raise BacklotError(str(exc)) from exc
    if per_run is None:
        per_run = estimate_cost(model, duration_s=req.duration_s, chars=req.chars)
    total = round(per_run * max(opts.n, 1), 4)
    return model, req, total, takes_mod.spent_eur(project)


def execute(studio: Studio, project: Project, opts: GenOptions) -> GenOutcome:
    """Run the full pipeline; raises BacklotError with EXIT_CONFIRM / EXIT_BUDGET when blocked."""
    model, req, total, spent = plan(studio, project, opts)
    info = {
        "model": model.id, "provider": model.provider, "kind": model.kind, "n": opts.n,
        "estimate_eur": total, "spent_eur": spent, "budget_eur": project.budget_eur,
    }
    if opts.dry_run:
        raise BacklotError(f"dry-run {model.id} x{opts.n}: ~{total:.3f} EUR (spent {spent:.3f} / {project.budget_eur:.2f})", code=0, data={"dry_run": True, **info})
    if project.budget_eur <= 0:
        raise BacklotError(
            "budget_eur is 0 or missing in project.yaml; set a positive budget before generating",
            code=EXIT_BUDGET, data={"budget_exceeded": True, **info},
        )
    if spent + total > project.budget_eur:
        raise BacklotError(
            f"budget exceeded: {spent:.3f} + {total:.3f} > {project.budget_eur:.2f} EUR (raise budget_eur in project.yaml)",
            code=EXIT_BUDGET, data={"budget_exceeded": True, **info},
        )
    if project.ask_before_generate and not opts.yes:
        raise BacklotError(
            f"confirm: {model.id} x{opts.n} ~{total:.3f} EUR (spent {spent:.3f} / {project.budget_eur:.2f}); re-run with --yes",
            code=EXIT_CONFIRM, data={"needs_confirmation": True, **info},
        )
    outcome = GenOutcome()
    if opts.shot and vault.ensure_shot_note(project, opts.shot):
        outcome.created_shots.append(opts.shot)
    provider = get_provider(model.provider, studio.provider_config(model.provider))
    per_run = total / max(opts.n, 1)
    for _ in range(max(opts.n, 1)):
        with tempfile.TemporaryDirectory(prefix="backlot-") as tmp:
            req.workdir = Path(tmp)
            try:
                result = provider.run(model, req)
            except ProviderError as exc:
                raise BacklotError(f"{model.provider}: {exc}") from exc
            per_file = round(per_run / max(len(result.files), 1), 4)
            for media in result.files:
                take_id = takes_mod.allocate_id(project, model.take_prefix, opts.parent)
                take = Take(
                    take=take_id, kind=model.take_prefix, model=model.id, provider=model.provider, shot=opts.shot,
                    status="new", cost_eur=per_file, parent=opts.parent, depends_on=list(opts.depends_on or []),
                    prompt=req.prompt or req.text, params=_record_params(req), voice=req.voice or None,
                    job_id=result.job_id, seconds=round(result.seconds, 2),
                )
                takes_mod.save_take(project, take, media, raw=result.raw)
                thumb = _thumb(project, take)
                vault.write_take_note(project, take, thumb)
                vault.record_take_on_shot(project, take)
                outcome.takes.append(take)
    vault.write_costs(project)
    vault.write_status(project)
    return outcome


def _thumb(project: Project, take: Take) -> Path | None:
    try:
        return make_thumb(project.root / take.file, vault.thumbs_dir(project), take.take)
    except (BacklotError, OSError) as exc:
        print(f"warn: thumbnail for {take.take} failed: {exc}", file=sys.stderr)
        return None


def _record_params(req: GenRequest) -> dict[str, Any]:
    params = dict(req.params)
    if req.image:
        params["image"] = str(req.image)
    if req.audio:
        params["audio"] = str(req.audio)
    if req.video:
        params["video"] = str(req.video)
    if req.duration_s and "duration" not in params:
        params["duration"] = req.duration_s
    return params
