"""ComfyUI Cloud: not configured. See Studio/Providers/comfyui-cloud.md in the vault."""

from __future__ import annotations

from backlot.models import ModelSpec
from backlot.providers.base import BaseProvider, GenRequest, GenResult, ProviderNotConfigured

_MSG = "provider comfyui-cloud is not configured; see the vault note Studio/Providers/comfyui-cloud.md"


class ComfyUICloudProvider(BaseProvider):
    name = "comfyui-cloud"

    def estimate(self, model: ModelSpec, req: GenRequest) -> float:
        raise ProviderNotConfigured(_MSG)

    def run(self, model: ModelSpec, req: GenRequest) -> GenResult:
        raise ProviderNotConfigured(_MSG)
