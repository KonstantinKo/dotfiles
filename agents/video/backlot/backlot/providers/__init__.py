"""Provider registry. Adding a provider = one module exposing a class with estimate/run."""

from __future__ import annotations

from typing import Any

from backlot.errors import BacklotError
from backlot.providers.base import BaseProvider, GenRequest, GenResult, Provider, ProviderError, ProviderNotConfigured

__all__ = [
    "BaseProvider",
    "GenRequest",
    "GenResult",
    "Provider",
    "ProviderError",
    "ProviderNotConfigured",
    "get_provider",
    "PROVIDERS",
]


def _fal(cfg):
    from backlot.providers.fal import FalProvider

    return FalProvider(cfg)


def _comfy_local(cfg):
    from backlot.providers.comfyui_local import ComfyUILocalProvider

    return ComfyUILocalProvider(cfg)


def _local(cfg):
    from backlot.providers.local import LocalProvider

    return LocalProvider(cfg)


def _comfy_cloud(cfg):
    from backlot.providers.comfyui_cloud import ComfyUICloudProvider

    return ComfyUICloudProvider(cfg)


def _higgsfield(cfg):
    from backlot.providers.higgsfield import HiggsfieldProvider

    return HiggsfieldProvider(cfg)


PROVIDERS = {
    "fal": _fal,
    "comfyui-local": _comfy_local,
    "local": _local,
    "comfyui-cloud": _comfy_cloud,
    "higgsfield": _higgsfield,
}


def get_provider(name: str, config: dict[str, Any] | None = None) -> BaseProvider:
    factory = PROVIDERS.get(name)
    if factory is None:
        raise BacklotError(f"unknown provider {name!r}; known: {', '.join(sorted(PROVIDERS))}")
    return factory(config or {})
