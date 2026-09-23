"""Higgsfield: not configured. See Studio/Providers/higgsfield.md in the vault."""

from __future__ import annotations

from backlot.models import ModelSpec
from backlot.providers.base import BaseProvider, GenRequest, GenResult, ProviderNotConfigured

_MSG = "provider higgsfield is not configured; see the vault note Studio/Providers/higgsfield.md"


class HiggsfieldProvider(BaseProvider):
    name = "higgsfield"

    def estimate(self, model: ModelSpec, req: GenRequest) -> float:
        raise ProviderNotConfigured(_MSG)

    def run(self, model: ModelSpec, req: GenRequest) -> GenResult:
        raise ProviderNotConfigured(_MSG)
