"""Captions: speech-to-text through an stt model note -> .srt + words.json next to the take."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import yaml

from backlot import authority, ffmpeg, takes as takes_mod, vault
from backlot.config import Studio
from backlot.errors import BacklotError
from backlot.gen import guard, record_paid_operation
from backlot.models import find_model, load_models, validate_estimate, validate_price
from backlot.overlays import Cue, write_srt
from backlot.project import Project
from backlot.providers import GenRequest, ProviderError, get_provider
from backlot.providers.base import ProviderPreSubmitError
from backlot.takes import Take
from backlot.thumbs import media_kind

MAX_CHARS = 42
MAX_CUE_S = 4.0


def _stt_model(studio: Studio, model_id: str | None):
    if model_id:
        model = find_model(studio.vault, model_id)
    else:
        models, _ = load_models(studio.vault)
        active = [m for m in models if m.kind == "stt" and m.status != "disabled"]
        if not active:
            raise BacklotError("no stt model note in the vault (Studio/Models with kind: stt); add one or pass --model")
        model = active[0]
    if model.kind != "stt":
        raise BacklotError(f"model {model.id} is kind {model.kind!r}, not stt")
    validate_price(model)
    return model


def normalize_words(result: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    """Return (full text, [{start, end, text}]) from whisper / elevenlabs / generic shapes."""
    items: list[dict[str, Any]] = []
    if isinstance(result.get("words"), list):
        for w in result["words"]:
            if w.get("type", "word") != "word" or w.get("start") is None:
                continue
            items.append({"start": float(w["start"]), "end": float(w.get("end", w["start"])), "text": str(w.get("text", "")).strip()})
    elif isinstance(result.get("chunks"), list):
        for c in result["chunks"]:
            ts = c.get("timestamp") or [c.get("start"), c.get("end")]
            if not ts or ts[0] is None:
                continue
            end = ts[1] if len(ts) > 1 and ts[1] is not None else ts[0]
            items.append({"start": float(ts[0]), "end": float(end), "text": str(c.get("text", "")).strip()})
    elif isinstance(result.get("segments"), list):
        for s in result["segments"]:
            if s.get("start") is None:
                continue
            items.append({"start": float(s["start"]), "end": float(s.get("end", s["start"])), "text": str(s.get("text", "")).strip()})
    text = str(result.get("text") or " ".join(i["text"] for i in items)).strip()
    return text, [i for i in items if i["text"]]


def cues_from_words(items: list[dict[str, Any]]) -> list[Cue]:
    if not items:
        return []
    avg = sum(i["end"] - i["start"] for i in items) / len(items)
    if avg > 1.5:
        return [Cue(i["start"], max(i["end"], i["start"] + 0.5), i["text"]) for i in items]
    cues: list[Cue] = []
    buf: list[dict[str, Any]] = []

    def flush() -> None:
        if buf:
            cues.append(Cue(buf[0]["start"], max(buf[-1]["end"], buf[0]["start"] + 0.5), " ".join(b["text"] for b in buf)))
            buf.clear()

    for item in items:
        candidate = " ".join(b["text"] for b in buf + [item])
        if buf and (len(candidate) > MAX_CHARS or item["end"] - buf[0]["start"] > MAX_CUE_S or item["start"] - buf[-1]["end"] > 1.0):
            flush()
        buf.append(item)
        if item["text"].endswith((".", "!", "?")) and len(" ".join(b["text"] for b in buf)) > MAX_CHARS // 2:
            flush()
    flush()
    return cues


def _audio_source(src: Path, tmp: Path) -> Path:
    if media_kind(src) == "video":
        out = tmp / "audio.wav"
        ffmpeg.run([ffmpeg.which("ffmpeg") or "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(out)])
        return out
    return src


def run_captions(studio: Studio, project: Project, ref: str, model_id: str | None, *, yes: bool = False,
                 dry_run: bool = False, force: bool = False, authorization: str | None = None) -> dict[str, Any]:
    """Reserve a recoverable operation before a paid STT create request."""
    model = _stt_model(studio, model_id)
    src = takes_mod.resolve_media(project, ref)
    is_take = takes_mod.meta_path(project, ref).exists()
    out_dir = src.parent if is_take else project.root / "renders"
    provider = get_provider(model.provider, studio.provider_config(model.provider))
    operation: Take | None = None
    with tempfile.TemporaryDirectory(prefix="backlot-cap-") as tmp:
        audio = _audio_source(src, Path(tmp))
        req = GenRequest(audio=audio, params={}, duration_s=ffmpeg.duration(audio) or None, workdir=Path(tmp))
        try:
            cost = round(float(provider.estimate(model, req)), 4)
        except ProviderError as exc:
            raise BacklotError(f"{model.provider}: {exc}") from exc
        validate_estimate(model, cost)
        info = {"model": model.id, "provider": model.provider, "kind": "stt", "src": ref}
        quoted = authority.quote(model, req, cost_eur=cost, parent=ref,
                                 override_max_call=force)
        guard(studio, project, info, per_call=cost, total=cost, spent=takes_mod.spent_eur(project),
              yes=yes, dry_run=dry_run, force=force, label=f"captions {ref} ({model.id})",
              quoted=quoted, authorizations=[authorization] if authorization else [], calls=1)
        if cost:
            authority.reserve(project, authorization, quoted)
            try:
                with takes_mod.locked(project):
                    if takes_mod.spent_eur(project) + cost > project.budget_eur:
                        raise BacklotError("budget changed before captions reservation")
                    operation = Take(take=takes_mod.allocate_id(project, "cap"), kind="cap",
                                     model=model.id, provider=model.provider, cost_eur=cost,
                                     endpoint=model.endpoint, authorization_id=authorization,
                                     params={"source_ref": ref, "source_path": str(src),
                                             "out_dir": str(out_dir), "stem": "out" if is_take else src.stem})
                    takes_mod.reserve_take(project, operation)
            except Exception:
                authority.update_state(project, authorization, "available")
                raise

        def on_submit(request_id: str) -> None:
            if operation:
                operation.request_id = request_id
                record_paid_operation(project, operation)
                takes_mod.write_meta(project, operation)
                authority.update_state(project, authorization, "submitted", take=operation.take,
                                       request_id=request_id)

        req.on_submit = on_submit
        req.on_before_submit = (lambda: authority.check_before_submit(project, authorization)) if cost else None
        try:
            staged = authority.stage_request(req, quoted, Path(tmp) / "approved-inputs")
            if staged.on_before_submit:
                staged.on_before_submit()
            result = provider.call_json(model, staged)
            if operation:
                record_paid_operation(project, operation)
                takes_mod.write_meta(project, operation, raw=result)
                authority.update_state(project, authorization, "completed", take=operation.take,
                                       request_id=operation.request_id or None)
        except (ProviderError, BacklotError, OSError) as exc:
            if operation:
                if not (isinstance(exc, ProviderPreSubmitError) and not operation.request_id):
                    record_paid_operation(project, operation)
                authority.update_state(project, authorization,
                                       "available" if isinstance(exc, ProviderPreSubmitError) and not operation.request_id else "uncertain",
                                       take=operation.take, request_id=operation.request_id or None, error=str(exc))
                if isinstance(exc, ProviderPreSubmitError) and not operation.request_id:
                    takes_mod.discard_take(project, operation.take)
                else:
                    _failed(project, operation, str(exc))
            raise BacklotError(f"{model.provider}: {exc}") from exc
    return _finish(project, operation, result, out_dir, "out" if is_take else src.stem, model.id, cost)


def _failed(project: Project, operation: Take, reason: str, raw: Any = None) -> None:
    operation.status = "failed"
    operation.error = reason.splitlines()[0][:300]
    takes_mod.write_meta(project, operation, raw=raw)
    vault.write_take_note(project, operation, None)
    vault.write_costs(project)


def _finish(project: Project, operation: Take | None, result: dict[str, Any],
            out_dir: Path, stem: str, model_id: str, cost: float) -> dict[str, Any]:
    text, items = normalize_words(result)
    if not items:
        if operation:
            _failed(project, operation, "STT result has no timestamps", result)
        raise BacklotError(f"stt result has no timestamps (keys: {', '.join(result)[:200]})")
    cues = cues_from_words(items)
    srt = write_srt(cues, out_dir / f"{stem}.srt")
    words = out_dir / f"{stem}.words.json"
    words.write_text(json.dumps({"text": text, "model": model_id, "words": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    if operation:
        operation.status = "new"
        operation.error = None
        operation.file = str(srt.relative_to(project.root))
        takes_mod.write_meta(project, operation, raw=result)
        vault.write_take_note(project, operation, None)
        vault.write_costs(project)
    return {"srt": str(srt), "words": str(words), "cues": len(cues), "cost_eur": cost,
            "model": model_id, "operation": operation.take if operation else None}


def recover_captions(studio: Studio, project: Project, take_id: str) -> Take:
    """Parse saved result or poll the accepted request; never submit another job."""
    operation = takes_mod.load_take(project, take_id)
    if operation.kind != "cap" or operation.status not in takes_mod.UNFINISHED:
        raise BacklotError(f"{take_id} is not an unfinished captions operation")
    meta = yaml.safe_load(takes_mod.meta_path(project, take_id).read_text(encoding="utf-8")) or {}
    result = meta.get("response")
    if result is None:
        if not operation.request_id:
            raise BacklotError(f"{take_id} has no request id; check provider history before another paid call")
        provider = get_provider(operation.provider, studio.provider_config(operation.provider))
        try:
            result = provider.fetch_json(operation.endpoint, operation.request_id)
        except ProviderError as exc:
            raise BacklotError(f"{operation.provider}: {exc}") from exc
        takes_mod.write_meta(project, operation, raw=result)
        record_paid_operation(project, operation)
        if operation.authorization_id:
            authority.update_state(project, operation.authorization_id, "completed", take=operation.take,
                                   request_id=operation.request_id)
    params = operation.params
    _finish(project, operation, result, Path(params["out_dir"]), params["stem"],
            operation.model, operation.cost_eur)
    return takes_mod.load_take(project, take_id)
