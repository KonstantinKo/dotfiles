"""Provider protocol. A provider estimates cost and runs a model, returning media files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable

from backlot.models import ModelSpec, estimate_cost


class ProviderError(Exception):
    """Provider call failed."""


class ProviderNotConfigured(ProviderError):
    """Provider exists as a stub only; see the vault provider note."""


MEDIA_INPUTS = ("image", "audio", "video")
DEFAULT_ARG_MAP = {
    "prompt": "prompt",
    "text": "text",
    "voice": "voice",
    "image": "image_url",
    "audio": "audio_url",
    "video": "video_url",
    "end_image": "end_image_url",
}


@dataclass
class GenRequest:
    prompt: str = ""
    text: str = ""
    voice: str = ""
    image: Path | None = None
    audio: Path | None = None
    video: Path | None = None
    end_image: Path | None = None
    images: list[Path] = field(default_factory=list)
    audios: list[Path] = field(default_factory=list)
    videos: list[Path] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)
    duration_s: float | None = None
    workdir: Path = Path(".")
    on_submit: Callable[[str], None] | None = None

    def __post_init__(self) -> None:
        for inp in MEDIA_INPUTS:
            many = getattr(self, inp + "s")
            one = getattr(self, inp)
            if many and one is None:
                setattr(self, inp, many[0])
            elif one is not None and not many:
                setattr(self, inp + "s", [one])

    def media(self, inp: str) -> list[Path]:
        return list(getattr(self, inp + "s"))

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

    def fetch(self, endpoint: str, request_id: str, workdir: Path) -> GenResult:
        """Re-fetch a finished request's media by id (`backlot recover`). Optional."""
        raise ProviderError(f"provider {self.name} cannot recover results by request id")


def arg_target(model: ModelSpec, inp: str) -> str:
    arg_map = dict(DEFAULT_ARG_MAP)
    arg_map.update(model.arg_map or model.extra.get("arg_map") or {})
    return arg_map.get(inp, inp)


def check_media_arity(model: ModelSpec, req: GenRequest) -> None:
    """A singular endpoint argument (target not ending in `s`) accepts exactly one file."""
    for inp in MEDIA_INPUTS:
        files = req.media(inp)
        if len(files) > 1 and not arg_target(model, inp).endswith("s"):
            raise ProviderError(f"model {model.id} takes a single --{inp} (argument {arg_target(model, inp)!r}); got {len(files)}")
    if req.end_image is not None and "end_image" not in model.inputs:
        raise ProviderError(f"model {model.id} does not take --end-image (add end_image to its inputs)")


def build_arguments(model: ModelSpec, req: GenRequest, uploader) -> dict[str, Any]:
    """Map a request onto endpoint arguments using the model note's `inputs`, `defaults`
    and optional `arg_map` ({input: argument_name}). `uploader(path) -> url`.
    Targets ending in `s` receive a list (every `--image` given); others exactly one file."""
    check_media_arity(model, req)
    args: dict[str, Any] = dict(model.defaults)
    for inp in model.inputs:
        key = arg_target(model, inp)
        value: Any = None
        if inp == "prompt" and req.prompt:
            value = req.prompt
        elif inp == "text" and (req.text or req.prompt):
            value = req.text or req.prompt
        elif inp == "voice" and req.voice:
            value = req.voice
        elif inp in MEDIA_INPUTS and req.media(inp):
            urls = [uploader(p) for p in req.media(inp)]
            value = urls if key.endswith("s") else urls[0]
        elif inp == "end_image" and req.end_image:
            value = uploader(req.end_image)
        if value is None:
            continue
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
