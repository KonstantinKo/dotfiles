"""Model catalog: one note per model under <vault>/Studio/Models/, frontmatter is the spec."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backlot import frontmatter
from backlot.errors import BacklotError

MEDIA_INPUTS = ("image", "audio", "video")
KINDS = ("image", "video", "tts", "music", "sfx", "upscale", "stt", "lipsync")
KIND_PREFIX = {
    "image": "img",
    "video": "vid",
    "tts": "vo",
    "music": "mus",
    "sfx": "sfx",
    "upscale": "up",
    "lipsync": "vid",
}
_KIND_ALIASES = {
    "img": "image",
    "vid": "video",
    "vo": "tts",
    "voice": "tts",
    "mus": "music",
    "up": "upscale",
}


def normalize_kind(kind: str) -> str:
    k = kind.strip().lower()
    return _KIND_ALIASES.get(k, k)


@dataclass
class ModelSpec:
    id: str
    provider: str
    kind: str
    endpoint: str = ""
    tier: str = "lite"
    cost_unit: str = "per_run"
    cost_eur: float = 0.0
    status: str = "untested"
    inputs: list[str] = field(default_factory=list)
    max_duration_s: float | None = None
    min_duration_s: float | None = None
    resolutions: list[str] = field(default_factory=list)
    defaults: dict[str, Any] = field(default_factory=dict)
    arg_map: dict[str, str] = field(default_factory=dict)
    param_types: dict[str, str] = field(default_factory=dict)
    optional_inputs: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    path: Path | None = None

    @property
    def take_prefix(self) -> str:
        return KIND_PREFIX.get(self.kind, self.kind[:3])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "provider": self.provider,
            "kind": self.kind,
            "endpoint": self.endpoint,
            "tier": self.tier,
            "cost_unit": self.cost_unit,
            "cost_eur": self.cost_eur,
            "status": self.status,
            "inputs": self.inputs,
            "max_duration_s": self.max_duration_s,
            "min_duration_s": self.min_duration_s,
            "resolutions": self.resolutions,
            "defaults": self.defaults,
            "arg_map": self.arg_map,
            "param_types": self.param_types,
            "optional_inputs": self.optional_inputs,
        }

    def required_inputs(self) -> list[str]:
        """Declared media inputs (image/audio/video) that a request must supply."""
        return [i for i in self.inputs if i in MEDIA_INPUTS and i not in self.optional_inputs]


def parse_model_note(path: Path) -> ModelSpec:
    data, _ = frontmatter.read(path)
    if not data.get("id"):
        raise ValueError("missing 'id'")
    if not data.get("provider"):
        raise ValueError("missing 'provider'")
    kind = normalize_kind(str(data.get("kind", "")))
    if kind not in KINDS:
        raise ValueError(f"unknown kind {data.get('kind')!r}")
    known = {
        "id", "provider", "kind", "endpoint", "tier", "cost_unit", "cost_eur", "status",
        "inputs", "max_duration_s", "min_duration_s", "resolutions", "defaults", "arg_map", "param_types", "optional_inputs",
    }
    for key in ("arg_map", "param_types"):
        if data.get(key) is not None and not isinstance(data[key], dict):
            raise ValueError(f"'{key}' must be a mapping")
    return ModelSpec(
        id=str(data["id"]),
        provider=str(data["provider"]),
        kind=kind,
        endpoint=str(data.get("endpoint") or ""),
        tier=str(data.get("tier") or "lite"),
        cost_unit=str(data.get("cost_unit") or "per_run"),
        cost_eur=float(data.get("cost_eur") or 0.0),
        status=str(data.get("status") or "untested"),
        inputs=[str(x) for x in (data.get("inputs") or [])],
        max_duration_s=float(data["max_duration_s"]) if data.get("max_duration_s") is not None else None,
        min_duration_s=float(data["min_duration_s"]) if data.get("min_duration_s") is not None else None,
        resolutions=[str(x) for x in (data.get("resolutions") or [])],
        defaults=dict(data.get("defaults") or {}),
        arg_map={str(k): str(v) for k, v in (data.get("arg_map") or {}).items()},
        param_types={str(k): str(v) for k, v in (data.get("param_types") or {}).items()},
        optional_inputs=[str(x) for x in (data.get("optional_inputs") or [])],
        extra={k: v for k, v in data.items() if k not in known},
        path=path,
    )


def models_dir(vault: Path) -> Path:
    return vault / "Studio" / "Models"


def load_models(vault: Path, strict: bool = False) -> tuple[list[ModelSpec], list[tuple[Path, str]]]:
    """Return (models, problems). Problems are (path, message) for notes that failed to parse."""
    models: list[ModelSpec] = []
    problems: list[tuple[Path, str]] = []
    folder = models_dir(vault)
    if not folder.is_dir():
        return models, problems
    for path in sorted(folder.glob("*.md")):
        try:
            models.append(parse_model_note(path))
        except (ValueError, KeyError, TypeError) as exc:
            if strict:
                raise BacklotError(f"model note {path.name}: {exc}") from exc
            problems.append((path, str(exc)))
    return models, problems


def find_model(vault: Path, model_id: str) -> ModelSpec:
    models, _ = load_models(vault)
    for m in models:
        if m.id == model_id:
            if m.status == "disabled":
                raise BacklotError(f"model {model_id} is disabled")
            return m
    raise BacklotError(f"unknown model {model_id!r} (no note in {models_dir(vault)})")


def estimate_cost(model: ModelSpec, *, n: int = 1, duration_s: float | None = None, chars: int = 0) -> float:
    unit = model.cost_unit
    if unit == "per_image":
        return round(model.cost_eur * n, 4)
    if unit == "per_second":
        dur = duration_s or model.max_duration_s or 5.0
        if model.min_duration_s:
            dur = max(dur, model.min_duration_s)
        return round(model.cost_eur * dur * n, 4)
    if unit == "per_1k_chars":
        return round(model.cost_eur * max(chars, 1) / 1000.0 * n, 4)
    return round(model.cost_eur * n, 4)


_PARAM_CASTS = {"str": str, "int": int, "float": float, "bool": bool}


def apply_param_types(model: ModelSpec, params: dict[str, Any]) -> dict[str, Any]:
    """Coerce --param values to the types the model note declares in `param_types`."""
    out = dict(params)
    for key, type_name in model.param_types.items():
        if key not in out or out[key] is None:
            continue
        cast = _PARAM_CASTS.get(type_name)
        if cast is None:
            raise BacklotError(f"model {model.id}: param_types.{key} must be one of {', '.join(_PARAM_CASTS)}")
        value = out[key]
        if cast is str and isinstance(value, float) and value.is_integer():
            value = int(value)
        try:
            out[key] = cast(value)
        except (TypeError, ValueError) as exc:
            raise BacklotError(f"--param {key}={value!r} is not a valid {type_name}") from exc
    return out
