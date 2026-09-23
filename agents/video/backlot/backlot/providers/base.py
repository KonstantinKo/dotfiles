"""Provider protocol. A provider estimates cost and runs a model, returning media files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from backlot.models import ModelSpec, estimate_cost


class ProviderError(Exception):
    """Provider call failed."""


class ProviderNotConfigured(ProviderError):
    """Provider exists as a stub only; see the vault provider note."""


@dataclass
class GenRequest:
    prompt: str = ""
    text: str = ""
    voice: str = ""
    image: Path | None = None
    audio: Path | None = None
    video: Path | None = None
    params: dict[str, Any] = field(default_factory=dict)
    duration_s: float | None = None
    workdir: Path = Path(".")

    @property
    def chars(self) -> int:
        return len(self.text or self.prompt)


@dataclass
class GenResult:
    files: list[Path]
    job_id: str = ""
    seconds: float = 0.0
    raw: Any = None


@runtime_checkable
class Provider(Protocol):
    name: str

    def estimate(self, model: ModelSpec, req: GenRequest) -> float: ...

    def run(self, model: ModelSpec, req: GenRequest) -> GenResult: ...


class BaseProvider:
    name = "base"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    def estimate(self, model: ModelSpec, req: GenRequest) -> float:
        return estimate_cost(model, n=1, duration_s=req.duration_s, chars=req.chars)

    def run(self, model: ModelSpec, req: GenRequest) -> GenResult:
        raise NotImplementedError

    def call_json(self, model: ModelSpec, req: GenRequest) -> dict[str, Any]:
        """Raw JSON response for non-media models (e.g. stt). Optional."""
        raise ProviderError(f"provider {self.name} does not return JSON results")


def build_arguments(model: ModelSpec, req: GenRequest, uploader) -> dict[str, Any]:
    """Map a request onto endpoint arguments using the model note's `inputs`, `defaults`
    and optional `arg_map` ({input: argument_name}). `uploader(path) -> url`."""
    arg_map = {
        "prompt": "prompt",
        "text": "text",
        "voice": "voice",
        "image": "image_url",
        "audio": "audio_url",
        "video": "video_url",
    }
    arg_map.update(model.arg_map or model.extra.get("arg_map") or {})
    args: dict[str, Any] = dict(model.defaults)
    for inp in model.inputs:
        key = arg_map.get(inp, inp)
        value: Any = None
        if inp == "prompt" and req.prompt:
            value = req.prompt
        elif inp == "text" and (req.text or req.prompt):
            value = req.text or req.prompt
        elif inp == "voice" and req.voice:
            value = req.voice
        elif inp == "image" and req.image:
            value = uploader(req.image)
        elif inp == "audio" and req.audio:
            value = uploader(req.audio)
        elif inp == "video" and req.video:
            value = uploader(req.video)
        if value is None:
            continue
        if inp in ("image", "audio", "video") and key.endswith("s"):
            value = [value]
        _set_arg(args, key, value)
    args.update(req.params)
    return args


def _set_arg(args: dict[str, Any], key: str, value: Any) -> None:
    """`a.b` targets nest under `a` (e.g. minimax `voice_setting.voice_id`)."""
    parts = key.split(".")
    node = args
    for part in parts[:-1]:
        child = node.get(part)
        if not isinstance(child, dict):
            child = {}
            node[part] = child
        node = child
    node[parts[-1]] = value
