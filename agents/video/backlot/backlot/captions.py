"""Captions: speech-to-text through an stt model note -> .srt + words.json next to the take."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from backlot import ffmpeg, takes as takes_mod, vault
from backlot.config import Studio
from backlot.errors import BacklotError
from backlot.gen import guard
from backlot.models import find_model, load_models
from backlot.overlays import Cue, write_srt
from backlot.project import Project
from backlot.providers import GenRequest, ProviderError, get_provider
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


def run_captions(studio: Studio, project: Project, ref: str, model_id: str | None, *, yes: bool = False, dry_run: bool = False, force: bool = False) -> dict[str, Any]:
    """Same spend path as gen: estimate -> guard (budget, max call, confirmation) -> provider."""
    model = _stt_model(studio, model_id)
    src = takes_mod.resolve_media(project, ref)
    is_take = takes_mod.meta_path(project, ref).exists()
    out_dir = src.parent if is_take else project.root / "renders"
    provider = get_provider(model.provider, studio.provider_config(model.provider))
    with tempfile.TemporaryDirectory(prefix="backlot-cap-") as tmp:
        audio = _audio_source(src, Path(tmp))
        req = GenRequest(audio=audio, params={}, duration_s=ffmpeg.duration(audio) or None, workdir=Path(tmp))
        try:
            cost = round(float(provider.estimate(model, req)), 4)
        except ProviderError as exc:
            raise BacklotError(f"{model.provider}: {exc}") from exc
        info = {"model": model.id, "provider": model.provider, "kind": "stt", "src": ref}
        guard(studio, project, info, per_call=cost, total=cost, spent=takes_mod.spent_eur(project),
              yes=yes, dry_run=dry_run, force=force, label=f"captions {ref} ({model.id})")
        try:
            result = provider.call_json(model, req)
        except ProviderError as exc:
            raise BacklotError(f"{model.provider}: {exc}") from exc
    text, items = normalize_words(result)
    if not items:
        raise BacklotError(f"stt result has no timestamps (keys: {', '.join(result)[:200]})")
    cues = cues_from_words(items)
    stem = "out" if is_take else src.stem
    srt = write_srt(cues, out_dir / f"{stem}.srt")
    words = out_dir / f"{stem}.words.json"
    words.write_text(json.dumps({"text": text, "model": model.id, "words": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    if is_take and cost:
        take = takes_mod.load_take(project, ref)
        take.cost_eur = round(take.cost_eur + cost, 4)
        takes_mod.write_meta(project, take)
        vault.write_costs(project)
    return {"srt": str(srt), "words": str(words), "cues": len(cues), "cost_eur": cost, "model": model.id}
